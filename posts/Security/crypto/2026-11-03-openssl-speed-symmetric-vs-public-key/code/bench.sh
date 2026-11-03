#!/usr/bin/env bash
# 대칭키와 공개키의 처리 속도를 같은 기계에서 재고, 차이를 바이트로 환산한다.
#
# 항목마다 2초씩 돈다. 1초로 줄여 봤더니 같은 기계에서도 다른 작업이 돌 때
# RSA-3072 서명이 792회/s 와 262회/s 사이에서 흔들렸다. 짧게 재면 비율까지
# 틀린다. 절대값은 기계와 부하에 따라 여전히 다르다.
#
# 측정은 알고리즘마다 한 번만 돌리고 결과를 파일에 받아 둔다. 같은 측정을
# 여러 번 돌리면 그만큼 느려지고, 절마다 값이 달라져 글의 숫자가 어긋난다.

set -u

DURATION=2
RULE="=============================================================="
WORK=$(mktemp -d)
trap 'rm -rf "${WORK}"' EXIT

section() {
    printf '\n%s\n%s\n%s\n' "${RULE}" "$1" "${RULE}"
}

# openssl speed 는 빌드 정보와 진행 상황을 측정값과 같이 찍는다. 측정값만 남긴다.
only_results() {
    grep -v -e '^version:' -e '^built on:' -e '^options:' -e '^compiler:' \
            -e '^CPUINFO:' -e "^The 'numbers' are" -e '^Doing '
}

measure() {
    local name="$1"; shift
    openssl speed -seconds "${DURATION}" "$@" 2>&1 | only_results > "${WORK}/${name}"
}

section "환경"
openssl version
printf '측정 시간: 항목마다 %s초\n' "${DURATION}"

measure aes128 -evp aes-128-gcm
measure aes256 -evp aes-256-gcm
measure chacha -evp chacha20-poly1305
measure sha256 -evp sha256
measure rsa rsa2048 rsa3072 rsa4096
measure ecdsa ecdsap256 ecdsap384 ecdsap521
measure ecdh ecdhp256 ecdhx25519

section "1. 대칭키 — 블록이 커질수록 처리량이 올라간다 (단위: 1000 바이트/초)"
cat "${WORK}/aes128"
tail -1 "${WORK}/aes256"
tail -1 "${WORK}/chacha"
tail -1 "${WORK}/sha256"

section "2. 공개키 — 초당 몇 번 하는가"
# RSA 는 같은 측정을 세 가지 표로 되풀이해 찍는다. 첫 표만 남긴다.
grep -E '^(rsa +[0-9]+ bits|.*encr\./s)' "${WORK}/rsa"
printf '\n'
cat "${WORK}/ecdsa"
printf '\n'
cat "${WORK}/ecdh"

section "3. 공개키 연산 한 번 하는 동안 대칭키는 몇 바이트를 처리하는가"
aes_16k=$(awk '/^AES-128-GCM/ {gsub(/k$/, "", $NF); print $NF}' "${WORK}/aes128")
rsa_sign=$(awk '/^rsa +2048 bits/ {print $8}' "${WORK}/rsa")
ecdsa_sign=$(awk '/ecdsa \(nistp256\)/ {print $(NF-1)}' "${WORK}/ecdsa")
ecdh_x=$(awk '/ecdh \(X25519\)/ {print $NF}' "${WORK}/ecdh")

printf 'AES-128-GCM 16KB 블록   %s kB/s\n' "${aes_16k}"
printf 'RSA-2048 서명           %s 회/s\n' "${rsa_sign}"
printf 'ECDSA P-256 서명        %s 회/s\n' "${ecdsa_sign}"
printf 'X25519 키 합의          %s 회/s\n' "${ecdh_x}"
awk -v aes="${aes_16k}" -v rsa="${rsa_sign}" -v ec="${ecdsa_sign}" -v dh="${ecdh_x}" 'BEGIN {
    printf "\nRSA-2048 서명 1회 시간 동안 AES 처리량    %8.2f MB\n", aes / rsa / 1024
    printf "ECDSA P-256 서명 1회 시간 동안 AES 처리량 %8.2f MB\n", aes / ec / 1024
    printf "X25519 키 합의 1회 시간 동안 AES 처리량   %8.2f MB\n", aes / dh / 1024
}'

section "4. 키 길이를 올리면 서명 비용이 어떻게 늘어나는가"
awk '/^rsa +[0-9]+ bits/ {printf "  RSA-%-6s %10.1f 서명/s %10.1f 검증/s\n", $2, $8, $9}' "${WORK}/rsa"
awk '/ecdsa \(/ {printf "  ECDSA %-11s %8.1f 서명/s %10.1f 검증/s\n", $4, $(NF-1), $NF}' "${WORK}/ecdsa"

section "5. RSA 서명 비용은 키 길이의 몇 제곱으로 늘어나는가"
awk 'BEGIN {n = 0}
     /^rsa +[0-9]+ bits/ {bits[n] = $2; rate[n] = $8; n++}
     END {
         for (i = 1; i < n; i++) {
             br = bits[i] / bits[i-1]
             sr = rate[i-1] / rate[i]
             printf "  %s → %s 비트: 비트 %.2f배, 서명 비용 %.2f배", bits[i-1], bits[i], br, sr
             printf "  (비트비의 세제곱 %.2f)\n", br * br * br
         }
     }' "${WORK}/rsa"
