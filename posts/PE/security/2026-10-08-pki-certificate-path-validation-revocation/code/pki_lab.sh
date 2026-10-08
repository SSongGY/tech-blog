#!/usr/bin/env bash
# 루트 CA → 중간 CA → 서버 인증서 3단 체인을 만들고, 검증 경로와 폐기 확인(CRL·OCSP)이
# 어느 지점에서 실패하는지 openssl 로 하나씩 확인한다.
# 키와 인증서는 probe_pki/ 아래에 만든다 (gitignore 대상, 돌릴 때마다 새로 만든다).
exec 2>&1
set -u

work=probe_pki
rm -rf "$work"
mkdir -p "$work"
# ca.cnf 가 $ENV::CA_DIR 을 읽으므로 req 도 이 값이 있어야 설정 파일을 연다
export CA_DIR="$work/root"

openssl version

init_ca() {
    # openssl ca 가 발급·폐기 이력을 적는 파일들
    mkdir -p "$work/$1/newcerts"
    : > "$work/$1/index.txt"
    echo "$2" > "$work/$1/serial"
    echo 01 > "$work/$1/crlnumber"
}

new_key() {
    openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$1" 2>/dev/null
}

new_csr() {
    # Git Bash 가 /CN=… 을 윈도우 경로로 바꾸지 않게 이 줄에만 끈다
    MSYS_NO_PATHCONV=1 openssl req -new -config ca.cnf -key "$1" -subj "$2" -out "$3"
}

issue() {
    # $1 발급 CA, $2 CSR, $3 결과 인증서, $4 확장 섹션
    CA_DIR="$work/$1" openssl ca -config ca.cnf -batch -notext \
        -in "$2" -out "$3" -extensions "$4" 2>&1 | grep -v '^Using configuration'
}

gencrl() {
    CA_DIR="$work/$1" openssl ca -config ca.cnf -gencrl -out "$2" 2>&1 \
        | grep -v '^Using configuration'
}

step() {
    echo
    echo "-- $1"
}

echo
echo "==== 0. 체인 만들기 ===="
init_ca root 1000
init_ca int 2000
new_key "$work/root/ca.key"
MSYS_NO_PATHCONV=1 openssl req -x509 -new -config ca.cnf -key "$work/root/ca.key" \
    -subj "/CN=Lab Root CA" -days 3650 -extensions v3_root -out "$work/root/ca.crt"

new_key "$work/int/ca.key"
new_csr "$work/int/ca.key" "/CN=Lab Issuing CA" "$work/int.csr"
issue root "$work/int.csr" "$work/int/ca.crt" v3_intermediate

for name in leaf leaf2 ocsp; do
    new_key "$work/$name.key"
done
new_csr "$work/leaf.key" "/CN=shop.example" "$work/leaf.csr"
issue int "$work/leaf.csr" "$work/leaf.crt" v3_leaf
new_csr "$work/leaf2.key" "/CN=api.example" "$work/leaf2.csr"
issue int "$work/leaf2.csr" "$work/leaf2.crt" v3_leaf
new_csr "$work/ocsp.key" "/CN=Lab OCSP Responder" "$work/ocsp.csr"
issue int "$work/ocsp.csr" "$work/ocsp.crt" v3_ocsp

cp "$work/root/ca.crt" "$work/root.crt"
cp "$work/int/ca.crt" "$work/int.crt"

step "체인 확인 — 발급자와 주체"
for name in root int leaf; do
    openssl x509 -in "$work/$name.crt" -noout -subject -issuer -serial
done

echo
echo "==== 1. 검증 경로 ===="
step "1-1. 루트를 신뢰하고 중간 CA 를 함께 넘김"
openssl verify -CAfile "$work/root.crt" -untrusted "$work/int.crt" "$work/leaf.crt"
echo "종료 코드 $?"

step "1-2. 중간 CA 를 빼고 넘김 (서버가 체인을 안 보낸 경우)"
openssl verify -CAfile "$work/root.crt" "$work/leaf.crt"
echo "종료 코드 $?"

step "1-3. 중간 CA 만 신뢰 앵커로 (루트 없이)"
openssl verify -CAfile "$work/int.crt" "$work/leaf.crt"
echo "종료 코드 $?"

step "1-4. 1-3 에 -partial_chain — 중간 CA 를 앵커로 인정"
openssl verify -partial_chain -CAfile "$work/int.crt" "$work/leaf.crt"
echo "종료 코드 $?"

echo
echo "==== 2. CRL ===="
CA_DIR="$work/int" openssl ca -config ca.cnf -revoke "$work/leaf.crt" \
    -crl_reason keyCompromise 2>&1 | grep -v '^Using configuration'
gencrl int "$work/int.crl"
gencrl root "$work/root.crl"

step "2-1. 중간 CA 가 낸 CRL 내용"
openssl crl -in "$work/int.crl" -noout -text \
    | grep -E 'Issuer:|Last Update|Next Update|Serial Number|Revocation Date|Key Compromise|CRL Number' \
    | sed 's/^ *//'

step "2-2. 폐기 확인을 켜지 않으면 (-crl_check 없음)"
openssl verify -CAfile "$work/root.crt" -untrusted "$work/int.crt" "$work/leaf.crt"
echo "종료 코드 $?"

step "2-3. -crl_check 를 켰는데 CRL 을 못 구했으면"
openssl verify -crl_check -CAfile "$work/root.crt" -untrusted "$work/int.crt" "$work/leaf.crt"
echo "종료 코드 $?"

step "2-4. -crl_check + CRL 제공"
openssl verify -crl_check -CAfile "$work/root.crt" -untrusted "$work/int.crt" \
    -CRLfile "$work/int.crl" "$work/leaf.crt"
echo "종료 코드 $?"

step "2-5. 폐기되지 않은 leaf2 는"
openssl verify -crl_check -CAfile "$work/root.crt" -untrusted "$work/int.crt" \
    -CRLfile "$work/int.crl" "$work/leaf2.crt"
echo "종료 코드 $?"

step "2-6. CRL 의 nextUpdate 가 지난 시각(이틀 뒤)으로 검증"
later=$(( $(date +%s) + 2 * 86400 ))
openssl verify -crl_check -attime "$later" -CAfile "$work/root.crt" -untrusted "$work/int.crt" \
    -CRLfile "$work/int.crl" "$work/leaf2.crt"
echo "종료 코드 $?"

echo
echo "==== 3. 중간 CA 가 폐기되면 ===="
CA_DIR="$work/root" openssl ca -config ca.cnf -revoke "$work/int.crt" \
    -crl_reason cACompromise 2>&1 | grep -v '^Using configuration'
gencrl root "$work/root.crl"

step "3-1. -crl_check (말단 인증서만 확인) — leaf2"
openssl verify -crl_check -CAfile "$work/root.crt" -untrusted "$work/int.crt" \
    -CRLfile "$work/int.crl" -CRLfile "$work/root.crl" "$work/leaf2.crt"
echo "종료 코드 $?"

step "3-2. -crl_check_all (경로 전체 확인) — leaf2"
openssl verify -crl_check_all -CAfile "$work/root.crt" -untrusted "$work/int.crt" \
    -CRLfile "$work/int.crl" -CRLfile "$work/root.crl" "$work/leaf2.crt"
echo "종료 코드 $?"

echo
echo "==== 4. OCSP ===="
cat "$work/root.crt" "$work/int.crt" > "$work/chain.pem"

ask() {
    # $1 질의 대상 인증서, $2 응답 서명 인증서, $3 응답 서명 키
    openssl ocsp -issuer "$work/int.crt" -cert "$1" -reqout "$work/req.der" >/dev/null
    openssl ocsp -index "$work/int/index.txt" -CA "$work/int.crt" \
        -rsigner "$2" -rkey "$3" -reqin "$work/req.der" -respout "$work/resp.der" \
        -ndays 1 >/dev/null
    openssl ocsp -respin "$work/resp.der" -issuer "$work/int.crt" -cert "$1" \
        -CAfile "$work/chain.pem" -no_nonce
    echo "종료 코드 $?"
}

step "4-1. 폐기된 leaf — OCSP 전용 인증서로 서명한 응답"
ask "$work/leaf.crt" "$work/ocsp.crt" "$work/ocsp.key"

step "4-2. 폐기되지 않은 leaf2"
ask "$work/leaf2.crt" "$work/ocsp.crt" "$work/ocsp.key"

step "4-3. OCSPSigning 용도가 없는 인증서(leaf2)로 서명한 응답"
ask "$work/leaf.crt" "$work/leaf2.crt" "$work/leaf2.key"

step "4-4. CA 에 기록이 없는 일련번호"
openssl ocsp -issuer "$work/int.crt" -serial 0x9999 -reqout "$work/req.der" >/dev/null
openssl ocsp -index "$work/int/index.txt" -CA "$work/int.crt" \
    -rsigner "$work/ocsp.crt" -rkey "$work/ocsp.key" -reqin "$work/req.der" \
    -respout "$work/resp.der" -ndays 1 >/dev/null
openssl ocsp -respin "$work/resp.der" -issuer "$work/int.crt" -serial 0x9999 \
    -CAfile "$work/chain.pem" -no_nonce
echo "종료 코드 $?"

step "4-5. 응답의 시각 필드 (4-4 응답)"
openssl ocsp -respin "$work/resp.der" -resp_text -noverify \
    | grep -E 'Produced At|This Update|Next Update|Cert Status' | sed 's/^ *//'
