#!/usr/bin/env bash
# cut, paste, tr 의 옵션을 한 벌의 샘플 파일 위에서 전부 돌려 본다. 파일은 끝나면 지운다.
set -u

make_files() {
    # ps 출력처럼 칸을 공백 여러 개로 맞춘 표. 첫 칸 앞에도 공백이 있다
    cat > ps.txt <<'EOF'
  PID USER     %CPU COMMAND
    1 root      0.0 init
  812 mysql    12.5 mysqld
 1034 www-data  3.1 nginx
EOF

    cat > users.csv <<'EOF'
# 사용자 목록 — 이 줄에는 쉼표가 없다
id,name,dept,email
1,kim,dev,kim@example.com
2,lee,ops,lee@example.com
3,park,dev,park@example.com
EOF

    # 따옴표 안에 쉼표가 든 CSV
    printf '%s\n' 'id,city,memo' '1,"Seoul, KR",ok' > quoted.csv

    printf 'id\tlevel\tmsg\n1\tWARN\tdisk 80%%\n2\tERROR\tdisk full\n' > app.tsv

    printf '%s\n' kim lee park > names.txt
    printf '%s\n' dev ops > depts.txt
    printf '%s\n' 700 450 500 > pays.txt
    printf '%s\n' a b c d e f > letters.txt

    printf '한글로그\n' > hangul.txt
    # 윈도우에서 만든 파일처럼 줄 끝이 CRLF 다
    printf 'alpha\r\nbeta\r\n' > crlf.txt
    printf 'x,1\0y,2\0' > nul.txt
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
run "cut --version | head -1"
run "paste --version | head -1"
run "tr --version | head -1"
run "bash --version | head -1"
run "echo \"LANG=\${LANG:-} LC_ALL=\${LC_ALL:-}\""

chapter "1. cut -f 는 구분자 한 글자마다 칸을 나눈다"
run "cat ps.txt"
run "cut -d' ' -f2 ps.txt"
run "cut -d' ' -f5 ps.txt"
run "cut -d', ' -f1 ps.txt"

chapter "2. 공백 여러 칸 — tr -s 로 줄인 뒤 자른다"
run "tr -s ' ' < ps.txt"
run "tr -s ' ' < ps.txt | cut -d' ' -f2"
run "tr -s ' ' < ps.txt | cut -d' ' -f3"
run "sed 's/^ *//' ps.txt | tr -s ' ' | cut -d' ' -f2"
run "awk '{print \$2}' ps.txt"

chapter "3. 필드 목록 — 범위, 순서, 여집합"
run "cut -d, -f1,3 users.csv"
run "cut -d, -f3,1 users.csv"
run "cut -d, -f2- users.csv"
run "cut -d, -f-2 users.csv"
run "cut -d, -f2 --complement users.csv"
run "cut -d, -f1,2 --output-delimiter=' | ' users.csv"

chapter "4. 구분자가 없는 줄 — 기본은 그대로, -s 는 버린다"
run "cut -d, -f2 users.csv | head -2"
run "cut -d, -f2 -s users.csv | head -2"

chapter "5. 기본 구분자는 탭"
run "cut -f2 app.tsv"
run "cut -f2,3 --output-delimiter=, app.tsv"

chapter "6. 따옴표 안의 쉼표도 구분자다"
run "cut -d, -f2 quoted.csv"

chapter "7. -b 와 -c — 이 판에서는 둘 다 바이트다"
run "LC_ALL=en_US.UTF-8 cut -c1-3 hangul.txt | od -An -tx1"
run "LC_ALL=en_US.UTF-8 cut -b1-3 hangul.txt | od -An -tx1"
run "LC_ALL=en_US.UTF-8 cut -c1-2 hangul.txt | od -An -tx1"
run "cut -b1-3 --complement hangul.txt | od -An -tx1"
run "cut -c1-3 users.csv | tail -3"

chapter "8. -z — NUL 로 끝나는 레코드"
run "cut -z -d, -f2 nul.txt | od -An -c"

chapter "9. paste — 줄을 옆으로 붙인다"
run "paste names.txt pays.txt"
run "paste -d, names.txt depts.txt pays.txt"
run "paste -d',;' names.txt depts.txt pays.txt"
run "paste -s names.txt"
run "paste -sd, names.txt"
run "paste -sd+ pays.txt"
run "paste - - < letters.txt"
run "paste -d, - - - < letters.txt"
run "cut -d, -f2 -s users.csv | paste -sd' '"
run "printf 'a\0b\0' | paste -z -sd, | od -An -c"

chapter "10. tr — 글자를 바꾼다"
run "echo 'Hello World' | tr a-z A-Z"
run "echo 'Hello World' | tr '[:lower:]' '[:upper:]'"
run "echo 'abcabc' | tr abc x"
run "echo 'abcabc' | tr -t abc x"
run "echo 'phone 010-1234-5678' | tr 0-9 '[#*]'"
run "echo 'a,b;c' | tr ',;' '\\t\\t' | od -An -c"

chapter "11. tr -d, -s, -c"
run "od -An -c crlf.txt"
run "tr -d '\\r' < crlf.txt | od -An -c"
run "echo 'order 42 total 1,300' | tr -cd '0-9\\n'"
run "echo 'aaa   bbb  ccc' | tr -s ' '"
run "echo 'aaa   bbb  ccc' | tr -s ' ' '\\n'"
run "echo 'one  two
three' | tr -s '[:space:]' '\\n'"
run "echo 'hello' | tr -s 'l'"
run "echo 'a--b' | tr -d -- '-'"

chapter "12. tr 은 파일 인자를 받지 않는다"
run "tr a-z A-Z names.txt"

chapter "13. tr 과 한글 — 바이트 단위로 바꾼다"
run "printf '가 나 글\n' | od -An -tx1"
# 가→나 한 글자를 바꾸라고 했지만 tr 은 ea→eb, b0→82, 80→98 세 바이트 대응으로 읽는다
run "echo '가나다' | LC_ALL=en_US.UTF-8 tr '가' '나'"
run "echo '가글' | LC_ALL=en_US.UTF-8 tr '가' '나'"
run "echo '가글' | LC_ALL=en_US.UTF-8 tr '가' '나' | od -An -tx1"
run "echo '가글' | sed 's/가/나/g'"

rm -f ps.txt users.csv quoted.csv app.tsv names.txt depts.txt pays.txt letters.txt \
    hangul.txt crlf.txt nul.txt
