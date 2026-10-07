#!/usr/bin/env bash
# split 과 csplit 의 옵션을 한 벌의 샘플 로그 위에서 전부 돌려 본다.
# 작업은 임시 폴더에서 하고 끝나면 지운다. 출력에 임시 폴더 경로는 찍지 않는다.
set -u

WORK_DIR="$(mktemp -d)"
trap 'cd / && rm -rf "${WORK_DIR}"' EXIT
cd "${WORK_DIR}" || exit 1

chapter() {
    printf '\n===== %s\n' "$1"
}

# 줄 수와 바이트 수를 한 줄씩. wc 는 파일 이름 정렬을 셸 glob 에 맡긴다
count_pieces() {
    local f
    for f in "$@"; do
        printf '%-14s %5d줄 %7d바이트\n' "${f}" "$(wc -l < "${f}")" "$(wc -c < "${f}")"
    done
}

clean() {
    rm -f x* part_* day_* sec_* xx* chunk* rr_* big_* *.gz joined.log
}

# 2,500줄 접근 로그. 줄 길이가 들쭉날쭉하도록 path 를 번갈아 쓴다
awk 'BEGIN {
    split("/api/items /api/items/42/reviews /health /api/orders?page=3", p, " ")
    for (i = 1; i <= 2500; i++)
        printf "2026-10-01T%02d:%02d:%02d INFO req=%04d path=%s status=200\n",
               int(i / 3600), int(i / 60) % 60, i % 60, i, p[i % 4 + 1]
}' > app.log

# 날짜마다 머리줄이 붙는 로그. csplit 실습용
{
    printf '# 서버 로그 — 머리말 두 줄\n# 생성: 2026-10-04\n'
    for d in 01 02 03; do
        printf '=== 2026-10-%s ===\n' "${d}"
        printf 'INFO start day %s\n' "${d}"
        printf 'WARN slow query day %s\n' "${d}"
        printf 'INFO end day %s\n' "${d}"
    done
} > days.log

chapter '0. 입력 파일'
count_pieces app.log days.log
head -2 app.log
cat days.log

chapter '1. 기본값 — 1000줄씩, 접두어 x, 접미사 aa'
split app.log
count_pieces x*
clean

chapter '2. -l, 접두어, -d, -a, --additional-suffix, --numeric-suffixes=FROM, -x'
split -l 1000 -d -a 3 --additional-suffix=.log app.log part_
ls part_*
clean
split -l 1000 --numeric-suffixes=7 app.log part_
ls part_*
clean
split -l 200 -x app.log part_
ls part_* | tr '\n' ' '; echo
clean

chapter '3. -b 는 줄 가운데를 자르고, -C 는 줄을 지킨다'
split -b 64K app.log part_
count_pieces part_*
printf 'part_aa 마지막 줄 : '; tail -c 40 part_aa; echo '|'
printf 'part_ab 첫 줄     : '; head -1 part_ab
clean
split -C 64K app.log part_
count_pieces part_*
printf 'part_aa 마지막 줄 : '; tail -1 part_aa
printf 'part_ab 첫 줄     : '; head -1 part_ab
clean

chapter '4. 한 줄이 -C 크기보다 길면'
printf '%0300d\nshort\n' 0 > long_line.txt
split -C 100 long_line.txt part_
count_pieces part_*
clean
rm -f long_line.txt

chapter '5. -n — 개수로 나누기 (N, l/N, r/N, K/N)'
split -n 3 app.log part_
count_pieces part_*
printf 'part_ab 첫 줄 : '; head -1 part_ab
clean
split -n l/3 app.log part_
count_pieces part_*
printf 'part_ab 첫 줄 : '; head -1 part_ab
clean
split -n r/3 app.log rr_
count_pieces rr_*
head -2 rr_ab
clean
printf 'l/2/3 를 표준 출력으로 받은 줄 수 : '
split -n l/2/3 app.log | wc -l

chapter '6. 조각이 입력보다 많으면 빈 파일 — -e'
printf 'a\nb\n' > two.txt
split -n l/4 two.txt part_
count_pieces part_*
clean
split -e -n l/4 two.txt part_
ls part_*
clean
rm -f two.txt

chapter '7. 접미사가 모자라면'
split -l 100 -a 1 app.log part_
echo "종료 코드 $?"
ls part_* | tr '\n' ' '; echo
clean
seq 1 3000 > lines.txt
split -l 100 -a 1 lines.txt part_
echo "종료 코드 $?"
ls part_* | wc -l
clean

chapter '8. -a 를 안 주면 접미사 길이가 늘어난다'
seq 1 700 > lines.txt
split -l 1 lines.txt x
ls x* | sed -n '1p;675,678p;$p'
printf '%s개 / 조각을 glob 순서로 이은 첫 줄과 마지막 줄 : ' "$(ls x* | wc -l)"
cat x* | sed -n '1p;$p' | tr '\n' ' '; echo
cat x* | cmp - lines.txt && echo 'cmp: 원본과 같다'
clean
rm -f lines.txt

chapter '9. --filter — 조각마다 명령에 넘기기'
split -l 1000 --filter='gzip > $FILE.gz' app.log part_
ls part_*
zcat part_*.gz | cmp - app.log && echo 'cmp: 원본과 같다'
clean

chapter '10. -t — 줄 대신 다른 구분자'
printf 'r1;r2;r3;r4;r5;' > recs.txt
split -t ';' -l 2 recs.txt part_
for f in part_*; do printf '%s: %s\n' "${f}" "$(cat "${f}")"; done
clean
rm -f recs.txt

chapter '11. 표준 입력과 --verbose'
head -250 app.log | split -l 100 --verbose - part_
clean

chapter '12. 다시 합치고 검사하기'
split -b 50K app.log part_
cat part_* > joined.log
sha256sum app.log joined.log | cut -c1-16,65-
clean

chapter '13. csplit — 줄 번호와 정규식'
csplit days.log 3 7
count_pieces xx*
clean
csplit days.log '/^=== /' '{*}'
count_pieces xx*
printf 'xx00 :\n'; cat xx00
clean

chapter '14. -s, -f, -n, -b'
csplit -s -f day_ -n 3 days.log '/^=== /' '{*}'
ls day_*
clean
csplit -s -f day_ -b '%02d.log' days.log '/^=== /' '{*}'
ls day_*
clean

chapter '15. %REGEXP% 로 앞을 버리기, --suppress-matched'
csplit -s -f sec_ days.log '%^=== %' '/^=== /' '{*}'
count_pieces sec_*
head -1 sec_00
clean
csplit -s -f sec_ --suppress-matched days.log '/^=== /' '{*}'
count_pieces sec_*
head -1 sec_01
clean

chapter '16. OFFSET'
csplit -s -f sec_ days.log '/^WARN/+1' '{*}'
count_pieces sec_*
clean
csplit -s -f sec_ days.log '/^=== 2026-10-02/-1'
count_pieces sec_*
tail -1 sec_00
clean

chapter '17. 처음부터 맞는 줄이면 빈 조각 — -z'
tail -n +3 days.log > nohead.log
csplit -f sec_ nohead.log '/^=== /' '{*}'
clean
csplit -z -f sec_ nohead.log '/^=== /' '{*}'
clean
rm -f nohead.log

chapter '18. 못 찾으면 지운다 — -k'
csplit -f sec_ days.log '/^=== /' '{5}'
echo "종료 코드 $?"
ls sec_* 2>&1
clean
csplit -k -f sec_ days.log '/^=== /' '{5}'
echo "종료 코드 $?"
ls sec_*
clean
csplit -f sec_ days.log '/^ERROR/'
echo "종료 코드 $?"
clean

chapter '19. 경계값 — 딱 맞으면'
seq 1 2600 > lines.txt
split -l 100 -a 1 lines.txt part_
echo "26조각, -a 1 : 종료 코드 $?"
clean
seq 1 650 > lines.txt
split -l 1 lines.txt x
printf '650조각, -a 없음 : 마지막 이름 %s\n' "$(ls x* | tail -1)"
clean
rm -f lines.txt
csplit -s -f sec_ days.log '/^=== /' '{2}'
echo "'{2}' : 종료 코드 $?, 조각 $(ls sec_* | wc -l)개"
clean
