---
title: "QUIC와 HTTP/3 — TCP 위에서 못 풀던 세 가지를 UDP로 내려가 푼 이유"
date: 2026-10-07
categories: [PE]
subcategory: network
track: pe
tags: [정보관리기술사, quic, http3, 개념정리]
description: "QUIC를 RFC 9000(전송)·9001(TLS 통합)·9002(손실 복구)로, HTTP/3를 RFC 9114로 세운다. HTTP/2가 TCP 위에서 못 풀던 머리 막힘·연결 수립 왕복·주소 변경 세 문제를 QUIC가 스트림·통합 핸드셰이크·연결 ID로 어떻게 푸는지, 왜 UDP 위에 사용자 공간으로 만들었는지를 정리한다. RFC 9000의 가변 길이 정수 예시 4개를 디코딩·재인코딩해 전부 일치했고, 스트림 ID 하위 2비트 규칙과 머리 막힘 모형도 계산으로 확인했다."
difficulty: 중급
feature:
environment: ["RFC 9000 (2021-05)", "RFC 9001 (2021-05)", "RFC 9002 (2021-05)", "RFC 9114 (2022-06)", "RFC 8446 (2018-08)", "Python 3.13.5"]
verification: executed
verified: true
topic_id: pe-057
---

> 이 글의 숫자는 RFC의 규칙을 [`code/quic_calc.py`](code/quic_calc.py)로 계산한 값이다. 패킷을 실제로 주고받은
> 실험이 아니다. 실행 기록은 [`code/output.txt`](code/output.txt)에 있다.

## 들어가며

HTTP/3 문항은 "QUIC의 특징을 설명하라"로 나오고, 대개 "UDP 기반이라 빠르다"로 답이 시작된다. 이 문장은 틀렸다.
UDP는 아무것도 빠르게 해 주지 않는다. 점수가 갈리는 곳은 **TCP 위의 HTTP/2가 무엇을 못 풀었고, 그것을 풀려면
왜 전송 계층을 다시 만들어야 했으며, 그 새 전송 계층을 왜 UDP 위에 얹었는가**다. 실무에서는 모바일 앱이
Wi-Fi에서 LTE로 넘어갈 때 연결이 끊기거나, 이미지 수십 장을 받는 페이지에서 패킷 하나가 사라지자 전부 멈추는
현상으로 만난다. 이 글은 그 세 문제를 축으로 QUIC와 HTTP/3를 정리한다.

## 정의

> **QUIC**: UDP 데이터그램에 실려 전달되는 **보안이 내장된 범용 전송 프로토콜**. 연결 지향이며, 암호 매개변수와
> 전송 매개변수의 협상을 핸드셰이크 하나로 합치고, 스트림이라는 순서 있는 바이트열 여러 개를 한 연결에 다중화한다
> (RFC 9000 개요 절, §1).

> **HTTP/3**: **HTTP 의미(RFC 9110)를 QUIC 전송 위에 대응시킨 것.** HTTP/2 설계를 많이 따르되, 스트림 수명과
> 흐름 제어는 QUIC에 맡기고 스트림마다 HTTP/2와 비슷한 이진 프레이밍을 쓴다(RFC 9114 QUIC 위임 절, §1.2).

두 정의에서 시험에 쓸 핵심은 하나다. **HTTP/3는 HTTP를 바꾼 것이 아니라 전송을 바꾼 것이다.** 메서드·상태 코드·헤더
필드의 의미는 그대로다.

## 등장 배경 — TCP 위에서 못 푼 세 가지

RFC 9114의 서론(§1)은 이전 세대의 한계를 순서대로 적는다.

| 세대 | 무엇을 했나 | 무엇이 남았나 |
|---|---|---|
| HTTP/1.1 | 텍스트 메시지. 다중화 계층이 없어 병렬 요청에 TCP 연결 여러 개를 쓴다 | 연결마다 혼잡 제어가 따로 돈다. 망 효율이 나쁘다 |
| HTTP/2 | 이진 프레이밍과 **다중화 계층**을 넣어 연결 하나로 병렬 요청 | 다중화가 **TCP의 손실 복구에는 보이지 않는다.** 패킷 하나가 사라지거나 순서가 바뀌면 그 패킷과 무관한 트랜잭션까지 전부 멈춘다 |

세 문제로 정리하면 다음과 같다.

1. **머리 막힘(head-of-line blocking)**: TCP는 바이트열 하나다. 사라진 패킷 뒤의 바이트는 재전송이 올 때까지 응용에
   올라가지 못한다. HTTP/2가 응용 계층에서 스트림을 나눠도 TCP는 그 경계를 모른다.
2. **연결 수립 왕복**: TCP 3-way 핸드셰이크(RFC 9293 §3.5) 1 RTT 뒤에 TLS 1.3 핸드셰이크(RFC 8446 §2) 1 RTT가 또
   든다. 첫 요청까지 2 RTT다.
3. **주소에 묶인 연결**: TCP 연결은 (출발지 IP·포트, 목적지 IP·포트) 네 값으로 식별된다. 단말이 망을 옮겨 IP가 바뀌면
   연결은 끝난다.

이 셋은 전부 **TCP 자체의 성질**이라 HTTP를 아무리 고쳐도 풀리지 않는다. 전송 계층을 바꿔야 한다. 그런데 새 전송
프로토콜을 IP 위에 직접 올리면 운영체제 커널과 중간 장비(NAT·방화벽)가 전부 바뀌어야 한다. RFC 9000은 QUIC 패킷을
**기존 시스템과 망에 배포하기 쉽도록 UDP 데이터그램에 싣는다**고 적는다(§1). UDP는 빠르라고 고른 것이 아니라
**이미 뚫려 있는 길**이라서 고른 것이다.

## 구성요소 — 세 문제에 대응하는 QUIC의 장치 3가지

### ① 스트림 — 머리 막힘을 스트림 하나로 가둔다

QUIC는 한 연결 안에 스트림 여러 개를 두고, **순서 보장과 손실 복구를 스트림 단위로** 한다. RFC 9114는 QUIC가
"스트림 수준의 신뢰성과 연결 전체의 혼잡 제어"를 제공한다고 적는다(§1.2). 패킷 하나가 사라지면 그 패킷에 실린
스트림만 재전송을 기다리고 다른 스트림의 데이터는 그대로 올라간다.

스트림은 62비트 ID로 구별하고, **하위 2비트**가 종류를 정한다(RFC 9000 §2.1).

| 하위 2비트 | 종류 | HTTP/3에서의 쓰임 |
|---|---|---|
| `0x00` | 클라이언트 시작 · 양방향 | 요청 스트림. 요청 하나에 스트림 하나(RFC 9114 §4.1) |
| `0x01` | 서버 시작 · 양방향 | HTTP/3는 쓰지 않는다 |
| `0x02` | 클라이언트 시작 · 단방향 | 제어 스트림(0x00)·QPACK 인코더/디코더 스트림 |
| `0x03` | 서버 시작 · 단방향 | 제어 스트림·푸시 스트림(0x01)·QPACK 스트림 |

### ② 통합 핸드셰이크 — 왕복을 하나로 합친다

QUIC는 TLS 1.3 핸드셰이크 메시지를 **CRYPTO 프레임에 담아 QUIC 패킷으로 직접** 나른다. RFC 9001은 "TLS 레코드를
QUIC 위에 싣는 대신, TLS 핸드셰이크와 경고 메시지를 QUIC 전송 위에 직접 실으며 QUIC가 TLS 레코드 계층의 역할을
넘겨받는다"고 적는다(§3). 그래서 전송 핸드셰이크와 암호 핸드셰이크가 **한 왕복에** 끝난다. 이전 연결의 정보가 있으면
클라이언트가 첫 패킷에 데이터를 실어 보내는 **0-RTT**도 있다(RFC 9000 §1).

암호화 수준은 4가지다 — Initial, 0-RTT, Handshake, 1-RTT(RFC 9001 §4.1.3). 응용 프로토콜은 ALPN으로 고르며,
HTTP/3의 토큰은 `h3`다(RFC 9114 §3.1). ALPN 협상에 실패하면 연결을 닫아야 한다(RFC 9001 §8.1).

### ③ 연결 ID — 주소가 바뀌어도 연결을 잇는다

QUIC 연결은 IP·포트가 아니라 **연결 ID**로 식별된다. RFC 9000은 연결 ID 덕에 "엔드포인트 주소(IP 주소와 포트)가
바뀌어도 연결이 살아남는다"고 적고, 이것을 **연결 이전(connection migration)** 이라 부른다(§9). 이 판에서는 클라이언트만
이전할 수 있다(§1). NAT가 매핑을 바꿔도 같은 원리로 연결이 유지된다.

### 덤 — 손실 복구가 TCP와 다른 점 (RFC 9002 §4)

패킷 번호는 **단조 증가하고 재사용하지 않는다.** 재전송도 새 번호를 받으므로 "원본에 대한 ACK인지 재전송에 대한
ACK인지" 모호함이 없다(§4.2). ACK 범위를 TCP SACK의 3개보다 많이 실을 수 있고(§4.5), 상대의 ACK 지연을 명시적으로
보정해 RTT를 더 정확히 잰다(§4.6). 기본 혼잡 제어는 TCP NewReno와 비슷한 것이고, 송신자가 CUBIC 같은 다른 알고리즘을
혼자 골라 쓸 수 있다(§7). 알고리즘 자체는 [TCP 혼잡 제어 — Reno·CUBIC·BBR](../2026-10-06-tcp-congestion-control-reno-cubic-bbr/index.md)에서 다뤘다.

## 도식

![HTTP/2 over TCP와 HTTP/3 over QUIC의 계층 비교. 왼쪽은 HTTP 의미, HTTP/2 프레이밍(스트림 다중화·흐름 제어·HPACK), TLS 1.3, TCP(바이트열 하나·손실 복구·혼잡 제어), IP. 오른쪽은 HTTP 의미, HTTP/3 프레이밍(QPACK), QUIC(스트림 다중화·스트림별 흐름 제어·스트림 단위 손실 복구·TLS 1.3 핸드셰이크 통합·연결 ID), UDP, IP. HTTP/2 프레이밍이 하던 다중화·흐름 제어가 QUIC로 내려갔다](fig/http2-vs-http3-stack.svg)

> **출처**: [RFC 9114 §1.2 Delegation to QUIC](https://www.rfc-editor.org/rfc/rfc9114.html#section-1.2)(다중화·흐름 제어의 QUIC 위임, 스트림마다 프레이밍),
> [RFC 9001 §3 Protocol Overview](https://www.rfc-editor.org/rfc/rfc9001.html#section-3)(QUIC가 TLS 레코드 계층을 대신, Figure 3),
> [RFC 9000 §1 Overview](https://www.rfc-editor.org/rfc/rfc9000.html#section-1)(UDP 데이터그램에 실음, 연결 ID로 이전),
> [RFC 9114 §4.2 HTTP Fields](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.2)(QPACK).

답안지에는 두 기둥만 그린다. 왼쪽 기둥은 **TCP 한 칸이 전부를 막는다**, 오른쪽 기둥은 **QUIC 한 칸이 스트림·보안·손실 복구를
다 가진다**를 적으면 된다.

## 계산으로 확인한 것

RFC 9000의 규칙 세 가지를 코드로 옮겨 RFC의 예시와 맞췄다.

**가변 길이 정수(§16).** QUIC는 프레임의 길이·스트림 ID 같은 정수를 첫 바이트의 상위 2비트로 길이를 정하는 방식으로 적는다.
부록 A.1의 예시 4개를 디코딩하고 다시 인코딩했다.

```text
   2MSB | 길이 | 쓰는 비트 | 최대값
   00   | 1    |  6        | 63
   01   | 2    | 14        | 16,383
   10   | 4    | 30        | 1,073,741,823
   11   | 8    | 62        | 4,611,686,018,427,387,903

   c2197c5eff14e88c   -> 8바이트, 값 151,288,809,941,952,652  RFC 일치 · 재인코딩 일치
   9d7f3e7d           -> 4바이트, 값 494,878,333  RFC 일치 · 재인코딩 일치
   7bbd               -> 2바이트, 값 15,293  RFC 일치 · 재인코딩 일치
   25                 -> 1바이트, 값 37  RFC 일치 · 재인코딩 일치
```

4개 모두 일치했다. 같은 값 300을 2·4·8바이트 형식으로 적어도 디코더는 전부 300으로 읽었다. 길이가 값이 아니라 **첫 바이트의
상위 2비트**로만 정해지기 때문이다. 스트림 ID의 상한 2^62 − 1도 이 표의 마지막 줄에서 나온다.

**스트림 ID(§2.1).** ID 0~11을 하위 2비트로 분류하니 0·4·8이 클라이언트 양방향, 2·6·10이 클라이언트 단방향으로 나왔다.
RFC 9114가 요청 스트림을 "클라이언트 시작 양방향 스트림"이라 적은 것과 맞는다.

**머리 막힘 모형.** 스트림 A·B·C가 패킷 6개에 번갈아 실렸고 2번 패킷이 사라졌다고 두고, RFC 9114 §1의 문장을 규칙으로 옮겼다.

```text
   전송 순서: 1:A 2:B 3:C 4:A 5:B 6:C
   TCP 위 HTTP/2 — 재전송을 기다리는 스트림: ['A', 'B', 'C']  (3개)
   QUIC 위 HTTP/3 — 재전송을 기다리는 스트림: ['B']  (1개)
```

TCP 모형은 사라진 패킷 뒤의 바이트를 전부 멈추므로 3·4·5·6번에 실린 A·C까지 기다린다. QUIC 모형은 B만 기다린다.
이것은 RFC의 문장을 그대로 옮긴 모형이지 측정이 아니다. 실제 지연은 재전송 타이머와 혼잡 제어가 정한다.

**왕복 수.** RFC가 적은 왕복 수(TCP 1 + TLS 1.3 1 = 2, QUIC 1, 0-RTT 0)에 RTT를 곱하면 RTT 100ms에서 첫 요청까지
200ms 대 100ms다. 왕복이 한 번 줄어든 만큼이고, 그 이상도 이하도 아니다.

## 비교

| 항목 | HTTP/2 over TCP (RFC 9113) | HTTP/3 over QUIC (RFC 9114) |
|---|---|---|
| 전송 | TCP, 바이트열 하나 | QUIC over UDP, 스트림 여러 개 |
| 손실 복구 단위 | 연결 전체 | 스트림 |
| 다중화·흐름 제어 | HTTP/2 프레이밍 계층 | QUIC 전송 계층 |
| 보안 | TLS를 TCP 위에 따로 | TLS 1.3 핸드셰이크를 QUIC가 통합, 패킷 보호가 레코드 계층 대신 |
| 첫 요청까지 | 2 RTT (TCP 1 + TLS 1) | 1 RTT, 재개 시 0-RTT |
| 연결 식별 | IP·포트 4요소 | 연결 ID — 주소가 바뀌어도 유지 |
| 헤더 압축 | HPACK (RFC 7541) | QPACK (RFC 9204) — 압축이 일으키는 머리 막힘을 인코더가 조절 |
| 프레임 | DATA·HEADERS·PRIORITY·RST_STREAM·SETTINGS·PUSH_PROMISE·PING·GOAWAY·WINDOW_UPDATE·CONTINUATION | DATA·HEADERS·CANCEL_PUSH·SETTINGS·PUSH_PROMISE·GOAWAY·MAX_PUSH_ID — 흐름 제어·리셋·핑은 QUIC가 맡아 프레임에서 빠짐 |
| 발견 | ALPN `h2` | ALPN `h3`, `Alt-Svc` 헤더로 광고 |

## 적용 시 고려사항

- **0-RTT 데이터는 재생(replay)될 수 있다.** RFC 9001은 0-RTT가 TLS 1.3 early data와 같은 재생 노출을 가지며, 재생 시
  원치 않는 효과를 낼 수 있는 요청에는 맞지 않는다고 적는다(§9.2). GET 같은 멱등 요청만 0-RTT로 보낸다.
- **UDP가 막힌 망이 있다.** 기업 방화벽이 UDP 443을 닫아 두면 QUIC가 서지 않는다. HTTP/3 클라이언트는 TCP로 폴백해야
  하고, 서버는 `Alt-Svc`로 광고만 할 뿐 강제하지 않는다(RFC 9114 §3.1).
- **혼잡 제어와 손실 복구가 커널이 아니라 라이브러리에 있다.** 사용자 공간 구현이라 배포는 쉽지만 CPU 비용이 커널 TCP보다
  크고, 어느 라이브러리를 쓰느냐에 따라 동작이 다르다. RFC 9002는 기본 알고리즘만 정하고 다른 알고리즘 선택을 허용한다(§7).
- **네트워크 가시성이 준다.** QUIC는 헤더까지 암호화하므로 중간 장비가 TCP처럼 순서 번호나 상태를 볼 수 없다. 운영 모니터링은
  엔드포인트 로그에 기대야 한다.
- **연결 이전은 클라이언트만 한다.** 이 판의 QUIC는 서버 쪽 주소 변경을 지원하지 않는다(RFC 9000 §1). 서버 이중화는
  별도 수단으로 푼다.

## 정리

- **세 문제**: 머리 막힘 · 연결 수립 2 RTT · 주소에 묶인 연결. 전부 TCP의 성질이라 전송 계층을 바꿔야 했다.
- **세 장치**: 스트림(손실을 스트림 하나에 가둠) · 통합 핸드셰이크(1 RTT, 재개 0-RTT) · 연결 ID(주소가 바뀌어도 유지).
- **UDP를 고른 이유**는 속도가 아니라 **배포**다. 커널과 중간 장비를 안 바꾸고 사용자 공간에서 돌린다.
- HTTP/3는 HTTP 의미를 바꾸지 않는다. HTTP/2의 다중화·흐름 제어가 QUIC로 내려갔고 HPACK이 QPACK이 됐다.
- 숫자: 스트림 ID 62비트·하위 2비트 4종류, 가변 길이 정수 1·2·4·8바이트, 암호화 수준 4가지, ALPN `h3`.

## 참고 자료

- [RFC 9000 — QUIC: A UDP-Based Multiplexed and Secure Transport (2021-05)](https://www.rfc-editor.org/rfc/rfc9000.html) — [§1 Overview](https://www.rfc-editor.org/rfc/rfc9000.html#section-1), [§2.1 Stream Types and Identifiers](https://www.rfc-editor.org/rfc/rfc9000.html#section-2.1), [§7 Cryptographic and Transport Handshake](https://www.rfc-editor.org/rfc/rfc9000.html#section-7), [§9 Connection Migration](https://www.rfc-editor.org/rfc/rfc9000.html#section-9), [§16 Variable-Length Integer Encoding](https://www.rfc-editor.org/rfc/rfc9000.html#section-16), 부록 A.1 Sample Variable-Length Integer Decoding (문서 맨 뒤, 예시 4개)
- [RFC 9001 — Using TLS to Secure QUIC (2021-05)](https://www.rfc-editor.org/rfc/rfc9001.html) — [§3 Protocol Overview](https://www.rfc-editor.org/rfc/rfc9001.html#section-3), [§4.1.3 Sending and Receiving Handshake Messages](https://www.rfc-editor.org/rfc/rfc9001.html#section-4.1.3), [§8.1 Protocol Negotiation](https://www.rfc-editor.org/rfc/rfc9001.html#section-8.1), [§9.2 Replay Attacks with 0-RTT](https://www.rfc-editor.org/rfc/rfc9001.html#section-9.2)
- [RFC 9002 — QUIC Loss Detection and Congestion Control (2021-05)](https://www.rfc-editor.org/rfc/rfc9002.html) — [§4 Relevant Differences Between QUIC and TCP](https://www.rfc-editor.org/rfc/rfc9002.html#section-4), [§7 Congestion Control](https://www.rfc-editor.org/rfc/rfc9002.html#section-7)
- [RFC 9114 — HTTP/3 (2022-06)](https://www.rfc-editor.org/rfc/rfc9114.html) — [§1 Introduction](https://www.rfc-editor.org/rfc/rfc9114.html#section-1), [§1.2 Delegation to QUIC](https://www.rfc-editor.org/rfc/rfc9114.html#section-1.2), [§3.1 Discovering an HTTP/3 Endpoint](https://www.rfc-editor.org/rfc/rfc9114.html#section-3.1), [§4.1 HTTP Message Framing](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.1), [§6.2 Unidirectional Streams](https://www.rfc-editor.org/rfc/rfc9114.html#section-6.2), [§7.2 Frame Definitions](https://www.rfc-editor.org/rfc/rfc9114.html#section-7.2)
- [RFC 9204 — QPACK: Field Compression for HTTP/3 (2022-06)](https://www.rfc-editor.org/rfc/rfc9204.html)
- [RFC 9113 — HTTP/2 (2022-06)](https://www.rfc-editor.org/rfc/rfc9113.html) — 비교표의 HTTP/2 프레임 목록
- [RFC 8446 — TLS 1.3 (2018-08) §2 Protocol Overview](https://www.rfc-editor.org/rfc/rfc8446.html#section-2) — 1-RTT 핸드셰이크, [§2.3 0-RTT Data](https://www.rfc-editor.org/rfc/rfc8446.html#section-2.3)
- [RFC 9293 — TCP (2022-08) §3.5 Establishing a Connection](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5) — 3-way 핸드셰이크
