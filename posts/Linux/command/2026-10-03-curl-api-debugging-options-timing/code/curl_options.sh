#!/usr/bin/env bash
# curl 의 자주 쓰는 옵션을 갈래별로 로컬 API 서버(api_server.py)에 대고 돌린다.
# 외부 네트워크에 나가지 않는다. 127.0.0.1 의 18080(HTTP)·18443(HTTPS)만 쓴다.

cd "$(dirname "$0")" || exit 1

API=http://127.0.0.1:18080

run() {
    printf '$ %s\n' "$1"
    eval "$1"
    printf '[종료 코드 %d]\n\n' $?
}

section() { printf '\n==== %s ====\n\n' "$1"; }

# 출력에서 날짜처럼 실행마다 바뀌는 줄을 걸러 구조만 남긴다
no_date() { grep -v -i '^< date:\|^date:'; }

curl --version | head -n 1
printf '옵션 수 (curl --help all 에서 - 로 시작하는 줄): '
curl --help all | grep -c '^ *-'
echo

python api_server.py &
SERVER_PID=$!
# 서버가 뜰 때까지 기다리는 것도 curl 옵션으로 한다
curl -s -o /dev/null --retry 10 --retry-connrefused --retry-delay 1 "$API/health"

section "1. 응답 보기"
run "curl -w '\n' $API/users/42 2>&1"
run "curl -s -w '\n' $API/users/42"
run "curl -s -i $API/users/42 | no_date"
run "curl -s -I $API/users/42 | no_date"
run "curl -s -D headers.txt -o body.json $API/users/42; cat headers.txt | no_date; cat body.json; echo"
run "curl --no-progress-meter -v $API/users/42 2>&1 | no_date"
run "curl -v -w '\n' $API/users/42 2>/dev/null"
run "curl http://127.0.0.1:1/users/42 2>&1"
run "curl -s http://127.0.0.1:1/users/42 2>&1"
run "curl -sS http://127.0.0.1:1/users/42 2>&1"

section "2. 요청 만들기"
run "curl -s -X DELETE $API/users/42/echo"
run "curl -s -H 'X-Trace-Id: t-777' -A 'my-batch/2.1' $API/echo"
run "curl -s -d 'name=kim&age=30' $API/echo"
run "curl -s -d @body.json $API/echo"
run "curl -s --data-raw @body.json $API/echo"
run "curl -s --data-urlencode 'q=a&b c' $API/echo"
run "curl -s --json '{\"name\":\"kim\"}' $API/echo"
run "curl -s -G -d 'page=2' -d 'size=10' $API/echo"
run "curl -s --url-query 'page=2' --url-query 'q=a b' $API/echo"
run "curl -s -u alice:secret $API/echo"
run "curl -s -v -u alice:secret -o /dev/null $API/echo 2>&1 | grep -i '^> authorization'"
run "curl -s -F 'title=report' -F 'file=@body.json' $API/echo-raw"
run "curl -s -c cookies.txt $API/session; echo; grep session cookies.txt"
run "curl -s -b cookies.txt $API/echo"

section "3. 리다이렉트와 실패 판정"
run "curl -s -w '%{http_code}\n' $API/old-users/42"
run "curl -s -L -w '\n%{http_code} redirects=%{num_redirects} url=%{url_effective}\n' $API/old-users/42"
run "curl -s -L -d 'id=kim' $API/login"
run "curl -s -L --post302 -d 'id=kim' $API/login"
run "curl -sS -L --max-redirs 3 $API/loop 2>&1"
run "curl -s -w '\n' $API/error"
run "curl -s -f $API/error 2>&1"
run "curl -sS -f $API/error 2>&1"
run "curl -sS --fail-with-body -w '\n' $API/error 2>&1"

section "4. 시간과 재시도"
run "curl -s -o /dev/null -w @timing-format.txt $API/slow-first-byte"
run "curl -s -o /dev/null -w @timing-format.txt $API/slow-body"
run "curl -s -o /dev/null -w '%{json}' $API/users/42 | tr ',' '\n' | grep -E 'http_code|size_download|num_connects|remote_ip|scheme|time_total'"
run "curl -s -w '\nx-request-id=%header{x-request-id}\n' $API/users/42"
run "curl -sS -m 0.5 $API/slow-body 2>&1"
run "curl -sS --connect-timeout 2 -m 5 $API/slow-first-byte 2>&1"
run "curl --no-progress-meter --retry 3 --retry-delay 1 -w ' http=%{http_code}\n' $API/flaky 2>&1"

section "5. 연결 바꾸기"
run "curl -s --resolve api.example.test:18080:127.0.0.1 http://api.example.test:18080/echo"
run "curl -s -x $API http://api.example.test/echo"

mkdir -p probe_pki
# Git Bash 가 -subj "/CN=..." 를 윈도 경로로 바꾸지 않게 이 명령에만 끈다
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=localhost" \
    -keyout probe_pki/key.pem -out probe_pki/cert.pem 2>/dev/null
openssl s_server -accept 127.0.0.1:18443 -cert probe_pki/cert.pem -key probe_pki/key.pem \
    -www -quiet >/dev/null 2>&1 &
TLS_PID=$!
curl -s -o /dev/null --retry 10 --retry-connrefused --retry-delay 1 -k https://127.0.0.1:18443/ 2>/dev/null
# Schannel 메시지 뒷부분은 윈도 로캘(CP949)로 찍혀 깨지므로 첫 줄의 앞부분만 남긴다
run "curl -sS -o /dev/null https://127.0.0.1:18443/ 2>&1 | head -n 1 | sed 's/ - .*//'"
run "curl -s -k -o /dev/null -w @timing-format.txt https://127.0.0.1:18443/"

kill "$TLS_PID" 2>/dev/null
curl -s "$API/shutdown" >/dev/null
wait "$SERVER_PID"
rm -f headers.txt cookies.txt body.json
