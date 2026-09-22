#!/usr/bin/env bash
# awk로 로그를 표로 집계한다. 샘플 로그를 직접 만들고 끝나면 지운다.
set -u

log_file="access.log"
csv_file="latency.csv"

make_files() {
    cat > "${log_file}" <<'EOF'
10.0.0.4 - - [22/Sep/2026:09:00:01] "GET /api/orders HTTP/1.1" 200 41
10.0.0.7 - - [22/Sep/2026:09:00:02] "GET /api/stock HTTP/1.1" 200 18
10.0.0.4 - - [22/Sep/2026:09:00:05] "POST /api/orders HTTP/1.1" 500 5002
10.0.0.9 - - [22/Sep/2026:09:00:06] "GET /api/orders HTTP/1.1" 200 39
10.0.0.4 - - [22/Sep/2026:09:00:08] "GET /healthz HTTP/1.1" 200 2
10.0.0.7 - - [22/Sep/2026:09:00:09] "POST /api/orders HTTP/1.1" 201 88
10.0.0.9 - - [22/Sep/2026:09:00:12] "GET /api/stock HTTP/1.1" 503 3001
10.0.0.4 - - [22/Sep/2026:09:00:13] "POST /api/orders HTTP/1.1" 201 91
10.0.0.2 - - [22/Sep/2026:09:00:15] "GET /api/orders HTTP/1.1" 404 7
10.0.0.7 - - [22/Sep/2026:09:00:16] "GET /healthz HTTP/1.1" 200 2
EOF

    # 세 번째 줄의 따옴표 안에 쉼표가 들어 있다. -F, 와 --csv 의 차이를 보는 자리다.
    cat > "${csv_file}" <<'EOF'
service,region,latency_ms
orders,seoul,41
"orders,legacy",busan,39
stock,seoul,18
orders,seoul,5002

stock,busan,3001
healthz,seoul,2
EOF
}

chapter() {
    printf '\n===== %s\n' "$1"
}

run() {
    printf '$ %s\n' "$1"
    eval "$1"
}

make_files

chapter "0. 버전"
run "awk --version | head -1"

chapter "1. 필드 번호를 먼저 확인한다"
run "awk 'NR==1 {for (i = 1; i <= NF; i++) printf \"%d:%s\\n\", i, \$i}' ${log_file}"

chapter "2. 기본 구분자는 연속 공백 — 상태코드는 \$8, 응답시간은 \$9"
run "awk '{print \$1, \$6, \$8, \$9}' ${log_file} | head -4"
run "awk 'END {print NR, NF}' ${log_file}"

chapter "3. -F 로 구분자를 바꾼다"
run "awk -F, 'NR>1 && NF {print \$1, \$3}' ${csv_file}"

chapter "4. --csv 는 따옴표 안의 구분자를 존중한다 (gawk 5.3+)"
run "awk -F, 'NR==3 {print NF; print \$1}' ${csv_file}"
run "awk --csv 'NR==3 {print NF; print \$1}' ${csv_file}"

chapter "5. 패턴만 / 액션만 / 둘 다"
run "awk '\$8 >= 500' ${log_file}"
run "awk '\$8 >= 500 {print \$6, \$8, \$9}' ${log_file}"
run "awk '/POST/ {print \$6, \$8}' ${log_file}"

chapter "6. 연관배열 — 상태코드별 건수"
run "awk '{count[\$8]++} END {for (code in count) print code, count[code]}' ${log_file}"

chapter "7. for-in 순회 순서는 정의되어 있지 않다 — 정렬은 밖에서"
run "awk '{count[\$8]++} END {for (code in count) print code, count[code]}' ${log_file} | sort -n"

chapter "8. 경로별 건수·합계·평균"
run "awk '{n[\$6]++; sum[\$6]+=\$9} END {for (p in n) printf \"%-14s %3d %7d %9.1f\\n\", p, n[p], sum[p], sum[p]/n[p]}' ${log_file} | sort"

chapter "9. OFS·ORS 로 출력 모양을 정한다"
run "awk -v OFS=, '{print \$1, \$8}' ${log_file} | head -3"
run "awk -v ORS='|' '{print \$8}' ${log_file}; echo"

chapter "10. \$0 를 바꾸면 재분해되고, \$1 을 바꾸면 \$0 가 다시 조립된다"
run "awk 'NR==1 {\$1 = \"HOST\"; print}' ${log_file}"
run "awk -v OFS=, 'NR==1 {\$1 = \$1; print}' ${log_file}"

chapter "11. -v 로 셸 값을 넘긴다"
threshold=500
run "awk -v limit=${threshold} '\$8 >= limit {c++} END {print \"임계 이상:\", c+0}' ${log_file}"

chapter "12. 정의되지 않은 변수는 0이자 빈 문자열이다"
run "awk 'END {print \"[\" undef \"]\", undef+0, length(undef)}' ${log_file}"
run "awk '/NEVER_MATCH/ {c++} END {print \"[\" c \"]\", c+0}' ${log_file}"

chapter "13. NR·FNR·FILENAME — 파일이 여러 개일 때"
run "awk '{print FILENAME, FNR, NR}' ${log_file} ${csv_file} | sed -n '9,13p'"

chapter "14. 빈 줄도 레코드다"
run "awk 'END {print NR}' ${csv_file}"
run "awk 'NF {c++} END {print c}' ${csv_file}"

chapter "15. 숫자 비교와 문자열 비교가 갈린다"
run "awk -F, 'NR>1 && NF && \$3 > 100 {print \$3}' ${csv_file}"
run "awk -F, 'NR>1 && NF && \$3 \"\" > \"100\" {print \$3}' ${csv_file}"

chapter "16. -f 로 프로그램을 파일에서 읽는다"
cat > status_report.awk <<'EOF'
# 상태코드를 2xx/4xx/5xx 갈래로 묶어 세고 갈래별 최대 응답시간을 남긴다.
{
    class = int($8 / 100) "xx"
    n[class]++
    if ($9 > max[class]) max[class] = $9
}
END {
    printf "%-6s %5s %10s\n", "CLASS", "CNT", "MAX_MS"
    # for-in 순서가 정의되어 있지 않으므로 볼 갈래를 직접 훑는다.
    for (i = 1; i <= 5; i++) {
        class = i "xx"
        if (class in n) printf "%-6s %5d %10d\n", class, n[class], max[class]
    }
}
EOF
run "awk -f status_report.awk ${log_file}"

chapter "17. --posix 는 gawk 확장을 막는다"
run "awk 'BEGIN {print gensub(/api/, \"v2\", \"g\", \"/api/orders\")}'"
run "awk --posix 'BEGIN {print gensub(/api/, \"v2\", \"g\", \"/api/orders\")}'"

chapter "18. 종료 코드는 exit 로 정한다"
run "awk '\$8 >= 500 {found=1} END {exit !found}' ${log_file}; echo \"종료 코드 \$?\""
run "awk '\$8 >= 900 {found=1} END {exit !found}' ${log_file}; echo \"종료 코드 \$?\""

rm -f "${log_file}" "${csv_file}" status_report.awk
