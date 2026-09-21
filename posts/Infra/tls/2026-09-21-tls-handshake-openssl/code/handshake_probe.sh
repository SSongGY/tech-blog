#!/usr/bin/env bash
# openssl s_client로 TLS 핸드셰이크를 갈라 보는 조사 스크립트.
# 인자로 호스트를 받는다. 기본값은 www.iana.org.
set -u

host="${1:-www.iana.org}"
port="${2:-443}"

banner() { printf '\n===== %s =====\n' "$1"; }

banner "1. 협상 결과 요약 (기본 설정)"
echo | openssl s_client -connect "$host:$port" -servername "$host" -brief 2>&1 |
  grep -E 'Protocol version|Ciphersuite|Peer certificate|Verification|Negotiated'

banner "2. TLS 1.2로 내려서 협상"
echo | openssl s_client -connect "$host:$port" -servername "$host" -tls1_2 -brief 2>&1 |
  grep -E 'Protocol version|Ciphersuite|Peer Temp Key|Verification'

banner "3. 핸드셰이크 메시지 순서 (TLS 1.3)"
echo | openssl s_client -connect "$host:$port" -servername "$host" -msg 2>&1 |
  grep -E '^(>>>|<<<).*(Hello|Certificate|Finished|EncryptedExtensions|KeyExchange|HelloDone|NewSessionTicket)'

banner "4. 키 교환 그룹별 ClientHello 크기"
for group in X25519MLKEM768 X25519 P-256; do
  size=$(echo | openssl s_client -connect "$host:$port" -servername "$host" \
           -groups "$group" -msg 2>&1 |
         grep -m1 'ClientHello' | grep -oE 'length [0-9a-f]{4}' | cut -d' ' -f2)
  # -msg는 길이를 16진수로 찍으므로 10진수로 바꿔 보여 준다.
  printf '  %-16s ClientHello 0x%s = %d 바이트\n' "$group" "$size" "$((16#$size))"
done

banner "5. 인증서 체인"
echo | openssl s_client -connect "$host:$port" -servername "$host" 2>&1 |
  sed -n '/Certificate chain/,/^---/p' | grep -E '^ [0-9] s:|^   i:|^   v:'

banner "6. 세션 티켓 저장과 재사용"
ticket=$(mktemp)
# TLS 1.3의 NewSessionTicket은 핸드셰이크가 끝난 뒤에 온다.
# 곧바로 끊으면 티켓을 못 받으므로 요청을 보내고 잠깐 연결을 유지한다.
python -c "
import sys, time
sys.stdout.write('GET / HTTP/1.1\r\nHost: $host\r\nConnection: close\r\n\r\n')
sys.stdout.flush()
time.sleep(5)" |
  openssl s_client -connect "$host:$port" -servername "$host" \
    -sess_out "$ticket" -quiet >/dev/null 2>&1

if [ -s "$ticket" ]; then
  echo "  티켓 저장됨: $(wc -c <"$ticket") 바이트"
  echo "  -- 티켓 없이 새로 접속"
  echo | openssl s_client -connect "$host:$port" -servername "$host" 2>&1 |
    grep -E '^New,|^Reused,|handshake has read'
  echo "  -- 저장한 티켓으로 재접속"
  echo | openssl s_client -connect "$host:$port" -servername "$host" -sess_in "$ticket" 2>&1 |
    grep -E '^New,|^Reused,|handshake has read'
else
  echo "  티켓을 받지 못했다. 서버가 티켓을 안 보내거나 연결이 너무 빨리 끊겼다."
fi
rm -f "$ticket"
