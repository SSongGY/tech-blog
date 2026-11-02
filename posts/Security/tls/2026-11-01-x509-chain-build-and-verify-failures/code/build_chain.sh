#!/usr/bin/env bash
#
# 루트 CA → 중간 CA → 서버 인증서를 직접 만들고,
# 체인을 한 군데씩 망가뜨려 openssl verify 가 내는 문구를 모은다.
#
# 만들어지는 파일은 전부 probe_work/ 아래에 들어가고 실행할 때마다 지워진다.

set -u

# Git Bash(MSYS)는 '/C=KR/O=...' 같은 인자를 윈도우 경로로 바꿔 버려서
# openssl 이 주체 이름을 'C:/Program Files/Git/C=KR/...' 로 받는다.
# 리눅스·macOS 에는 이 변수가 없고, 있어도 아무 영향이 없다.
export MSYS2_ARG_CONV_EXCL='*'

WORK_DIR="probe_work"
EXT_DIR="ext"

banner() {
    printf '\n----------------------------------------------------------------\n'
    printf '%s\n' "$1"
    printf -- '----------------------------------------------------------------\n'
}

# verify 는 실패해도 스크립트를 세우지 않는다. 실패 문구를 모으는 것이 목적이다.
try_verify() {
    local title="$1"
    shift
    printf '  %s\n' "${title}"
    printf '  $ openssl %s\n' "$*"
    openssl "$@" 2>&1 | sed 's/^/      /'
    printf '      (종료 코드 %d)\n\n' "${PIPESTATUS[0]}"
}

new_key_and_csr() {
    local name="$1"
    local subject="$2"
    openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -noenc \
        -keyout "${WORK_DIR}/${name}.key" -out "${WORK_DIR}/${name}.csr" \
        -subj "${subject}" 2>/dev/null
}

sign_with() {
    local issuer="$1" name="$2" ext_file="$3" serial="$4"
    shift 4
    openssl x509 -req -in "${WORK_DIR}/${name}.csr" \
        -CA "${WORK_DIR}/${issuer}.pem" -CAkey "${WORK_DIR}/${issuer}.key" \
        -extfile "${EXT_DIR}/${ext_file}" -set_serial "${serial}" \
        -out "${WORK_DIR}/${name}.pem" "$@" 2>/dev/null
}

banner "환경"
openssl version -a | sed -n '1,3p' | sed 's/^/  /'

rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}"

banner "1. 세 단계 체인을 만든다"

openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -noenc \
    -keyout "${WORK_DIR}/root.key" -out "${WORK_DIR}/root.pem" -days 3650 \
    -subj "/C=KR/O=Example Trust/CN=Example Root CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null

new_key_and_csr "inter" "/C=KR/O=Example Trust/CN=Example Intermediate CA"
sign_with "root" "inter" "intermediate.ext" 2 -days 1825

new_key_and_csr "server" "/C=KR/O=Example Service/CN=shop.example.com"
sign_with "inter" "server" "server.ext" 3 -days 365

for cert in root inter server; do
    printf '  %-7s subject= %s\n' "${cert}" \
        "$(openssl x509 -in "${WORK_DIR}/${cert}.pem" -noout -subject -nameopt oneline,sep_comma_plus | sed 's/^subject=//')"
    printf '  %-7s issuer = %s\n' "" \
        "$(openssl x509 -in "${WORK_DIR}/${cert}.pem" -noout -issuer -nameopt oneline,sep_comma_plus | sed 's/^issuer=//')"
done

printf '\n  중간 CA 의 제약:\n'
openssl x509 -in "${WORK_DIR}/inter.pem" -noout -ext basicConstraints | sed 's/^/    /'

banner "2. 정상 체인 — 루트를 신뢰하고 중간을 함께 준다"
try_verify "체인 전체를 보여 달라고 한다" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    -show_chain "${WORK_DIR}/server.pem"

banner "3. 중간 인증서를 빠뜨린다 — 서버 설정에서 가장 흔한 실수"
try_verify "루트만 주고 중간을 주지 않는다" \
    verify -CAfile "${WORK_DIR}/root.pem" "${WORK_DIR}/server.pem"

banner "4. 신뢰 앵커가 없다 — 사설 CA 를 OS 가 모를 때"
try_verify "중간은 주되 루트를 신뢰 목록에서 뺀다" \
    verify -no-CAfile -no-CApath -untrusted "${WORK_DIR}/inter.pem" \
    -untrusted "${WORK_DIR}/root.pem" "${WORK_DIR}/server.pem"

banner "5. 기간이 지났다"
new_key_and_csr "expired" "/C=KR/O=Example Service/CN=shop.example.com"
sign_with "inter" "expired" "server.ext" 4 \
    -not_before 20240101000000Z -not_after 20240401000000Z
openssl x509 -in "${WORK_DIR}/expired.pem" -noout -dates | sed 's/^/  /'
printf '\n'
try_verify "만료된 서버 인증서" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    "${WORK_DIR}/expired.pem"

try_verify "같은 인증서를 유효기간 안의 시각으로 검증한다" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    -attime 1709251200 "${WORK_DIR}/expired.pem"

banner "6. 이름이 다르다"
printf '  서버 인증서의 subjectAltName:\n'
openssl x509 -in "${WORK_DIR}/server.pem" -noout -ext subjectAltName | sed 's/^/    /'
printf '\n'
try_verify "인증서에 적힌 이름으로 검증" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    -verify_hostname shop.example.com "${WORK_DIR}/server.pem"

try_verify "적혀 있지 않은 이름으로 검증" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    -verify_hostname app.example.com "${WORK_DIR}/server.pem"

try_verify "CN 은 같지만 SAN 에 없는 상위 도메인" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    -verify_hostname example.com "${WORK_DIR}/server.pem"

banner "7. 중간 인증서가 CA 가 아니다"
sign_with "root" "inter" "intermediate-notca.ext" 5 -days 1825
openssl x509 -in "${WORK_DIR}/inter.pem" -noout -ext basicConstraints | sed 's/^/  /'
printf '\n'
try_verify "같은 키로 CA:FALSE 로 다시 발급한 중간 인증서" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/inter.pem" \
    "${WORK_DIR}/server.pem"

banner "8. pathlen 을 넘긴다"
# 7번에서 inter.pem 을 CA:FALSE 로 덮어썼으므로 CA:TRUE 로 되돌린다.
sign_with "root" "inter" "intermediate.ext" 6 -days 1825
new_key_and_csr "subca" "/C=KR/O=Example Trust/CN=Example Sub CA"
sign_with "inter" "subca" "subca.ext" 7 -days 900
new_key_and_csr "leaf" "/C=KR/O=Example Service/CN=shop.example.com"
sign_with "subca" "leaf" "server.ext" 8 -days 365

cat "${WORK_DIR}/inter.pem" "${WORK_DIR}/subca.pem" > "${WORK_DIR}/bundle.pem"
try_verify "중간 CA 의 pathlen:0 아래에 또 CA 를 끼운다" \
    verify -CAfile "${WORK_DIR}/root.pem" -untrusted "${WORK_DIR}/bundle.pem" \
    "${WORK_DIR}/leaf.pem"

banner "끝"
