---
title: "MCP 개정판 2026-07-28의 무상태 전환 — 핸드셰이크 제거, 요청별 버전·능력 선언, server/discover"
date: 2026-11-22
categories: [PE]
subcategory: emerging-tech
track: pe
tags: [정보관리기술사, emerging-tech, mcp, ai-agent, 개념정리]
description: "MCP 개정판 2026-07-28은 initialize 핸드셰이크와 Mcp-Session-Id 세션을 없애고, 요청마다 _meta에 프로토콜 버전과 클라이언트 능력을 싣게 했다. 서버가 먼저 보내던 정보 요청은 input_required 결과와 재요청(MRTR)으로 바뀌었다. 주요 변경 9가지, 요청별 _meta 4필드, 레거시 호환 3경우를 사양 근거로 정리했다."
difficulty: 심화
feature: mcp
environment: ["Model Context Protocol 사양 개정판 2026-07-28", "Model Context Protocol 사양 개정판 2025-11-25 (Lifecycle)"]
verification: manual-only
verified: true
topic_id: pe-292
---

> 실행 검증 없음 — 프로토콜 사양의 구조 변화를 다루는 개념 글이라 MCP 공식 사양 개정판 2026-07-28과
> 2025-11-25를 1차 자료로 썼다. 메시지 이름과 오류 코드는 사양 원문 그대로다.

## 들어가며

MCP는 AI 에이전트가 외부 도구·데이터에 붙는 표준으로 자리 잡아 기출에도 나오기 시작했다. 그런데 2026-07-28 개정판에서 연결을 맺는 방식 자체가 바뀌어, 교재에 실린 "initialize로 시작하는 3단계 수명주기"는 이제 레거시 설명이 됐다. 답안에 어느 개정판 기준인지 밝히지 않고 두 방식을 섞으면 틀린 설명이 된다. 실무에서는 사내 MCP 서버를 여러 인스턴스로 늘려 운영할 때, 그리고 이전 개정판 서버와 새 클라이언트가 섞일 때 이 변화가 바로 설계 문제로 나타난다.

## 정의

**MCP 무상태 전환**: MCP 개정판 2026-07-28에서 프로토콜 수준의 세션과 `initialize` 핸드셰이크를 없애고, **요청 하나에 처리에 필요한 정보를 모두 담게** 하며, 요청을 넘는 상태는 클라이언트가 매 요청에 넘기는 **명시적 식별자로만** 잇도록 바꾼 개정이다.

사양 기본 프로토콜의 무상태 절(Statelessness)은 서버가 같은 연결의 이전 요청에 기대어 문맥을 만들면 안 된다(MUST NOT)고 적고, stdio 프로세스도 대화나 세션이 아니라고 못 박는다. 연결은 메시지를 나르는 수단일 뿐이라는 뜻이다.

## 등장 배경

2025-11-25까지의 MCP는 **수명주기 3단계(초기화·운영·종료)** 를 거쳤다. 클라이언트가 `initialize`로 버전·능력·`clientInfo`를 보내면 서버가 합의한 버전·능력·`serverInfo`로 답하고, 클라이언트가 `notifications/initialized`를 보낸 뒤에야 본 요청이 오갔다. Streamable HTTP에서는 서버가 `Mcp-Session-Id`를 발급했고, 서버가 클라이언트에 먼저 보내는 요청(정보 요청·샘플링·루트 목록)은 별도의 GET SSE 스트림으로 흘렀다.

이 구조에서 서버는 세션마다 합의된 버전과 능력을 기억해야 한다. 그러면 같은 세션의 요청은 그 기억을 가진 서버 인스턴스로 다시 와야 하고, 인스턴스가 재시작되면 세션이 사라진다. 서버가 먼저 요청을 보내려면 클라이언트 쪽으로 열린 스트림을 계속 붙잡고 있어야 하며, 끊긴 스트림을 잇기 위한 재개 장치(`Last-Event-ID`)도 필요했다. 2026-07-28은 이 장치들을 걷어내고 각 요청을 독립된 단위로 만들었다.

## 구성요소 / 절차

### 주요 변경 9가지 (사양 변경 이력의 Major changes)

| 번호 | 변경 | 대체 수단 |
|---|---|---|
| ① | 프로토콜 수준 세션과 `Mcp-Session-Id` 제거 | 서버가 발급한 핸들을 일반 도구 인자로 넘긴다 |
| ② | `initialize`·`notifications/initialized` 핸드셰이크 제거 | 요청마다 `_meta`로 버전·능력 선언 |
| ③ | `server/discover` 추가, 서버는 구현 필수(MUST) | 지원 버전·능력 조회 |
| ④ | HTTP GET 엔드포인트와 `resources/subscribe`·`unsubscribe` 제거 | `subscriptions/listen` (POST 응답의 장기 SSE 스트림) |
| ⑤ | `ping`, `logging/setLevel`, `notifications/roots/list_changed` 제거 | 로그 수준은 `_meta`의 `logLevel` |
| ⑥ | 작업(tasks)을 확장으로 이동 | `io.modelcontextprotocol/tasks` 확장 |
| ⑦ | 서버가 먼저 보내던 요청 제거 | 다중 왕복 요청(MRTR) |
| ⑧ | 모든 결과에 `resultType` 필수 | `complete` / `input_required` |
| ⑨ | SSE 재개(`Last-Event-ID`) 제거 | 끊기면 진행 중 요청은 잃는다 |

### 요청별 `_meta` 4필드 (기본 프로토콜 절)

| 키 | 필수 여부 | 빠졌을 때 |
|---|---|---|
| `io.modelcontextprotocol/protocolVersion` | 필수 | `-32602` (HTTP 400) |
| `io.modelcontextprotocol/clientCapabilities` | 필수 | `-32602` (HTTP 400) |
| `io.modelcontextprotocol/clientInfo` | 권고(SHOULD) | — |
| `io.modelcontextprotocol/logLevel` | 선택 | — |

서버가 처리에 필요한 클라이언트 능력이 선언되지 않았으면 `-32021`(MissingRequiredClientCapability)로, 지원하지 않는 버전이면 `-32022`(UnsupportedProtocolVersion)로 거절한다. `-32022`의 `data`에는 `supported`(지원 버전 배열)와 `requested`가 들어가고, 클라이언트는 그중 하나로 다시 요청한다(버전 호환 절의 버전 협상 항목). 사양은 이 방식을 두고 협상용 핸드셰이크가 없다고 적는다. 요청이 하나씩 받아들여지거나 거절될 뿐이다.

Streamable HTTP에서는 같은 버전을 `MCP-Protocol-Version` 헤더에도 실어야 하고, `_meta` 값과 다르면 `-32020`(HeaderMismatch)이다. 같은 방식으로 `Mcp-Method` 헤더는 모든 요청에, `Mcp-Name` 헤더는 `tools/call`·`resources/read`·`prompts/get`에 붙인다. 본문의 값과 헤더의 값이 둘 다 있으므로, 둘이 어긋나지 않는지 서버가 확인한다.

### 다중 왕복 요청(MRTR) 3요소

서버가 처리 도중 사용자 확인이 필요하면 클라이언트에 요청을 따로 보내지 않고, **결과로 돌려준다.**

| 요소 | 누가 | 내용 |
|---|---|---|
| ① `inputRequests` | 서버 → 클라이언트 | 필요한 입력. 정보 요청·샘플링·루트 목록 요청 형식 |
| ② `requestState` | 서버 → 클라이언트 → 서버 | 서버가 이어서 처리하는 데 필요한 상태. 클라이언트는 그대로 되돌려준다 |
| ③ `inputResponses` | 클라이언트 → 서버 | ①에 대한 답. 원래 요청을 **새 JSON-RPC `id`로** 다시 보낼 때 싣는다 |

서버는 ①과 ② 중 적어도 하나를 넣어야 하고, `input_required`를 돌려줄 수 있는 메서드는 `tools/call`, `resources/read`, `prompts/get` 셋뿐이다. 서버가 기억하던 중간 상태가 ②로 옮겨 가서 클라이언트가 들고 다니는 것이 무상태 설계의 핵심이다.

## 도식

![MCP 레거시 세션 방식과 2026-07-28 무상태 방식의 메시지 흐름 비교](fig/mcp-legacy-vs-stateless.svg)

> **출처**: 레거시 흐름은 [MCP 사양 2025-11-25 — Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), 무상태 흐름은 [MCP 사양 2026-07-28 — Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)·[Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)·[Discovery](https://modelcontextprotocol.io/specification/latest/server/discover)

답안에는 양쪽의 ② 구간만 그려도 된다. 왼쪽은 서버가 먼저 요청을 보내는 빨간 화살표, 오른쪽은 결과(`input_required`)와 재요청으로 같은 일을 하는 초록 화살표 두 개다.

## 비교

### 레거시와 무상태

| 구분 | 레거시 (2025-11-25 이전) | 무상태 (2026-07-28) |
|---|---|---|
| 연결 수립 | `initialize` → 결과 → `notifications/initialized` | 없음. `server/discover`는 선택 |
| 버전 합의 | 세션 시작 때 한 번 | 요청마다 `_meta`와 HTTP 헤더로 선언 |
| 상태 보관 | 서버가 세션별로 | 클라이언트가 식별자·`requestState`로 |
| 서버발 요청 | `elicitation/create` 등 독립 요청 (GET SSE) | `input_required` 결과 + 재요청 |
| 구독 | `resources/subscribe` | `subscriptions/listen` |
| 끊김 복구 | `Last-Event-ID`로 재개 | 재개 없음. 진행 중 요청은 잃는다 |
| 미지원 버전 오류 | `-32602` | `-32022` |

### 레거시 호환 3경우 (버전 호환 절의 호환 행렬)

| 클라이언트 → 서버 | 결과 |
|---|---|
| 무상태 전용 → 레거시 | 실패 |
| 레거시 → 무상태 전용 | 실패 |
| 양쪽 지원(dual-era) → 레거시 | 성공. `initialize`로 되돌아간다 |

사양은 서버가 어느 시대(era)인지를 **요청이 아니라 서버의 속성**으로 보고, 클라이언트가 stdio 프로세스나 HTTP 출처 단위로 기억해 두도록 권고한다. stdio에서는 `server/discover`를 먼저 보내 무상태 오류가 아닌 오류가 오면 레거시로 판단하고, HTTP에서는 무상태 요청을 보내 `400` 응답 본문을 본 뒤 되돌아간다.

## 적용 시 고려사항

1. **`requestState`는 공격자가 고칠 수 있는 입력이다.** 클라이언트를 거쳐 돌아오므로 사양은 그 값이 인가나 업무 판단에 영향을 주면 무결성 보호를 해야 한다(MUST)고 적는다. 서버 서명(MAC)을 붙이거나, 상태는 서버 저장소에 두고 추측할 수 없는 식별자만 넘긴다.
2. **세션 기반 서버는 상태를 도구 인자로 옮긴다.** 장바구니·작업 문맥처럼 여러 호출에 걸친 상태를 세션에 두던 서버는, 변경 ①대로 서버가 발급한 핸들을 도구 인자로 받게 고쳐야 한다. 그러면 어느 인스턴스가 요청을 받아도 같은 저장소에서 상태를 찾으므로 고정 라우팅 없이 인스턴스를 늘릴 수 있다.
3. **끊김에 대비해 도구를 멱등하게 만든다.** 재개가 없어져 스트림이 끊기면 진행 중 요청은 잃고, 클라이언트는 같은 요청을 다시 보낼 수밖에 없다. 송금·이슈 등록처럼 부작용이 있는 도구는 같은 요청 식별자로 두 번 와도 한 번만 수행되게 만든다. 오래 걸리는 작업은 tasks 확장으로 넘긴다.
4. **혼재 기간에는 양쪽 지원 클라이언트를 둔다.** 호환 행렬대로 한쪽 전용끼리는 붙지 않는다. 사내에 이전 개정판 서버가 남아 있으면 클라이언트를 양쪽 지원으로 두고, 무상태 전용 서버는 `initialize` 요청에 지원 버전을 담아 오류로 답하게 해(사양 권고) 원인을 바로 알 수 있게 한다.
5. **폐지 예정 기능에 새로 기대지 않는다.** 루트·샘플링·로깅은 폐지 예정(Deprecated)이다. MRTR로 아직 실어 나를 수는 있지만 새 서버 설계의 전제로 삼지 않는다.

## 정리

- 정의 한 줄: **세션·핸드셰이크 제거, 요청마다 완결, 요청을 넘는 상태는 명시적 식별자로**
- 레거시 수명주기 **3단계**(초기화·운영·종료) → 무상태는 **단계 없음**
- 주요 변경 **9가지**: 세션·핸드셰이크·discover·구독·ping/로그·tasks·MRTR·resultType·재개
- 요청별 `_meta` **4필드**: 버전·능력(필수), clientInfo(권고), logLevel(선택)
- MRTR **3요소**: inputRequests → requestState → inputResponses(새 id로 재요청)
- 오류 코드 **3개**: `-32020` 헤더 불일치, `-32021` 능력 누락, `-32022` 미지원 버전
- 암기 단서: **"묻지 말고 돌려줘라"** — 서버가 먼저 묻던 것을 결과로 돌려준다

> 기출 답안: [기출문제 — MCP(Model Context Protocol)](../../exam/2026-11-21-model-context-protocol-mcp/index.md)
>
> 관련 개념: [MCP 인가 구조 — OAuth 2.1, 보호 자원 메타데이터, 자원 지시자와 토큰 대상 검증](../../security/2026-11-11-mcp-authorization-oauth-resource-audience/index.md)

## 참고 자료

- [MCP 사양 2026-07-28 — Changelog](https://modelcontextprotocol.io/specification/latest/changelog) — 주요 변경 9가지, 부수 변경(`-32004`에서 `-32022`로 재번호), 폐지 예정 목록
- [MCP 사양 2026-07-28 — Base Protocol](https://modelcontextprotocol.io/specification/latest/basic) — 무상태 원칙, 요청별 `_meta` 필드, `resultType`, 오류 코드 표
- [MCP 사양 2026-07-28 — Versioning and Compatibility](https://modelcontextprotocol.io/specification/latest/basic/lifecycle) — 요청별 버전 선언, `-32022`와 `supported`·`requested`, 레거시 판별과 호환 행렬
- [MCP 사양 2026-07-28 — Discovery](https://modelcontextprotocol.io/specification/latest/server/discover) — `server/discover` 구현 의무와 응답 필드
- [MCP 사양 2026-07-28 — Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) — `MCP-Protocol-Version` 헤더, 세션·GET 스트림·재개 제거, 서버발 독립 요청 금지
- [MCP 사양 2026-07-28 — Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr) — `inputRequests`·`requestState`·`inputResponses`, 허용 메서드 3개, `requestState` 무결성
- [MCP 사양 2025-11-25 — Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) — 수명주기 3단계, `initialize` 요청·응답 필드, `notifications/initialized`
