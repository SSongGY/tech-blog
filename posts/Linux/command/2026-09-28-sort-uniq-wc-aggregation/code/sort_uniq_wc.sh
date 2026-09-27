#!/usr/bin/env bash
# sort, uniq, wc 의 옵션을 한 벌의 샘플 파일 위에서 전부 돌려 본다. 파일은 끝나면 지운다.
set -u

make_files() {
    # 접속 IP 10줄. 같은 IP 가 떨어져 나타나도록 일부러 섞어 둔다
    printf '%s\n' 10.0.0.4 10.0.0.7 10.0.0.4 10.0.0.9 10.0.0.4 \
        10.0.0.7 10.0.0.9 10.0.0.4 10.0.0.2 10.0.0.7 > ip.txt

    printf '%s\n' banana Apple cherry apple _tmp Banana > words.txt
    printf '%s\n' 10 9 100 2 -3 1.5 > numbers.txt
    printf '%s\n' 1e3 5 0x10 20 > general.txt
    printf '%s\n' 2M 512 1K 1G 3K > sizes.txt
    printf '%s\n' app-1.10.0 app-1.2.0 app-1.9.3 app-1.2.10 > versions.txt
    printf '%s\n' MAR jan Dec feb xyz > months.txt
    printf '%s\n' '  zeta' 'alpha' ' beta' > blanks.txt
    printf '%s\n' 'b-2' 'a.3' 'a_1' 'b 1' > dict.txt
    printf 'b\x01x\nab\na\x02z\n' > nonprint.txt

    cat > staff.csv <<'EOF'
kim,dev,700
lee,ops,450
park,dev,500
choi,ops,800
jung,dev,500
han,hr,1200
EOF

    cat > status.log <<'EOF'
09:00:01 200 /api/orders
09:00:02 200 /api/stock
09:00:05 500 /api/orders
09:00:06 200 /api/orders
09:00:08 404 /healthz
09:00:09 500 /api/orders
09:00:12 503 /api/stock
EOF

    printf '%s\n' a c e > sorted_a.txt
    printf '%s\n' b d f > sorted_b.txt

    printf '%s\n' ERROR error Error warn WARN > levels.txt
    printf '%s\n' 'x1 GET /a' 'x2 GET /a' 'x3 POST /b' 'y4 POST /b' > fields.txt

    printf '한글 로그\nabc\n' > hangul.txt
    printf 'one\ntwo\nthree' > no_newline.txt
    printf 'first line\n\nsecond  line   here\n' > spaces.txt
    : > empty.txt

    # --random-source 에 줄 고정 바이트. 같은 바이트를 주면 -R 의 결과도 같아진다
    printf '%0256d' 0 > seed.bin
    printf 'ip.txt\0words.txt\0' > names0.txt
}

chapter() {
    printf '\n===== %s\n' "$1"
}

run() {
    printf '$ %s\n' "$1"
    eval "$1"
    local status=$?
    if [ "${status}" -ne 0 ]; then
        printf '[종료 코드 %d]\n' "${status}"
    fi
}

make_files

chapter "0. 버전과 로케일"
run "sort --version | head -1"
run "uniq --version | head -1"
run "wc --version | head -1"
run "bash --version | head -1"
run "echo \"LANG=\${LANG:-} LC_ALL=\${LC_ALL:-}\""

chapter "1. 기본 정렬은 로케일을 따른다"
run "LC_ALL=C sort words.txt"
run "LC_ALL=en_US.UTF-8 sort words.txt"

chapter "2. 숫자 정렬 -n, -g, -h"
run "sort numbers.txt | paste -sd' '"
run "sort -n numbers.txt | paste -sd' '"
run "sort -n general.txt | paste -sd' '"
run "sort -g general.txt | paste -sd' '"
run "sort -n sizes.txt | paste -sd' '"
run "sort -h sizes.txt | paste -sd' '"

chapter "3. 버전 -V, 월 -M, 역순 -r"
run "sort versions.txt | paste -sd' '"
run "sort -V versions.txt | paste -sd' '"
run "sort -M months.txt | paste -sd' '"
run "sort -rn numbers.txt | paste -sd' '"
run "sort --sort=version -r versions.txt | paste -sd' '"

chapter "4. 비교 전 문자 다루기 -f, -b, -d, -i"
run "LC_ALL=C sort words.txt | paste -sd' '"
run "LC_ALL=C sort -f words.txt | paste -sd' '"
run "LC_ALL=C sort blanks.txt | cat -A"
run "LC_ALL=C sort -b blanks.txt | cat -A"
run "LC_ALL=C sort dict.txt | paste -sd'|'"
run "LC_ALL=C sort -d dict.txt | paste -sd'|'"
run "LC_ALL=C sort nonprint.txt | cat -A"
run "LC_ALL=C sort -i nonprint.txt | cat -A"

chapter "5. 키 -k 와 구분자 -t"
run "sort -t, -k3 staff.csv | paste -sd' '"
run "sort -t, -k3n staff.csv | paste -sd' '"
run "sort -t, -k2,2 -k3,3nr staff.csv"
run "sort -t, -k2 staff.csv | paste -sd' '"
run "sort -t, -k2,2 staff.csv | paste -sd' '"
run "sort -t, -k2 --debug staff.csv 2>&1 | head -6"
run "sort -t, -k2,2 --debug staff.csv 2>&1 | head -6"
run "sort -s -k2.1,2.1 status.log"
run "sort -s -k2.1,2.1 --debug status.log 2>&1 | head -4"
run "sort -s -b -k2.1,2.1 status.log"

chapter "6. 안정 정렬 -s"
run "sort -t, -k3,3n staff.csv | paste -sd' '"
run "sort -s -t, -k3,3n staff.csv | paste -sd' '"
run "sort -s -t, -k3,3n -r staff.csv | paste -sd' '"
run "sort -s -t, -k3,3nr staff.csv | paste -sd' '"

chapter "7. 중복 제거 -u"
run "sort -u ip.txt | paste -sd' '"
run "sort -t, -k2,2 -u staff.csv | paste -sd' '"
run "sort -f -u levels.txt | paste -sd' '"

chapter "8. 검사 -c, -C"
run "sort -c numbers.txt"
run "sort -C numbers.txt"
run "sort -n numbers.txt | sort -nc"
run "sort -u ip.txt | sort -cu"
run "sort ip.txt | sort -cu"

chapter "9. 병합 -m, 출력 -o, 여러 파일"
run "sort -m sorted_a.txt sorted_b.txt | paste -sd' '"
run "sort sorted_b.txt sorted_a.txt | paste -sd' '"
run "cp numbers.txt redirect.txt && sort -n redirect.txt > redirect.txt; wc -l redirect.txt"
run "cp numbers.txt inplace.txt && sort -n -o inplace.txt inplace.txt; paste -sd' ' inplace.txt"
run "sort --files0-from=names0.txt | head -3"

chapter "10. 구분자 -z, 무작위 -R"
run "printf 'b\\0a\\0c\\0' | sort -z | tr '\\0' ' '; echo"
run "sort -R --random-source=seed.bin ip.txt | paste -sd' '"
run "sort -R --random-source=seed.bin ip.txt | paste -sd' '"

chapter "11. 자원 -S, -T, --parallel, --batch-size, --compress-program"
run "sort ip.txt | md5sum"
run "sort -S 1K -T . --parallel=1 --batch-size=2 ip.txt | md5sum"
run "sort -S 1K --compress-program=gzip ip.txt | md5sum"

chapter "12. uniq 는 바로 앞 줄과만 비교한다"
run "uniq ip.txt | paste -sd' '"
run "uniq -c ip.txt"
run "sort ip.txt | uniq -c"
run "sort ip.txt | uniq -c | sort -rn"
run "sort ip.txt | uniq -c | sort -k1,1nr -k2,2V"

chapter "13. uniq 가 무엇을 남기는가 -d, -D, -u, --all-repeated, --group"
run "sort ip.txt | uniq -d | paste -sd' '"
run "sort ip.txt | uniq -D | paste -sd' '"
run "sort ip.txt | uniq -u | paste -sd' '"
run "sort ip.txt | uniq --all-repeated=separate"
run "sort ip.txt | uniq --group=append | head -6"

chapter "14. uniq 가 무엇을 비교하는가 -i, -f, -s, -w, -z"
run "uniq -i levels.txt | paste -sd' '"
run "uniq -c -f1 fields.txt"
run "uniq -c -s2 fields.txt"
run "uniq -c -w1 fields.txt"
run "printf 'a\\0a\\0b\\0' | uniq -z | tr '\\0' ' '; echo"
run "sort -u ip.txt > u1.txt; sort ip.txt | uniq > u2.txt; cmp u1.txt u2.txt && echo same"

chapter "15. wc 가 세는 것 -l, -w, -c, -m, -L"
run "wc spaces.txt"
run "wc -l no_newline.txt"
run "wc -w spaces.txt"
run "LC_ALL=C wc -c -m hangul.txt"
run "LC_ALL=en_US.UTF-8 wc -c -m hangul.txt"
run "LC_ALL=en_US.UTF-8 wc -L hangul.txt"
run "wc -m -c -l hangul.txt"

chapter "16. wc 의 출력 모양 — 여러 파일, 표준 입력, --files0-from"
run "wc -l ip.txt words.txt empty.txt"
run "wc -l < ip.txt"
run "cat ip.txt | wc -l"
run "wc -l --files0-from=names0.txt"

rm -f ip.txt words.txt numbers.txt general.txt sizes.txt versions.txt months.txt \
    blanks.txt dict.txt nonprint.txt staff.csv status.log sorted_a.txt sorted_b.txt \
    levels.txt fields.txt hangul.txt no_newline.txt spaces.txt empty.txt seed.bin \
    names0.txt redirect.txt inplace.txt u1.txt u2.txt
