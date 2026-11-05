---
title: "HTTP 조건부 요청 — ETag 와 Last-Modified 로 304 를 받는 조건"
date: 2026-11-05
categories: [Backend]
subcategory: http
track: general
tags: [http, etag, cache, conditional-request]
description: "If-None-Match, If-Match, If-Modified-Since 가 서버에서 어떤 순서와 비교 방식으로 평가되는지 RFC 9110 규칙을 구현해 200·304·412 가 갈리는 지점을 표로 확인한다. 약한 ETag 와 강한 ETag 가 두 헤더에서 다르게 비교되는 자리가 핵심이다."
difficulty: 중급
environment: ["Python 3.13.5", "RFC 9110 (2022)"]
verification: executed
verified: true
topic_id: gen-019
---

## 들어가며

API 서버의 응답 본문이 수백 KB 인데 대부분의 요청에서 내용이 바뀌지 않는다.
클라이언트는 매번 같은 본문을 통째로 받고, 서버는 매번 직렬화하고, 사이의 회선은
매번 같은 바이트를 나른다. 초당 요청이 천 건이면 같은 본문을 하루 8,600만 번
보내는 셈이다. `Cache-Control: max-age` 를 길게 잡으면 요청 자체가 사라지지만
바뀌었을 때 반영이 늦어진다. 그 사이에 있는 수단이 **조건부 요청**이다. 클라이언트가
"내가 가진 것이 아직 유효하면 본문 없이 답해 달라"고 물으면 서버가 304 로 답한다.

## 개념

조건부 요청은 요청에 **조건 헤더**를 실어 보내는 방식이다. 서버는 현재 표현(representation)의
검증자(validator)와 조건을 비교해 응답을 정한다. 검증자는 두 가지다.

- `ETag`: 표현을 가리키는 불투명한 따옴표 문자열. 앞에 `W/` 가 붙으면 약한 태그다
- `Last-Modified`: 표현이 마지막으로 바뀐 시각

조건 헤더는 이 글에서 다루는 세 개다.

| 헤더 | 참이 되는 때 | 거짓이면 (GET) |
|---|---|---|
| `If-None-Match` | 보낸 태그 중 현재 태그와 **일치하는 것이 없다** | 304 |
| `If-Match` | 보낸 태그 중 현재 태그와 일치하는 것이 있다 | 412 |
| `If-Modified-Since` | 수정 시각이 보낸 날짜보다 **뒤**다 | 304 |

304 는 읽기 캐시 검증에, 412 는 "내가 본 버전이 맞을 때만 처리하라"는 쓰기 보호에 쓴다.

## 구조

![조건 헤더가 평가되는 순서](fig/conditional-evaluation-order.svg)

> **출처**: [RFC 9110 §13.2.2 Precondition Handling](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.2.2)

도식은 GET 요청에서의 순서만 그렸다. 규격에는 `If-Unmodified-Since` 와 `If-Range` 도 평가
순서에 들어 있으나 이 글은 다루지 않는다.

## 동작 원리

비교 방식이 헤더마다 다르다. 이 부분이 가장 자주 틀린다. 태그 비교(RFC 9110 §8.8.3.2)는
두 가지다. 강한 비교는 두 태그가 모두 약하지 않고 문자열이 같아야 일치다. 약한 비교는
`W/` 접두사를 무시하고 따옴표 안의 문자열만 본다.

- `If-None-Match` 는 **약한 비교**를 쓴다 (§13.1.2)
- `If-Match` 는 **강한 비교**를 쓴다 (§13.1.1)

그래서 캐시 검증(`If-None-Match`)은 약한 태그로도 304 가 나오지만, 쓰기 보호(`If-Match`)는
약한 태그면 같은 문자열이어도 일치하지 않는다. 바이트가 같다는 보장이 없는 표현을
근거로 덮어쓰기를 허용하지 않으려는 규칙이다.

또 `If-Modified-Since` 는 `If-None-Match` 가 있으면 무시된다(§13.1.3). 두 헤더를 같이 보내도
태그가 먼저 결정하고 날짜는 보지 않는다.

## 실습 예제

`http.server` 는 조건부 요청을 처리해 주지 않는다. 위 규칙을 핸들러에 직접 구현하고
`http.client` 로 헤더를 바꿔 가며 요청했다. 따라서 아래 표는 **RFC 규칙을 구현한
서버가 어떻게 답하는지**를 보인 것이고, 특정 웹 서버나 프록시의 동작을 측정한 것은
아니다. 전체 소스는 [`code/`](code/)에 있고, 수치는 `code/output.txt` 에서 가져왔다.
서버의 태그는 `"v1-abc"`, `Last-Modified` 는 `Thu, 01 Jan 2026 00:00:00 GMT` 이다.

**강한 ETag 일 때**

| 요청 헤더 | 상태 | 본문 |
|---|---|---|
| (조건 헤더 없음) | 200 | 26B |
| `If-None-Match`: 같은 강한 태그 | 304 | 0B |
| `If-None-Match`: 같은 값의 약한 태그 | 304 | 0B |
| `If-None-Match`: 다른 태그 | 200 | 26B |
| `If-None-Match`: 여러 개 중 하나가 일치 | 304 | 0B |
| `If-None-Match: *` | 304 | 0B |
| `If-Match`: 같은 강한 태그 | 200 | 26B |
| `If-Match`: 다른 태그 | 412 | 0B |
| `If-Match`: 같은 값의 약한 태그 | 412 | 0B |

**서버의 ETag 가 약할 때(`W/"v1-abc"`)**

| 요청 헤더 | 상태 |
|---|---|
| `If-None-Match`: 같은 약한 태그 | 304 |
| `If-None-Match`: 같은 값의 강한 태그 | 304 |
| `If-Match`: 같은 약한 태그 | 412 |
| `If-Match`: 같은 값의 강한 태그 | 412 |

예상과 같았던 것은 `If-None-Match` 가 약·강을 가리지 않고 304 를 낸다는 점이다.
눈에 띄는 것은 서버 태그가 약하면 `If-Match` 가 **자기 자신의 태그를 그대로 보내도**
412 라는 점이다. 약한 태그를 발급하는 서버에서는 `If-Match` 로 쓰기 보호를 할 수 없다.

**날짜 헤더와 우선순위**

| 요청 헤더 | 상태 |
|---|---|
| `If-Modified-Since`: 수정 시각과 같음 | 304 |
| `If-Modified-Since`: 수정 시각보다 1시간 이전 | 200 |
| `If-Modified-Since`: 수정 시각보다 1시간 이후 | 304 |
| `If-Modified-Since` 이후 + `If-None-Match` 다름 | 200 |
| `If-Modified-Since` 이전 + `If-None-Match` 같음 | 304 |

네 번째 줄이 우선순위를 보여 준다. 날짜만 보면 304 인데 태그가 다르므로 200 이 나왔다.
다섯 번째는 반대로 날짜만 보면 200 인데 태그가 같아 304 가 나왔다.

## 실무에서 주의할 점

1. **`Last-Modified` 만으로는 같은 시각에 두 번 바뀐 것을 구분하지 못한다.** 날짜는
   초 단위 문자열이라, 한 초 안에 표현이 두 번 바뀌면 어느 쪽도 같은 날짜를 갖는다.
   RFC 는 이런 경우를 위해 날짜 검증자를 기본적으로 약한 것으로 취급한다(§8.8.2.2).
2. **304 에도 검증자 헤더를 실어 보낸다.** 이 예제는 304 에 `ETag` 를 넣었다. 캐시가
   저장된 응답의 메타데이터를 갱신할 때 쓴다.
3. **약한 태그로 쓰기 보호를 하려고 하지 않는다.** `If-Match` 는 강한 비교라 약한
   태그와 일치하지 않는다. 낙관적 잠금이 목적이면 강한 태그를 발급한다.
4. **`If-None-Match: *` 는 다른 의미다.** 읽기에서는 "표현이 존재하면" 304 를 내고,
   쓰기에서는 "이미 있으면 거부" 용도로 쓴다(§13.1.2). 같은 헤더가 메서드에 따라
   다른 일을 한다.
5. **이 글의 서버는 규칙만 구현했다.** 실제 프록시나 CDN 이 압축 등으로 태그를
   바꾸는 동작은 확인하지 않았다.

## 정리

- 조건부 요청은 검증자(`ETag`, `Last-Modified`)와 조건 헤더를 비교해 304 · 412 를 가른다
- `If-None-Match` 는 약한 비교, `If-Match` 는 강한 비교를 쓴다
- 약한 태그는 `If-None-Match` 로 304 를 받을 수 있지만 `If-Match` 로는 항상 412 다
- `If-None-Match` 가 있으면 `If-Modified-Since` 는 무시된다
- 평가 순서는 `If-Match`, `If-None-Match`, `If-Modified-Since` 이다

## 참고 자료

- [RFC 9110 HTTP Semantics §13 Conditional Requests](https://www.rfc-editor.org/rfc/rfc9110.html#section-13)
- [RFC 9110 §8.8.3.2 ETag Comparison](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8.3.2)
- [RFC 9110 §8.8.2.2 Last-Modified Comparison](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8.2.2)
