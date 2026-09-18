# 언어별 식별자 명명 규칙

예제 코드를 쓰기 전 이 문서를 확인한다. 출처는 각 언어의 **공식 스타일 가이드**다.

## 공통 원칙 (길이)

| 스코프 | 권장 길이 | 예 |
|---|---|---|
| 1~3줄 루프 인덱스 | 1~2자 | `i`, `k`, `ok` |
| 함수 지역 변수 | 4~15자 | `row_count`, `retryDelay` |
| 함수/메서드 이름 | 8~25자 | `resolve_index_plan` |
| 모듈/패키지 공개 상수 | 10~30자 | `DEFAULT_POOL_TIMEOUT_MS` |

> **Go의 예외**: Go는 "스코프가 좁을수록 이름이 짧아야 한다"를 명시적으로 요구한다.
> 다른 언어에서 `index`로 쓸 것을 Go에서는 `i`로 쓰는 것이 관용이다.

축약은 **널리 통용되는 것만** 쓴다: `id`, `url`, `db`, `ctx`, `cfg`, `req`, `res`, `tx`, `idx`, `ms`.
`usr`, `mgr`, `calc`, `val` 같은 자의적 축약은 쓰지 않는다.

---

## Python — PEP 8

| 대상 | 규칙 | 예 |
|---|---|---|
| 변수·함수·인자 | `snake_case` | `connection_pool`, `fetch_plan()` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_POOL_SIZE` |
| 클래스 | `PascalCase` | `QueryPlanner` |
| 모듈·패키지 | 짧은 `lowercase` | `planner`, `dbutil` |
| 내부 전용 | 앞 `_` 1개 | `_build_index()` |
| 예약어 충돌 | 뒤 `_` 1개 | `class_`, `id_` |

- 한 글자 중 `l`, `O`, `I`는 금지(1/0과 혼동).
- 줄 길이 79자 권장이나 실무에서는 88자(Black 기본)를 쓴다. 이 블로그는 **88자**를 기준으로 한다.

## Java — Google Java Style

| 대상 | 규칙 | 예 |
|---|---|---|
| 변수·메서드 | `lowerCamelCase` | `maxPoolSize`, `acquireConnection()` |
| 상수 (`static final` 불변) | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_MS` |
| 클래스·인터페이스 | `UpperCamelCase` | `ConnectionPool` |
| 패키지 | 구분자 없는 `lowercase` | `com.example.dbpool` |
| 타입 파라미터 | 단일 대문자 또는 `T` 접미 | `T`, `RowT` |

- 약어도 카멜케이스로 처리한다: `HTTPServer`(X) → `HttpServer`(O), `userID`(X) → `userId`(O).
- 인터페이스에 `I` 접두사를 붙이지 않는다(`IUserService` 금지).

## JavaScript / TypeScript

| 대상 | 규칙 | 예 |
|---|---|---|
| 변수·함수 | `camelCase` | `retryDelayMs` |
| 클래스·타입·인터페이스 | `PascalCase` | `PoolOptions` |
| 상수(진짜 불변) | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| 파일명 | `kebab-case.ts` | `connection-pool.ts` |
| private 필드 | `#` 접두 (또는 `_`) | `#activeCount` |

- 불리언은 `is`/`has`/`should` 접두: `isStale`, `hasPendingWrite`.
- TS에서 타입에 `T` 접두사를 붙이지 않는다(`TUser` 금지).

## Go — Effective Go

| 대상 | 규칙 | 예 |
|---|---|---|
| 공개 | `MixedCaps` 대문자 시작 | `MaxIdleConns` |
| 비공개 | `mixedCaps` 소문자 시작 | `idleCount` |
| 패키지 | 짧은 단수형 `lowercase` | `pool`, `sqlx` |
| 인터페이스(메서드 1개) | 동사 + `er` | `Reader`, `Closer` |
| 에러 변수 | `Err` 접두 | `ErrPoolClosed` |

- 언더스코어를 쓰지 않는다. `max_conns`(X) → `maxConns`(O).
- 이름에 패키지명을 반복하지 않는다: `pool.PoolNew()`(X) → `pool.New()`(O).
- 약어는 대소문자를 통일한다: `userID`, `httpClient`, `parseURL`.
- **관용 짧은 이름**: `i`(인덱스), `n`(개수), `b`(버퍼/바이트), `r`/`w`(Reader/Writer), `ctx`, `err`.

## Rust — RFC 430

| 대상 | 규칙 | 예 |
|---|---|---|
| 변수·함수·모듈 | `snake_case` | `acquire_conn()` |
| 타입·트레이트·enum 배리언트 | `PascalCase` | `PoolError`, `State::Idle` |
| 상수·static | `SCREAMING_SNAKE_CASE` | `MAX_IDLE` |
| 라이프타임 | 짧은 소문자 | `'a`, `'src` |
| 크레이트 | `snake_case` | `conn_pool` |

- 의도적으로 안 쓰는 변수는 `_` 접두: `_unused`.
- 변환 메서드 접두사 규칙: `as_`(무비용 참조), `to_`(비용 있는 복제), `into_`(소유권 이동).

## C# — Microsoft 가이드라인

| 대상 | 규칙 | 예 |
|---|---|---|
| public 멤버·메서드·프로퍼티·클래스 | `PascalCase` | `MaxPoolSize` |
| 지역 변수·매개변수 | `camelCase` | `retryCount` |
| private 필드 | `_camelCase` | `_activeCount` |
| 인터페이스 | `I` + `PascalCase` | `IConnectionPool` |
| 비동기 메서드 | `Async` 접미 | `AcquireAsync()` |

## SQL

| 대상 | 규칙 | 예 |
|---|---|---|
| 키워드 | `UPPERCASE` | `SELECT`, `LEFT JOIN` |
| 테이블·컬럼 | `snake_case` 소문자 | `order_item`, `created_at` |
| 테이블명 | 단수형 권장 | `order_item` (not `order_items`) |
| PK | `id` 또는 `<테이블>_id` | `order_id` |
| FK | `<참조테이블>_id` | `customer_id` |
| 인덱스 | `ix_<테이블>_<컬럼들>` | `ix_order_customer_id_created_at` |
| 유니크 인덱스 | `ux_...` | `ux_customer_email` |

- 예약어를 식별자로 쓰지 않는다(`order`, `user`, `size`, `level`).
- 불리언 컬럼은 `is_`/`has_` 접두: `is_deleted`.

## Shell (bash)

| 대상 | 규칙 | 예 |
|---|---|---|
| 지역 변수 | `lower_snake_case` + `local` | `local retry_count` |
| 환경변수·전역 | `UPPER_SNAKE_CASE` | `DB_HOME` |
| 함수 | `lower_snake_case` | `wait_for_port()` |

- 변수 참조는 항상 `"${var}"`로 중괄호와 큰따옴표를 함께 쓴다.

---

## 출처

- Python: [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- Java: [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- Go: [Effective Go — Names](https://go.dev/doc/effective_go#names), [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- Rust: [RFC 430 — Naming Conventions](https://rust-lang.github.io/rfcs/0430-finalizing-naming-conventions.html)
- C#: [Microsoft — Coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- TypeScript: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
