---
title: "RIGHT JOIN과 FULL OUTER JOIN — SQLite 3.39 에서 생긴 양쪽 외부 조인"
date: 2026-11-05
categories: [Database]
subcategory: sql-basics
track: basics
tags: [sql, join, full-outer-join, basics]
description: "주문 목록과 입금 목록을 맞춰 보면 양쪽에 짝 없는 행이 모두 필요하다. RIGHT JOIN 과 FULL OUTER JOIN 이 무엇을 남기는지, 예전의 UNION ALL 우회와 결과가 같은지, 조건을 ON 에 두느냐 WHERE 에 두느냐가 결과를 어떻게 바꾸는지 SQLite 3.49.1 에서 확인한다."
difficulty: 입문
environment: ["SQLite 3.49.1", "Python 3.13.5"]
verification: executed
verified: true
topic_id: db-106
---

## 들어가며

월말에 주문 목록과 입금 목록을 맞춰 봐야 한다. 입금이 없는 주문도 찾아야 하고,
반대로 주문이 없는 입금, 이를테면 번호를 잘못 적은 입금도 찾아야 한다. 대부분은
`LEFT JOIN` 을 한 번 써서 입금 없는 주문을 뽑고, 표 순서를 뒤집어 한 번 더 써서
주문 없는 입금을 뽑은 뒤 두 결과를 엑셀에서 합친다. 쿼리는 두 번, 합치는 손은
한 번 더 든다. 데이터가 바뀌면 이 세 단계를 처음부터 다시 해야 한다.
이 일을 한 번에 하는 조인이 `FULL OUTER JOIN` 이다.

## 개념

외부 조인(outer join)은 `ON` 조건에 맞는 짝이 없는 행도 버리지 않고 남기는 조인이다.
짝이 없는 쪽 컬럼은 `NULL` 로 채워진다. 어느 쪽 표의 행을 남기느냐로 세 가지가
나뉜다.

| 종류 | 짝이 없어도 남기는 행 |
|---|---|
| `LEFT JOIN` | 왼쪽 표의 행 |
| `RIGHT JOIN` | 오른쪽 표의 행 |
| `FULL OUTER JOIN` | 양쪽 표의 행 |

SQLite 는 오랫동안 `LEFT JOIN` 만 지원했다. `RIGHT JOIN` 과 `FULL OUTER JOIN` 은
3.39.0 에서 추가됐다. 이 글의 예제는 3.49.1 에서만 돌렸고, 3.39.0 미만에서의 동작은
확인하지 않았다.

## 구조

![짝이 없는 행을 남기는 범위에 따른 조인 종류](fig/outer-join-matrix.svg)

> **출처**: [SQLite 3.39.0 릴리스 노트](https://www.sqlite.org/releaselog/3_39_0.html), [SQLite SELECT 문](https://www.sqlite.org/lang_select.html)

도식의 주문 4건·입금 4건에서 짝이 있는 행은 3개다(주문 1, 주문 2 두 건). 여기에
주문만 있는 행 2개, 입금만 있는 행 1개가 더해지는 방식으로 행 수가 달라진다.

## 동작 원리

먼저 조인은 `ON` 조건으로 짝을 맺은 뒤, 외부 조인이라면 짝을 못 만난 행을 `NULL`
로 채워 추가한다. `FULL OUTER JOIN` 은 이 보충을 양쪽에서 한다. 아래 예제의 8번은
`EXPLAIN QUERY PLAN` 이 `FULL OUTER JOIN` 을 어떻게 보여 주는지 찍은 것이다.

```text
SCAN o
SCAN p LEFT-JOIN
RIGHT-JOIN payment
SCAN p
```

`payment` 를 훑는 줄이 두 번 나온다. 한 번은 주문 기준 `LEFT-JOIN` 이고, 한 번은
`RIGHT-JOIN` 항목 아래의 훑기다. 한 쪽 표를 한 번만 읽는 `LEFT JOIN` 보다 일이 많다는
뜻으로 읽을 수 있으나, 내부 구현까지 확인한 것은 아니다.

그다음 `ON` 과 `WHERE` 의 차이가 있다. `ON` 은 짝을 **맺는** 조건이고 `WHERE` 는 조인이
끝난 결과에서 행을 **거르는** 조건이다. 외부 조인에서 이 둘은 결과가 다르다.

## 실습 예제

주문 4건과 입금 4건을 만든다. 전체 소스는 [`code/`](code/)에 있고, 출력은
`code/output.txt` 에서 가져왔다. 입금 12는 주문 2의 두 번째 입금이고, 입금 13은
존재하지 않는 주문 9를 가리킨다.

```text
  order_id | amount          payment_id | order_id | paid
  ---------+-------          -----------+----------+-----
         1 |   1000                  10 |        1 | 1000
         2 |   2000                  11 |        2 | 2000
         3 |   3000                  12 |        2 |  500
         4 |   4000                  13 |        9 |  700
```

**1. `LEFT JOIN`** 은 주문 기준으로 5행을 낸다. 주문 3, 4는 입금 컬럼이 `None` 이고
입금 13은 결과에 없다. 주문이 없는 입금을 못 찾는다.

**2. `RIGHT JOIN`** 은 입금 기준으로 4행을 낸다. 입금 13이 `(None, None, 13, 700)`
으로 남지만 이번에는 주문 3, 4가 사라진다.

**3. `FULL OUTER JOIN`** 은 6행이다. 정렬을 `ORDER BY o.order_id` 로 했더니 주문 번호가
`NULL` 인 입금 13이 맨 위에 나왔다. SQLite 는 `NULL` 을 가장 작은 값으로 정렬한다.

```text
(None, None, 13, 700)
(1, 1000, 10, 1000)
(2, 2000, 11, 2000)
(2, 2000, 12, 500)
(3, 3000, None, None)
(4, 4000, None, None)
```

**4. 예전 우회 방식**, 즉 `LEFT JOIN` 결과에 반대편 짝 없는 행을 `UNION ALL` 로 붙인
쿼리도 같은 6행을 냈다. 결과가 같으니 `FULL OUTER JOIN` 은 이 우회를 한 줄로 줄인
것이다. 우회 쿼리는 같은 표를 두 번 읽고 문장도 길다.

**5. 대사에 쓰는 형태**는 `FULL OUTER JOIN` 에 `WHERE o.order_id IS NULL OR p.payment_id
IS NULL` 을 붙인다. 입금 13, 주문 3, 주문 4 세 행만 남는다. 짝 없는 쪽을 찾으려면
`NULL` 이 아닌 키 컬럼을 검사해야 한다.

**6. 조건을 `ON` 에 둘 때와 `WHERE` 에 둘 때.** `p.paid >= 1000` 을 `ON` 에 두면 짝을
맺을 때만 쓰여서 주문 3, 4가 `None` 으로 남아 4행이 나온다. 같은 조건을 `WHERE` 에
두면 `NULL >= 1000` 이 참이 되지 않아 짝 없는 주문이 사라지고 2행만 남는다. 외부
조인으로 썼는데 결과가 내부 조인처럼 줄었다면 이 자리를 의심한다.

**7. 입금이 여러 건인 주문**은 조인하면 행이 늘어난다. 주문 2가 입금 2건과 만나
두 행이 된다. 금액을 대조하려면 입금을 `SUM` 으로 먼저 합친 뒤 조인한다. 이 경우 주문
2는 `(2, 2000, 2500)` 이 되어 입금이 주문보다 500 많다는 사실이 한 줄에 드러난다.

## 실무에서 주의할 점

1. **`WHERE` 에 외부 조인의 반대편 컬럼 조건을 쓰면 내부 조인이 된다.** 6번이 이
   경우다. 그 조건은 `ON` 으로 옮긴다.
2. **짝 없음은 키 컬럼의 `IS NULL` 로 판정한다.** 일반 컬럼은 짝이 있어도 값이
   `NULL` 일 수 있어서 판정에 쓰면 틀린다.
3. **일대다 관계에서는 행이 늘어난다.** 7번처럼 합계를 비교할 때는 먼저 집계한 뒤
   조인한다. 집계 전에 조인하면 주문 금액이 입금 건수만큼 중복 합산된다.
4. **버전 의존이다.** `RIGHT JOIN` 과 `FULL OUTER JOIN` 은 3.39.0 부터이므로, 낮은 버전의
   SQLite 가 내장된 환경에서 돌릴 쿼리라면 4번의 우회가 필요할 수 있다.

## 정리

- 외부 조인은 짝이 없는 행도 `NULL` 로 채워 남기고, 어느 쪽을 남기느냐가 `LEFT`·`RIGHT`·`FULL` 이다
- `FULL OUTER JOIN` 은 `LEFT JOIN` + 반대편 짝 없는 행의 `UNION ALL` 과 같은 6행을 냈다
- 짝 없는 행만 보려면 키 컬럼의 `IS NULL` 을 `WHERE` 에서 검사한다
- 반대편 표 컬럼에 대한 조건은 `ON` 에 둬야 외부 조인이 유지된다
- SQLite 에서는 3.39.0 부터 쓸 수 있다

## 참고 자료

- [SQLite 3.39.0 릴리스 노트](https://www.sqlite.org/releaselog/3_39_0.html)
- [SQLite SELECT 문](https://www.sqlite.org/lang_select.html)
