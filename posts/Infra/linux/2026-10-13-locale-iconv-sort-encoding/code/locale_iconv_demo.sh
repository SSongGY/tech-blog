#!/usr/bin/env bash
# locale 설정에 따라 정렬·글자 수·숫자 표기가 달라지는 것과,
# iconv 로 인코딩을 바꿀 때 실패하는 자리와 그 처리 옵션을 확인한다.
# 작업 파일은 이 스크립트 옆의 probe_work/ 에 만든다 (gitignore 대상).
exec 2>&1
cd "$(dirname "$0")" || exit 1
work_dir="probe_work"
mkdir -p "${work_dir}"

section() { printf '\n== %s\n' "$1"; }

section "0. 버전"
locale --version | head -n 1
iconv --version | head -n 1
sort --version | head -n 1
printf 'locale -a 개수: '; locale -a | wc -l
printf 'iconv -l 개수 : '; iconv -l | wc -l
locale -a | grep -E '^(ko_KR|en_US|de_DE)(\.utf8)?$'

section "1. 변수 우선순위 — LC_ALL > LC_* > LANG"
echo "-- LANG=ko_KR.UTF-8 만"
env -u LC_ALL LANG=ko_KR.UTF-8 locale | grep -E '^(LANG|LC_CTYPE|LC_COLLATE|LC_ALL)='
echo "-- LANG=ko_KR.UTF-8 + LC_COLLATE=C"
env -u LC_ALL LANG=ko_KR.UTF-8 LC_COLLATE=C locale | grep -E '^(LANG|LC_CTYPE|LC_COLLATE|LC_ALL)='
echo "-- 위에 LC_ALL=en_US.UTF-8 을 더하면"
env LANG=ko_KR.UTF-8 LC_COLLATE=C LC_ALL=en_US.UTF-8 locale | grep -E '^(LANG|LC_CTYPE|LC_COLLATE|LC_ALL)='

section "2. 없는 로케일을 주면"
LC_ALL=xx_YY.UTF-8 locale charmap
echo "종료 코드 $?"
LC_ALL=xx_YY.UTF-8 sort --version | head -n 1

section "3. locale -k / -c — 범주의 값 보기"
LC_ALL=en_US.UTF-8 locale -k charmap
LC_ALL=C locale -k charmap
LC_ALL=ko_KR.UTF-8 locale -c -k LC_NUMERIC
LC_ALL=de_DE.UTF-8 locale -k decimal_point thousands_sep
LC_ALL=ko_KR.UTF-8 locale -k abday | head -n 1

section "4. locale -m — 문자 집합 목록 (앞부분)"
locale -m | head -n 8
printf '개수: '; locale -m | wc -l

section "4-1. locale -a -v — 로케일마다 자세히 (앞 한 건)"
locale -a -v | head -n 6

section "4-2. Cygwin 전용 — 윈도우 설정에서 읽는 기본 로케일"
# 이 판의 locale 은 이 옵션들의 출력 끝에 줄바꿈을 찍지 않는다
printf -- '-i  입력 로케일          : '; locale -i; echo
printf -- '-u  사용자 UI 언어       : '; locale -u; echo
printf -- '-s  시스템 UI 언어       : '; locale -s; echo
printf -- '-f  사용자 지역 형식     : '; locale -f; echo
printf -- '-n  비유니코드 기본값    : '; locale -n; echo
printf -- '-nU 위에 .UTF-8 을 붙여  : '; locale -n -U; echo

section "4-3. iconv -l — 지원 인코딩 목록 (앞부분)"
iconv -l | head -n 3

section "5. 같은 단어 목록을 로케일만 바꿔 sort"
printf '%s\n' banana Apple apple _tmp 가나 Éclair 10 9 Zebra 나비 eclair > "${work_dir}/words.txt"
for loc in C en_US.UTF-8 ko_KR.UTF-8; do
  echo "-- LC_ALL=${loc}"
  LC_ALL="${loc}" sort "${work_dir}/words.txt" | paste -sd ' ' -
done

section "6. sort -n 과 소수점 — 로케일이 숫자 읽기를 바꾼다"
printf '%s\n' 1,5 1.2 10 2,25 > "${work_dir}/numbers.txt"
for loc in C en_US.UTF-8 de_DE.UTF-8; do
  echo "-- LC_ALL=${loc} sort -n"
  LC_ALL="${loc}" sort -n "${work_dir}/numbers.txt" | paste -sd ' ' -
done

section "7. 천 단위 구분 — printf %'d"
for loc in C en_US.UTF-8 de_DE.UTF-8 ko_KR.UTF-8; do
  printf '%-12s ' "${loc}"; LC_ALL="${loc}" printf "%'d\n" 1234567
done

section "8. 글자 수 — wc -c / wc -m 과 LC_CTYPE"
printf '한글abc\n' > "${work_dir}/mixed.txt"
for loc in C.UTF-8 POSIX en_US.UTF-8; do
  printf '%-12s wc -c=%s  wc -m=%s\n' "${loc}" \
    "$(LC_ALL="${loc}" wc -c < "${work_dir}/mixed.txt")" \
    "$(LC_ALL="${loc}" wc -m < "${work_dir}/mixed.txt")"
done
echo "-- cut -c1-2 (UTF-8 로케일)"
LC_ALL=en_US.UTF-8 cut -c1-2 "${work_dir}/mixed.txt" | od -An -tx1

section "9. iconv -f / -t — UTF-8 을 CP949 로"
printf '가똠\n' > "${work_dir}/utf8.txt"
od -An -tx1 "${work_dir}/utf8.txt"
iconv -f UTF-8 -t CP949 "${work_dir}/utf8.txt" > "${work_dir}/cp949.txt"
echo "종료 코드 $?"
od -An -tx1 "${work_dir}/cp949.txt"

section "10. 같은 글자를 EUC-KR 로"
iconv -f UTF-8 -t EUC-KR "${work_dir}/utf8.txt" | od -An -tx1
echo "종료 코드 ${PIPESTATUS[0]}"

section "11. 인코딩을 잘못 짚으면 — CP949 파일을 UTF-8 로 읽기"
iconv -f UTF-8 -t UTF-16LE "${work_dir}/cp949.txt" > /dev/null
echo "종료 코드 $?"
echo "-- -c 를 붙여도"
iconv -c -f UTF-8 -t UTF-16LE "${work_dir}/cp949.txt" | od -An -tx1
echo "종료 코드 ${PIPESTATUS[0]}"
echo "-- //IGNORE 를 붙여도"
iconv -f UTF-8 -t UTF-16LE//IGNORE "${work_dir}/cp949.txt" | od -An -tx1
echo "종료 코드 ${PIPESTATUS[0]}"
echo "-- 올바르게 짚으면"
iconv -f CP949 -t UTF-8 "${work_dir}/cp949.txt"
echo "종료 코드 $?"

section "12. 변환할 수 없는 글자 — -c, -s, //IGNORE, //TRANSLIT"
printf 'Café €5 똠\n' > "${work_dir}/latin.txt"
echo "-- 옵션 없이 ASCII 로"
iconv -f UTF-8 -t ASCII "${work_dir}/latin.txt"; echo " [종료 코드 $?]"
echo "-- -c"
iconv -c -f UTF-8 -t ASCII "${work_dir}/latin.txt"; echo "[종료 코드 $?]"
echo "-- -c -s"
iconv -c -s -f UTF-8 -t ASCII "${work_dir}/latin.txt"; echo "[종료 코드 $?]"
echo "-- -t ASCII//IGNORE"
iconv -f UTF-8 -t ASCII//IGNORE "${work_dir}/latin.txt"; echo "[종료 코드 $?]"
echo "-- -t ASCII//TRANSLIT"
iconv -f UTF-8 -t ASCII//TRANSLIT "${work_dir}/latin.txt"; echo "[종료 코드 $?]"

section "13. 대체 문자열 — --unicode-subst / --byte-subst"
iconv -f UTF-8 -t ASCII --unicode-subst='<U+%04X>' "${work_dir}/latin.txt"
echo "종료 코드 $?"
iconv -f UTF-8 -t UTF-8 --byte-subst='<0x%02x>' "${work_dir}/cp949.txt"
echo "종료 코드 $?"

section "14. UTF-16 과 BOM"
printf 'A' | iconv -f UTF-8 -t UTF-16 | od -An -tx1
printf 'A' | iconv -f UTF-8 -t UTF-16LE | od -An -tx1
printf 'A' | iconv -f UTF-8 -t UTF-16BE | od -An -tx1

section "15. 글자가 UTF-8 로 올바른지 검사 — 변환 없이 종료 코드만"
for f in utf8.txt cp949.txt; do
  if iconv -f UTF-8 -t UTF-8 "${work_dir}/${f}" > /dev/null 2>&1; then
    echo "${f}: UTF-8 로 읽힌다"
  else
    echo "${f}: UTF-8 이 아니다"
  fi
done

section "16. 옮겨 적기 — 파일을 바꿔 저장"
iconv -f CP949 -t UTF-8 "${work_dir}/cp949.txt" > "${work_dir}/converted.txt"
cmp "${work_dir}/utf8.txt" "${work_dir}/converted.txt" && echo "원본 UTF-8 과 같다"
