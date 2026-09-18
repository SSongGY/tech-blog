---
title: "Tibero 7 시퀀스 — 생성, 캐시, 그리고 값이 튀는 순간"
date: 2026-09-18
categories: [Database]
subcategory: tibero
track: product
tags: [tibero, sequence, sql]
description: "Tibero 7 시퀀스의 속성과 기본값, 번호가 건너뛰는 세 경로(비정상 종료·ALTER SEQUENCE·클러스터 NOORDER), 그리고 구성요소 표에 없는 제약을 에러 코드(7340 캐시<사이클 등)로 정리했다. 컬럼 DEFAULT에 NEXTVAL을 쓸 수 있는지는 매뉴얼 두 페이지가 반대로 적는다."
difficulty: beginner
product: Tibero
product_version: "7"
feature: sequence
environment: ["Tibero 7.2.6"]
verification: manual-only
verified: true
topic_id: tb-001
---

> **실행 검증 없음.** 이 글은 Tibero 7.2.6 공개 매뉴얼을 근거로 문법과 동작을 정리한
> 것이다. 작성 환경에 `tbsql`이 없어 예제를 실행하지 않았으므로 **출력이나 측정값은
> 싣지 않는다.** 근거를 찾지 못한 동작은 쓰지 않고, 매뉴얼이 명시하지 않은 항목은
> 그렇다고 밝혔다.

## 들어가며

전표 번호에 쓸 순번이 필요해 시퀀스를 하나 만든다. 잘 돌아간다. 그러다 어느 날
운영에서 문의가 온다. 번호가 1041에서 1140으로 건너뛰었으니 누락된 99개를 확인해
달라는 것이다.

이때 대개 애플리케이션 코드에서 번호를 버리는 지점을 찾는다. 그런데 시퀀스는 **번호가
비는 것을 막아 주는 객체가 아니다.** 어디서 비는지는 코드가 아니라 시퀀스 속성과
인스턴스 상태에 적혀 있다. 이 글은 속성을 기본값까지 정리하고, 번호가 건너뛰는 경로와
DDL이 막히는 제약을 매뉴얼에 적힌 것만 골라 묶는다.

## 개념

시퀀스는 유일한 연속 값을 만드는 스키마 객체다. 주로 기본 키를 채울 때 쓰고, 값은
두 의사 컬럼으로 꺼낸다.

| 의사 컬럼 | 동작 |
|---|---|
| `NEXTVAL` | 시퀀스 값을 증가시키고 증가된 값을 반환 |
| `CURRVAL` | 현재 세션에서 마지막으로 조회한 `NEXTVAL` 값을 반환 |

`CURRVAL`을 쓰려면 같은 세션에서 `NEXTVAL`을 먼저 호출해야 한다. 이름은 최대 30자이고
**테이블과 같은 네임스페이스를 쓴다.** 같은 스키마의 테이블·동의어·PSM 객체와 겹치면
생성되지 않는다.

의사 컬럼은 쓸 수 있는 자리가 정해져 있다.

- 쓸 수 있는 곳: `SELECT` 리스트, `INSERT`의 `VALUES` 절, `INSERT`의 부질의 `SELECT`
  리스트, `UPDATE`의 `SET` 절
- 쓸 수 없는 곳: 부질의 내부, 뷰 내부, `DISTINCT`가 있는 `SELECT`, `GROUP BY`나
  `ORDER BY`가 있는 `SELECT`, 집합 연산자로 연결된 `SELECT`, `WHERE` 절,
  `CREATE TABLE`/`ALTER TABLE`의 `DEFAULT` 값, `CHECK` 제약 조건

`DEFAULT` 항목은 **매뉴얼 안에서 반대로 적혀 있다.** 스키마 객체 페이지는 사용 불가
목록에 넣고, `CREATE TABLE` 페이지의 `DEFAULT expr` 항목은 `CURRVAL`과 `NEXTVAL`을
지정할 수 있다고 적는다. 실행해 확인할 수 없어 **어느 쪽이 맞는지 단정하지 않는다.**

순번 자동 채움에는 **identity 컬럼**이 따로 있다. `identity_clause`는 **Tibero 7
FS02부터 지원**하고 구성요소는 네 가지다.

| 구성요소 | 동작 |
|---|---|
| `ALWAYS` | 시퀀스 생성기로만 값을 할당. 사용자가 직접 지정하면 오류 |
| `BY DEFAULT` | 기본적으로 시퀀스 값을 할당하되 사용자가 명시적으로 지정 가능 |
| `ON NULL` | `INSERT` 시 NULL이 들어오면 시퀀스 값을 할당 |
| `sequence_attributes` | 시작 값, 증가 값 등을 지정 |

> `identity_clause`의 문법 도식은 매뉴얼에서 이미지로만 제공된다. 그래서 이 글은
> 구성요소만 옮긴다. 정확한 키워드 배치는 `CREATE TABLE` 문법 도식을 직접 확인할 것.

## 구조

![시퀀스 값이 나오는 경로와 번호가 건너뛰는 지점](fig/sequence-cache-path.svg)

> **구조 근거**: [Tibero 7.2.6 SQL 참조 안내서 — CREATE SEQUENCE](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/create-sequence.md)
> (`CACHE`는 지정한 개수만큼 값을 캐시에 저장하고 모두 사용하면 그 수만큼 다시 가져오며
> 그때마다 데이터 사전을 갱신한다는 점, 비정상 종료 시 캐시에 저장된 값이 유실될 수 있다는 점,
> `NOORDER`가 노드별 캐시를 유지한다는 점),
> [ALTER SEQUENCE](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/alter-sequence.md)
> (`ALTER SEQUENCE`가 캐시에 존재하던 값을 무효화해 일부 값이 누락될 수 있다는 점).
> 캐시의 내부 자료구조나 갱신 시점의 락 동작은 매뉴얼에 근거가 없어 그리지 않았다.

`CACHE N`을 주면 데이터 사전에서 N개를 미리 확보해 그 안에서 `NEXTVAL`을 처리하고,
다 쓰면 다시 N개를 가져오며 데이터 사전을 갱신한다. `NOCACHE`는 요청할 때마다 갱신한다.

성능과 연속성이 여기서 맞바꿔진다. 확보해 둔 N개는 **아직 아무도 쓰지 않았지만 이미
데이터 사전상으로는 발급된 값**이다. 그 상태로 비정상 종료하면 남은 값은 유실될 수
있다. `CACHE 100`이면 최대 99개가 빈다.

## 동작 원리

속성과 기본값을 정리하면 이렇다. 생략했을 때 무엇이 되는지가 실무에서 더 중요하다.

| 속성 | 생략했을 때 |
|---|---|
| `INCREMENT BY` | `1`. 양수면 증가, 음수면 감소 |
| `START WITH` | 증가 값이 양수면 `MINVALUE`, 음수면 `MAXVALUE` |
| `MAXVALUE` | `NOMAXVALUE`와 같다. 증가 값이 양수면 `INT64_MAX`, 음수면 `-1` |
| `MINVALUE` | `NOMINVALUE`와 같다. 증가 값이 양수면 `1`, 음수면 `INT64_MIN` |
| `CYCLE` / `NOCYCLE` | `NOCYCLE`. 한계에 닿으면 더 이상 값을 만들지 않는다 |
| `ORDER` / `NOORDER` | `NOORDER`. `ORDER`는 클러스터 환경에서만 지정할 수 있다 |
| `CACHE` / `NOCACHE` | **매뉴얼에 기본 개수가 명시되어 있지 않다** |

마지막 줄을 그대로 적은 이유가 있다. `CACHE` 생략 시 몇 개가 잡히는지는 매뉴얼에
나오지 않는다. 다른 DB의 기본값을 가져와 추정하지 말고 `USER_SEQUENCES`(또는
`ALL_SEQUENCES`, `DBA_SEQUENCES`)를 조회해 확인하는 편이 맞다. `INCREMENT BY`에는
제약이 하나 더 붙는다. `MAXVALUE - MINVALUE`보다 클 수 없다.

값이 증가하는 단위는 행이다. 매뉴얼은 **다섯 가지**를 든다. 최상위 `SELECT`가 반환하는 행,
`INSERT ... SELECT`에서 선택된 행, `CREATE TABLE ... AS SELECT`에서 선택된 행,
`UPDATE`가 갱신하는 각 행, `VALUES` 절을 포함한 `INSERT`가 삽입하는 행이다. 한 행에서
`NEXTVAL`이 여러 번 나와도 **증가는 한 번**이고 `CURRVAL`과 같은 값을 공유한다.

### 구성요소 표에 없는 제약과 그때 나오는 에러

구성요소 표에 없는 제약이 에러 참조 안내서에 드러난다. 미리 알면 DDL을 한 번에
통과시킬 수 있다.

| 에러 | 제약 |
|---|---|
| 7133 `ERROR_DDL_SEQ_INCR_ZERO` | `INCREMENT`는 0이 될 수 없다 |
| 7134 `ERROR_DDL_NEXTVAL_RANGE` | 다음(시작) 값은 `MINVALUE`와 `MAXVALUE` 사이여야 한다 |
| 7136 `ERROR_DDL_MUST_SPECIFY_MAXVAL` | 오름차순에서 `CYCLE`은 `MAXVALUE`와 함께 써야 한다 |
| 7135 `ERROR_DDL_MUST_SPECIFY_MINVAL` | 내림차순에서 `CYCLE`은 `MINVALUE`와 함께 써야 한다 |
| 7340 `ERROR_DDL_SEQ_CACHE_OVER_ONE_CYCLE` | **캐시 크기는 한 사이클보다 작아야 한다** |
| 7008 `ERROR_DDL_NOSTARTWITH_FOR_ALTER` | `START WITH`는 `CREATE`에서만 허용된다 |
| 7615 `ERROR_DDL_CANT_RESTART_WITH_CREATE_SEQUENCE` | `RESTART`는 `CREATE`에서 허용되지 않는다 |
| 7583 `ERROR_SEQ_CANNOT_BE_ACCESSED` | 이미 삭제되었거나 다른 세션이 삭제 중인 시퀀스 |
| 6003 `ERROR_DD_SEQ_NO_CURRVAL` | 같은 세션에서 `NEXTVAL`을 쓴 뒤에만 `CURRVAL`을 쓸 수 있다 |
| 6004 `ERROR_DD_SEQ_OVERFLOW` | 쓸 값을 다 썼다. 조치는 `ALTER SEQUENCE`로 범위 변경 |
| 7600 `ERROR_DDL_CANNOT_DISABLE_ALREADY_SCALED_SEQ_SCALABILITY` | 활성화된 시퀀스 확장성은 끌 수 없다. `NO SCALE`로 바꾸려면 삭제 후 재생성 |

7340이 특히 걸린다. `CYCLE` 시퀀스에 캐시를 크게 잡으면 생성 자체가 막힌다. 7008과
7615는 `CREATE`와 `ALTER`에서 쓸 수 있는 속성이 다르다는 뜻이다.

확장성 옵션은 근거가 한쪽에만 있다. 7600과 6011은 `NO SCALE`, `SCALE EXTEND` 같은
옵션을 언급하지만 SQL 참조 안내서 구성요소 표에는 설명이 없다. **옵션의 존재와 조치
문구까지만 적고 동작은 쓰지 않는다.**

### 번호가 건너뛰는 세 가지 경로

1. **비정상 종료.** 캐시에 저장된 값이 유실될 수 있다. `CACHE N`이면 최대 N-1개가 빈다.
2. **`ALTER SEQUENCE`.** 변경은 앞으로 생성될 번호에만 적용되고, 캐시를 쓰면
   **캐시에 존재하던 값을 무효화하기 때문에** 일부 값이 누락될 수 있다. 증가값을
   바꾸려고 한 번 돌린 것이 번호 구멍의 원인일 수 있다.
3. **클러스터 환경의 `NOORDER`.** 노드별 캐시를 유지하므로 노드 안에서는 순서가
   지켜지지만 **전체 노드 기준 순서는 달라진다.** 순서를 맞춰야 하면 `ORDER`를 쓴다.
   노드 간 발급 순서를 유지하는 옵션이므로 캐시로 얻던 이점을 포기하는 선택이 된다.

## 실습 예제

전체 스크립트: [`code/sequence_examples.sql`](code/sequence_examples.sql)
(`tbsql <사용자>/<비밀번호> @sequence_examples.sql`)

속성을 모두 지정하면 이렇게 된다.

```sql
CREATE SEQUENCE invoice_seq
    START WITH 1000
    INCREMENT BY 1
    MINVALUE 1000
    MAXVALUE 9999999999
    NOCYCLE
    CACHE 100
    NOORDER;
```

감소 시퀀스는 `START WITH`를 생략하면 `MAXVALUE`에서 시작한다.

```sql
CREATE SEQUENCE countdown_seq INCREMENT BY -1 MAXVALUE 1000 MINVALUE 1 NOCYCLE;
```

시작값으로 되돌릴 때 시퀀스를 다시 만들 필요는 없다. `RESTART`가 있다.

```sql
ALTER SEQUENCE invoice_seq RESTART;
ALTER SEQUENCE invoice_seq RESTART START WITH 5000;
```

`START WITH` 자체는 `ALTER`로 바꿀 수 없다(7008). 특정 값으로 옮기려면 위처럼
`RESTART START WITH`를 쓴다.

**이 절의 예제에는 출력이 없다.** 실행 검증을 하지 않았으므로 결과를 싣지 않는다.

## 실무에서 주의할 점

- **연속성이 필요하면 시퀀스를 쓰지 않는다.** 세금계산서 번호처럼 빈 번호가 문제가
  되는 요건이라면 맞는 도구가 아니다. 위 세 경로 중 하나만 발생해도 구멍이 생긴다.
- **`CACHE` 개수는 발급 속도와 최대 누락 개수를 동시에 정한다.** 크게 잡으면 데이터
  사전 갱신이 줄지만 비정상 종료 시 잃는 번호도 그만큼 늘어난다.
- **운영 중 `ALTER SEQUENCE`는 번호 구멍을 만든다.** 점검 시간에 하고 변경 전후 값을
  기록해 둔다.
- **컬럼 `DEFAULT`에 `NEXTVAL`을 쓸 수 있는지는 매뉴얼이 엇갈린다.** 확인 전에는
  `INSERT`에서 명시적으로 호출하거나 identity 컬럼을 쓰는 쪽이 안전하다.
- **`CYCLE`을 쓸 때 캐시 개수를 사이클보다 크게 잡지 않는다.** 7340으로 막힌다.
- **`CURRVAL`은 세션에 묶인다(6003).** 커넥션 풀에서 `NEXTVAL`과 `CURRVAL`을 다른
  요청에 나눠 호출하면 같은 세션이라는 보장이 없다.
- **`NOCYCLE` 시퀀스는 한계에 닿으면 멈춘다(6004).** 좁게 잡은 시퀀스는 소진 시점을
  감시해야 한다.

## 정리

- 시퀀스는 유일한 값을 빠르게 주는 객체다. **번호의 연속성은 보장 대상이 아니다.**
- 생략 기본값은 `INCREMENT BY 1`, `NOCYCLE`, `NOORDER`다. 캐시 기본 개수는 매뉴얼에
  없으므로 인스턴스에서 직접 확인한다.
- 번호가 건너뛰는 경로는 세 가지다. 비정상 종료, `ALTER SEQUENCE`, 클러스터 `NOORDER`.
- 구성요소 표에 없는 제약은 에러 코드로 확인한다. 특히 7340(캐시 < 사이클).
- 컬럼 `DEFAULT`는 매뉴얼 두 페이지가 반대로 적는다. 자동 채움은 identity 컬럼(FS02부터).

## 참고 자료

- [Tibero 7.2.6 SQL 참조 안내서 — CREATE SEQUENCE](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/create-sequence.md)
- [Tibero 7.2.6 SQL 참조 안내서 — ALTER SEQUENCE](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/alter-sequence.md)
- [Tibero 7.2.6 SQL 참조 안내서 — DROP SEQUENCE](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/drop-sequence.md)
- [Tibero 7.2.6 SQL 참조 안내서 — 스키마 객체 (시퀀스)](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/sql-elements/schema-objects.md)
- [Tibero 7.2.6 SQL 참조 안내서 — CREATE TABLE (coldef, identity_clause)](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/sql-reference-guide/data-definition-language/create-table.md)
- [Tibero 7.2.6 참조 안내서 — 정적 뷰](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/reference-guide/static-views.md)
- [Tibero 7.2.6 에러 참조 안내서 — chapter 6000.dd.error](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/error-reference-guide/chapter-6000.dd.error.md)
- [Tibero 7.2.6 에러 참조 안내서 — chapter 7000.ddl.error](https://docs.tibero.com/tibero-manuals/7.2.6.manuals/error-reference-guide/chapter-7000.ddl.error.md)
