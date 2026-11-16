---
title: "BPF와 eBPF — 소켓 필터에서 커널 안 범용 실행 환경으로"
date: 2026-11-17
categories: [PE]
subcategory: system
track: pe
tags: [정보관리기술사, system, 개념정리]
description: "패킷을 커널 안에서 먼저 거르려고 만든 classic BPF의 구조(레지스터 2개, 64비트 명령)와, 이를 레지스터 10개·64비트로 넓혀 검증기·JIT·맵·헬퍼를 갖춘 커널 안 실행 환경이 된 eBPF를 원 논문·RFC 9669·리눅스 커널 문서로 정리하고, 관측·보안 도구와 BPFDoor 같은 악용을 대비했다."
difficulty: 중급
environment: ["Linux kernel 문서 (docs.kernel.org, 7.4.0-rc3)", "RFC 9669 BPF Instruction Set Architecture (2024-10)", "bpf(2) man-pages 6.19 (2026-02-10)"]
verification: manual-only
verified: true
topic_id: pe-277
---

## 들어가며

BPFDoor 기출문제는 "포트를 열지 않는 백도어"를 물었지만, 답안의 설득력은 그 밑에 깔린 BPF를 설명할 수 있느냐에서 나온다. BPF는 `tcpdump`가 캡처 조건을 커널에 내려보내는 장치로 시작했고, 지금은 리눅스 커널 안에서 검증된 프로그램을 실행하는 범용 환경(eBPF)으로 넓어졌다. 관측·네트워크·보안 도구가 이 위에서 만들어지는 동시에, 같은 기능이 공격자의 은닉 수단도 된다. 시험에서는 classic BPF와 eBPF의 차이, eBPF의 구성요소, 그리고 안전성을 보장하는 검증기를 묻는 형태로 나온다.

> **실행 검증 없음.** 이 환경은 Windows라 BPF 프로그램을 적재할 수 없다. McCanne·Jacobson 원 논문(1993), IETF RFC 9669, 리눅스 커널 문서, bpf(2) 매뉴얼, eBPF 재단 소개 문서만 근거로 정리했다. 버전마다 달라지는 명령 수 한도는 문서마다 값이 달라 쓰지 않았다.

## 정의

**classic BPF(cBPF)는 사용자 프로그램이 지정한 조건으로 커널이 패킷을 먼저 걸러, 원하지 않는 패킷이 사용자 공간으로 복사되기 전에 버리게 하는 레지스터 기반 패킷 필터다** (McCanne·Jacobson, 1993).

**eBPF는 운영체제 커널 같은 특권 영역에서 샌드박스된 프로그램을 실행하는 기술로, 적재 전에 검증기가 안전성을 확인하고 JIT 컴파일러가 기계어로 바꿔 커널의 훅에서 실행한다** (ebpf.io, 커널 문서).

지금 커널 문서는 둘을 구분할 때 classic BPF와 eBPF(또는 그냥 BPF)라고 부른다. 명령어 체계는 2024년 10월 **RFC 9669(BPF Instruction Set Architecture, 표준화 트랙)** 로 IETF 문서가 됐다.

## 등장 배경

**① classic BPF가 풀려던 문제.** 네트워크 모니터는 사용자 프로세스라서 패킷을 커널에서 사용자 공간으로 복사해야 한다. 원 논문은 이 복사를 줄이려면 커널 안의 패킷 필터가 불필요한 패킷을 가능한 한 일찍 버려야 한다고 본다. 그 전의 필터(CSPF)는 스택 기반 평가기라 당시 RISC CPU에서 비효율적이었고, BPF는 레지스터 기반 평가기로 바꿔 원래 설계보다 최대 20배 빨랐다고 보고했다.

**② eBPF로 넓어진 이유.** classic BPF는 32비트 레지스터 2개(A, X)에 패킷 필터라는 한 용도만 가졌다. 커널 문서는 eBPF가 레지스터를 10개로, 폭을 64비트로 늘리고, **실제 CPU 레지스터에 일대일로 대응해 JIT 컴파일되도록** 설계됐다고 설명한다. 이렇게 넓히자 패킷뿐 아니라 시스템 콜, 함수 진입·종료, 트레이스포인트에 프로그램을 걸 수 있게 됐다. 커널은 지금 classic BPF 프로그램도 내부에서 eBPF로 변환해 실행한다(커널 문서 filter.html).

## 구성요소

**① classic BPF 머신 — 3가지 저장소와 64비트 명령** (커널 문서 filter.html)

| 요소 | 내용 |
|---|---|
| A | 32비트 누산기 |
| X | 32비트 보조 레지스터 |
| M[0~15] | 32비트 칸 16개의 임시 메모리 |
| 명령 형식 | `code`(16비트) + `jt`(8) + `jf`(8) + `k`(32) = 64비트. 비교 결과에 따라 `jt`·`jf`만큼 앞으로 건너뛴다 |

사용자 프로그램은 이 명령 배열을 `setsockopt(…, SO_ATTACH_FILTER, …)`로 소켓에 붙인다. BPFDoor가 쓰는 것이 바로 이 경로다(MITRE ATT&CK T1205.002).

**② eBPF 실행 환경 — 구성요소 6가지** (ebpf.io, 커널 문서)

| 구성요소 | 역할 |
|---|---|
| 훅 (Hook) | 프로그램이 실행될 지점. 시스템 콜, 함수 진입·종료, 커널 트레이스포인트, 네트워크 이벤트. 없으면 kprobe·uprobe로 임의 함수에 건다 |
| 로더 | 사용자 공간에서 `bpf()` 시스템 콜로 바이트코드를 커널에 적재 |
| 검증기 (Verifier) | 적재 전에 안전성을 정적으로 확인 |
| JIT 컴파일러 | 범용 바이트코드를 그 CPU의 기계어로 번역 |
| 맵 (Map) | 커널과 사용자 공간이 데이터를 나누는 범용 저장소. 해시·배열 등 여러 형식 |
| 헬퍼 함수 | 프로그램은 임의의 커널 함수를 부를 수 없고, 허용된 헬퍼만 호출한다 |

**③ eBPF 레지스터 — 11개** (커널 문서 classic_vs_extended, RFC 9669)

| 레지스터 | 용도 |
|---|---|
| R0 | 함수 반환값 |
| R1~R5 | 함수 인자 (인자는 최대 5개) |
| R6~R9 | 호출 뒤에도 값이 보존되는 레지스터 |
| R10 | 읽기 전용 프레임 포인터 |

명령은 기본 64비트, 64비트 상수를 담는 넓은 형식은 128비트다(RFC 9669).

**④ 검증기의 2단계** (커널 문서 verifier.html)

1. **제어 흐름 검사** — 깊이 우선 탐색으로 루프와 도달할 수 없는 명령을 찾아 거부한다
2. **경로 모의 실행** — 첫 명령부터 가능한 모든 경로를 따라가며 레지스터·스택의 상태를 추적한다. 초기화하지 않은 레지스터 읽기, 쓰기 전 스택 읽기, 범위를 벗어난 메모리 접근이 나오면 거부한다

루프에 대해서는 문서마다 갱신 시점이 달라 서술이 다르다. 커널 검증기 문서는 1단계에서 루프를 거부한다고 적고, ebpf.io는 검증기가 종료 조건을 확인할 수 있는 **유한 루프**는 받아들인다고 적는다. 답안에는 "종료가 증명되지 않는 프로그램은 적재되지 않는다"로 쓰면 두 서술을 모두 만족한다.

## 도식

![사용자 공간의 로더가 bpf()로 적재한 프로그램이 검증기, JIT 컴파일러를 거쳐 훅에 부착되고, 맵을 통해 사용자 공간 도구와 결과를 공유하는 흐름](fig/ebpf-lifecycle.svg)

> **출처**: [ebpf.io — What is eBPF? (Loader & Verification Architecture, Maps, Helper Calls)](https://ebpf.io/what-is-ebpf/), [Linux kernel docs — eBPF verifier](https://docs.kernel.org/bpf/verifier.html), [Linux kernel docs — BPF maps](https://docs.kernel.org/bpf/maps.html)

답안지에는 "사용자 공간 / 커널" 두 영역, 커널 안의 검증기 → JIT → 훅 세 박스와 맵 하나만 그려도 된다.

## 비교

**classic BPF와 eBPF**

| 구분 | classic BPF | eBPF |
|---|---|---|
| 출발 | 1993 BSD 패킷 필터 | 리눅스 커널의 확장 |
| 레지스터 | A·X 2개, 32비트 | R0~R9 10개 + R10 프레임 포인터, 64비트 |
| 용도 | 소켓·패킷 필터 | 네트워크·추적·보안 등 범용 |
| 붙는 곳 | 소켓 | 시스템 콜·함수·트레이스포인트·네트워크 이벤트 |
| 상태 저장 | 없음 (임시 메모리만) | 맵으로 실행 사이·사용자 공간과 공유 |
| 외부 호출 | 없음 | 헬퍼 함수 |
| 실행 | 지금 커널은 eBPF로 변환해 인터프리터나 JIT로 실행 | 검증 뒤 JIT 컴파일 |

**eBPF와 커널 모듈** — 커널 기능을 넓히는 두 방법이다.

| 구분 | 커널 모듈 | eBPF |
|---|---|---|
| 적재 전 검사 | 없음. 임의 코드가 커널 권한으로 실행 | 검증기가 종료·메모리 안전성 확인 |
| 커널 함수 접근 | 내보낸 함수 전부 | 허용된 헬퍼만 |
| 잘못됐을 때 | 커널 전체가 멈출 수 있다 | 적재 단계에서 거부된다 |

## 적용 시 고려사항

1. **누가 적재할 수 있는지를 정한다.** 리눅스 4.4 전에는 모든 `bpf()` 명령에 `CAP_SYS_ADMIN`이 필요했고, 4.4부터 일반 사용자도 소켓 필터 형식의 제한된 프로그램을 만들 수 있게 됐다(bpf(2)). 커널 매개변수 `kernel.unprivileged_bpf_disabled`로 이를 막는다. 1은 다시 켤 수 없게 끄고, 2는 관리자가 나중에 다시 켤 수 있게 끈다(커널 sysctl 문서).
2. **좋은 기능이 그대로 은닉 수단이 된다.** BPFDoor는 패킷 소켓에 classic BPF 필터를 붙여 특정 패킷만 받는다. 열린 포트가 없어 포트 점검에 드러나지 않는다(MITRE T1205.002). 점검은 포트 목록이 아니라 **소켓에 붙은 필터**를 봐야 하며, `ss`의 `-b`(BPF 필터 표시)와 `-0`(패킷 소켓) 옵션이 그 수단이다(ss(8)). 패킷 소켓은 root나 `CAP_NET_RAW`가 있어야 열리므로 권한 관리가 첫 방어선이다.
3. **커널 버전이 기능을 정한다.** 프로그램 형식마다 들어온 커널 버전이 다르다. 소켓 필터는 3.19, kprobe와 트래픽 분류(`SCHED_CLS`)는 4.1부터다(bpf(2)). 운영 서버 커널에서 쓰려는 훅이 지원되는지 먼저 확인한다.
4. **검증기의 제약이 설계를 제한한다.** 인자는 5개까지이고, 종료가 증명되지 않는 반복은 적재되지 않는다. 복잡한 로직은 커널 쪽 프로그램을 작게 두고 맵으로 데이터를 넘겨 사용자 공간에서 처리하는 구조가 된다.

## 정리

- **classic BPF**: 커널에서 패킷을 먼저 거르는 레지스터 기반 필터. A·X·M[16], 64비트 명령, `SO_ATTACH_FILTER`
- **eBPF 구성 6가지 "훅·로더·검증기·JIT·맵·헬퍼"**, 수명 4단계 **적재 → 검증 → JIT → 부착**
- **레지스터 11개**: R0 반환, R1~R5 인자, R6~R9 보존, R10 프레임 포인터. 명령 64/128비트 (RFC 9669)
- **검증기 2단계**: 제어 흐름 검사 → 경로 모의 실행
- 같은 기술이 관측·보안 도구의 기반이자 BPFDoor 같은 은닉 백도어의 수단이다

> 기출 답안: [기출문제 — BPFDoor 악성코드: 개념과 기존 백도어와의 차이, 위협과 영향, 기술적·관리적 대응](../../exam/2026-11-16-bpfdoor-concept-threats-countermeasures/index.md)

## 참고 자료

- [McCanne, Jacobson — The BSD Packet Filter: A New Architecture for User-level Packet Capture, USENIX Winter 1993](https://www.tcpdump.org/papers/bpf-usenix93.pdf) — 초록·서론: 커널 필터의 목적, CSPF 대비 레지스터 기반 평가기
- [RFC 9669 — BPF Instruction Set Architecture (ISA), D. Thaler 편, 2024-10, Proposed Standard](https://www.rfc-editor.org/rfc/rfc9669) — 3.1·3.2절 명령 인코딩, 레지스터 번호
- Linux kernel 문서 (7.4.0-rc3)
  - [Linux Socket Filtering aka Berkeley Packet Filter (BPF)](https://docs.kernel.org/networking/filter.html) — classic BPF 레지스터·명령 형식, `SO_ATTACH_FILTER`, eBPF 변환
  - [Classic BPF vs eBPF](https://docs.kernel.org/bpf/classic_vs_extended.html) — 레지스터 확장, 호출 규약, JIT 대응
  - [eBPF verifier](https://docs.kernel.org/bpf/verifier.html) — 2단계 검사, 레지스터 상태 추적
  - [BPF maps](https://docs.kernel.org/bpf/maps.html) — 맵 정의
  - [Documentation for /proc/sys/kernel/ — unprivileged_bpf_disabled](https://docs.kernel.org/admin-guide/sysctl/kernel.html) — 비특권 적재 차단
- [bpf(2) — Linux manual page (man-pages 6.19, 2026-02-10)](https://man7.org/linux/man-pages/man2/bpf.2.html) — 프로그램 형식별 도입 버전, 권한 요건
- [ss(8) — Linux manual page](https://man7.org/linux/man-pages/man8/ss.8.html) — `-0`·`-b` 옵션
- [ebpf.io — What is eBPF?](https://ebpf.io/what-is-ebpf/) — 정의, 훅·로더·검증·JIT·맵·헬퍼, 유한 루프 (eBPF 재단 운영)
- [MITRE ATT&CK — T1205.002 Traffic Signaling: Socket Filters](https://attack.mitre.org/techniques/T1205/002/) — 소켓 필터 악용
