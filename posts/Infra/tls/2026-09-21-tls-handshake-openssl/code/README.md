# openssl s_client로 TLS 핸드셰이크 갈라 보기

## 실행

```bash
bash handshake_probe.sh                  # 기본 대상 www.iana.org:443
bash handshake_probe.sh example.com 443  # 다른 호스트
```

필요한 것: `openssl`, `bash`, `python`(6단계에서 연결을 잠깐 유지하는 데만 쓴다).
확인 환경: OpenSSL 3.5.6 (2026-04-07) / Git Bash on Windows 11.
외부로 TLS 접속이 나가므로 사내 프록시 환경에서는 결과가 달라질 수 있다.

## 각 단계가 보는 것

| 단계 | 확인하는 것 |
|---|---|
| 1 | 기본 설정으로 무엇이 협상되는가 (버전·암호 스위트·키 교환 그룹) |
| 2 | `-tls1_2`로 내렸을 때 무엇이 달라지는가 |
| 3 | 실제로 오간 핸드셰이크 메시지 순서 |
| 4 | 키 교환 그룹이 ClientHello 크기를 얼마나 키우는가 |
| 5 | 인증서 체인의 깊이와 각 단계의 발급자·유효기간 |
| 6 | 세션 티켓 재사용이 주고받는 바이트를 어떻게 바꾸는가 |

## 바꿔 볼 값

- `-groups`에 넣는 그룹 이름 — `openssl ecparam -list_curves`와
  `openssl list -tls1_3-groups`(빌드에 따라 다름)로 후보를 볼 수 있다.
- `-tls1_2`를 `-tls1_1`이나 `-tls1`로 바꾸기 — 최신 서버는 거절한다.
  거절 방식(알림 메시지)도 `-msg`로 볼 수 있다.
- 6단계 `time.sleep(5)`의 초 — 너무 짧으면 티켓을 받기 전에 끊긴다.
- 대상 호스트 — `-servername`을 일부러 빼면 SNI 없이 접속해
  공유 IP에서 어떤 인증서가 오는지 볼 수 있다.
