#!/usr/bin/env bash
# openssl s_client 로 인증서 체인·호스트명·만료를 점검한다.
# 외부 서버 대신 이 스크립트가 만든 사설 CA(루트 → 중간 → 서버)와 127.0.0.1 의 s_server 를 쓴다.
# 그래야 "중간 인증서를 빠뜨린 서버", "만료된 서버" 같은 고장 난 상태를 마음대로 만들 수 있다.
set -u
cd "$(dirname "$0")"
# Git Bash 는 /CN=... 을 윈도 경로로 바꿔 버린다. 리눅스에서는 아무 영향이 없다
export MSYS_NO_PATHCONV=1

# 키·인증서는 공개 저장소에 올리지 않는다 — probe* 는 gitignore 대상이다
WORK_DIR=probe_pki
rm -rf "${WORK_DIR}"
mkdir "${WORK_DIR}"
cd "${WORK_DIR}"

openssl version

new_key() {
  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$1" 2>/dev/null
}

# $1=이름 $2=subject $3=서명 CA 이름 $4=확장 파일 $5...=날짜 옵션
issue_cert() {
  local name="$1" subj="$2" ca="$3" ext="$4"
  shift 4
  new_key "${name}.key"
  openssl req -new -key "${name}.key" -subj "${subj}" -out "${name}.csr"
  openssl x509 -req -in "${name}.csr" -CA "${ca}.pem" -CAkey "${ca}.key" \
    -extfile "${ext}" -out "${name}.pem" "$@" 2>/dev/null
}

printf 'basicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n' > ca.ext
printf 'basicConstraints=CA:FALSE\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n' > server.ext
printf 'basicConstraints=CA:FALSE\nsubjectAltName=DNS:www.test\nextendedKeyUsage=serverAuth\n' > sni.ext
printf 'basicConstraints=CA:FALSE\nextendedKeyUsage=clientAuth\n' > client.ext

new_key root.key
openssl req -x509 -new -key root.key -subj "/CN=Blog Test Root CA" -days 3650 \
  -addext "basicConstraints=critical,CA:TRUE" -out root.pem
issue_cert inter  "/CN=Blog Test Intermediate CA" root  ca.ext     -days 1825
issue_cert server "/CN=localhost"                 inter server.ext -days 90
issue_cert soon   "/CN=localhost"                 inter server.ext -days 1
issue_cert old    "/CN=localhost"                 inter server.ext \
  -not_before 20250101000000Z -not_after 20250401000000Z
issue_cert sni    "/CN=www.test"                  inter sni.ext    -days 90
issue_cert client "/CN=batch-job"                 inter client.ext -days 90
cat server.pem inter.pem > fullchain.pem

PORT=44300
# 연결 하나를 받고 끝나는 서버를 띄운다. -www 라 표준 입력을 읽지 않는다
serve() {
  PORT=$((PORT + 1))
  openssl s_server -accept "127.0.0.1:${PORT}" -naccept 1 -www -quiet "$@" >/dev/null 2>&1 &
  sleep 1
}

probe() {
  echo
  echo "\$ openssl s_client -connect 127.0.0.1:${PORT} $*"
  openssl s_client -connect "127.0.0.1:${PORT}" "$@" </dev/null 2>&1
  echo "[종료 코드 $?]"
  wait
}

echo
echo "== 1. 체인을 다 보내는 서버 =="
serve -cert server.pem -key server.key -cert_chain inter.pem
probe -CAfile root.pem -verify_hostname localhost -brief

echo
echo "== 2. 중간 인증서를 빠뜨린 서버 =="
serve -cert server.pem -key server.key
probe -CAfile root.pem -brief
serve -cert server.pem -key server.key
probe -CAfile root.pem -brief -verify_return_error

echo
echo "== 3. 서버가 보낸 인증서 세기 (-showcerts) =="
serve -cert server.pem -key server.key -cert_chain inter.pem
probe -CAfile root.pem -showcerts | grep -E '^ *[0-9] s:|^ +i:|BEGIN CERT|Verify return code|New Session Ticket'
serve -cert server.pem -key server.key
probe -CAfile root.pem -showcerts | grep -E '^ *[0-9] s:|^ +i:|BEGIN CERT|^Verify return code'

echo
echo "== 4. 호스트명이 다를 때 =="
serve -cert server.pem -key server.key -cert_chain inter.pem
probe -CAfile root.pem -verify_hostname db.internal.test -brief

echo
echo "== 5. 만료된 서버 =="
serve -cert old.pem -key old.key -cert_chain inter.pem
probe -CAfile root.pem -brief

echo
echo "== 6. SNI — 같은 포트에서 이름에 따라 다른 인증서 =="
serve -cert server.pem -key server.key -cert_chain inter.pem \
  -servername www.test -cert2 sni.pem -key2 sni.key
probe -CAfile root.pem -servername www.test -brief | grep -E 'Peer certificate|Verification'
serve -cert server.pem -key server.key -cert_chain inter.pem \
  -servername www.test -cert2 sni.pem -key2 sni.key
probe -CAfile root.pem -servername www.test -showcerts | grep -E '^ *[0-9] s:'
serve -cert server.pem -key server.key -cert_chain inter.pem \
  -servername www.test -cert2 sni.pem -key2 sni.key
probe -CAfile root.pem -noservername -brief | grep -E 'Peer certificate|Verification'

echo
echo "== 7. 프로토콜·ALPN·OCSP 상태 요청 =="
serve -cert server.pem -key server.key -cert_chain inter.pem
probe -CAfile root.pem -tls1_2 -brief
serve -cert server.pem -key server.key -cert_chain inter.pem -alpn h2,http/1.1
probe -CAfile root.pem -alpn h2 | grep -E 'ALPN'
serve -cert server.pem -key server.key -cert_chain inter.pem
probe -CAfile root.pem -status | grep -E 'OCSP'

echo
echo "== 8. 클라이언트 인증서를 요구하는 서버 =="
serve -cert server.pem -key server.key -cert_chain inter.pem -Verify 1 -CAfile root.pem -chainCAfile inter.pem
probe -CAfile root.pem -brief
serve -cert server.pem -key server.key -cert_chain inter.pem -Verify 1 -CAfile root.pem -chainCAfile inter.pem
probe -CAfile root.pem -cert client.pem -key client.key -cert_chain inter.pem -brief

echo
echo "== 9. 받은 인증서를 x509 로 넘겨 읽기 =="
serve -cert server.pem -key server.key -cert_chain inter.pem
openssl s_client -connect "127.0.0.1:${PORT}" -CAfile root.pem </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -serial -ext subjectAltName -nameopt RFC2253 \
  | sed -E 's/^(serial=).*/\1(난수, 생략)/'
wait

echo
echo "== 10. 만료 임박 판정 -checkend =="
for cert in server soon old; do
  openssl x509 -in "${cert}.pem" -noout -enddate
  openssl x509 -in "${cert}.pem" -noout -checkend 604800
  echo "[${cert}: 종료 코드 $?]"
done

echo
echo "== 11. 파일로 체인 검증 — openssl verify =="
# verify 는 실패 내용을 표준 오류로 내므로 합쳐서 순서대로 찍는다
check() {
  echo "\$ openssl verify $*"
  openssl verify "$@" 2>&1
  echo "[종료 코드 $?]"
}
check -CAfile root.pem server.pem
check -CAfile root.pem -untrusted inter.pem -show_chain server.pem
check -CAfile root.pem -untrusted inter.pem old.pem
NEXT_WEEK=$(( $(date +%s) + 604800 ))
check -CAfile root.pem -untrusted inter.pem -attime "${NEXT_WEEK}" soon.pem
