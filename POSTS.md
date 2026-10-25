# 글 목록

총 **447편** · 갱신 2026-10-26

> 이 파일은 `python scripts/blog.py index`가 생성한다. 직접 고치지 말 것.

## DB문법 (basics) — 69편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-23 | [WITHOUT ROWID 테이블 — 기본키가 곧 저장 순서](posts/Database/sql-basics/2026-10-23-without-rowid-table/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-23 | [AUTOINCREMENT와 rowid — 번호가 재사용되는가](posts/Database/sql-basics/2026-10-23-autoincrement-rowid-reuse/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-22 | [자기참조 외래키 — 계층 데이터를 한 표에 담기](posts/Database/sql-basics/2026-10-22-self-referencing-foreign-key/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-20 | [복합 기본키와 대리키 — 어느 쪽을 쓸까](posts/Database/sql-basics/2026-10-20-composite-key-vs-surrogate-key/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-19 | [ON CONFLICT 다섯 가지 — ROLLBACK·ABORT·FAIL·IGNORE·REPLACE](posts/Database/sql-basics/2026-10-19-on-conflict-five-resolutions/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-17 | [집계 함수의 FILTER 절 — CASE WHEN보다 읽기 쉬운 조건부 집계](posts/Database/sql-basics/2026-10-17-aggregate-filter-clause/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [NTILE — 데이터를 n등분하는 법](posts/Database/sql-basics/2026-10-16-ntile-quartile-remainder/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [인덱스와 NULL — 실행계획이 같은데 결과가 0건인 자리](posts/Database/sql-basics/2026-10-16-index-and-null/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-16 | [FIRST_VALUE와 LAST_VALUE — 구간의 처음과 끝](posts/Database/sql-basics/2026-10-16-first-value-last-value-window-frame/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [ANALYZE와 통계 — 옵티마이저가 보는 숫자](posts/Database/sql-basics/2026-10-16-analyze-and-statistics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-15 | [UPDATE … FROM — 다른 표의 값으로 갱신하기](posts/Database/sql-basics/2026-10-15-update-from-other-table/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-15 | [부분 인덱스 — WHERE가 붙은 인덱스](posts/Database/sql-basics/2026-10-15-partial-index-where-clause/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-15 | [표현식 인덱스 — 함수를 씌운 컬럼도 인덱스를 타게](posts/Database/sql-basics/2026-10-15-expression-index-function-on-column/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-14 | [임시 테이블과 CTE — 어느 쪽을 쓸까](posts/Database/sql-basics/2026-10-14-temp-table-vs-cte/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-14 | [키셋 페이지네이션 — OFFSET을 버리는 이유](posts/Database/sql-basics/2026-10-14-keyset-pagination-vs-offset/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-14 | [인덱스가 여럿일 때 무엇이 쓰이는가](posts/Database/sql-basics/2026-10-14-index-choice-multiple-indexes/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-14 | [커버링 인덱스 — 테이블을 안 보고 끝내기](posts/Database/sql-basics/2026-10-14-covering-index-no-table-lookup/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-13 | [중복 행 찾아 지우기 — GROUP BY HAVING과 rowid](posts/Database/sql-basics/2026-10-13-sql-find-delete-duplicate-rows/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-13 | [ORDER BY에 별칭과 표현식 쓰기](posts/Database/sql-basics/2026-10-13-order-by-alias-and-expression/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-13 | [CHECK 제약 — 값의 범위를 DB가 지키게](posts/Database/sql-basics/2026-10-13-check-constraint-value-range/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-13 | [BETWEEN과 IN — 범위와 목록을 쓰는 법](posts/Database/sql-basics/2026-10-13-between-in-range-list/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-12 | [트리거 기본 — 행이 바뀔 때 자동으로 도는 SQL](posts/Database/sql-basics/2026-10-12-trigger-before-after-audit/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-12 | [RETURNING — 넣은 값을 그 자리에서 돌려받기](posts/Database/sql-basics/2026-10-12-sqlite-returning-clause/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-12 | [LAG와 LEAD — 앞뒤 행의 값을 같은 줄에 놓기](posts/Database/sql-basics/2026-10-12-lag-lead-previous-next-row/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-12 | [INTERSECT와 EXCEPT — 두 결과의 교집합과 차집합](posts/Database/sql-basics/2026-10-12-intersect-except-set-operators/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-08 | [COLLATE — 대소문자와 정렬 규칙](posts/Database/sql-basics/2026-10-08-sql-collate-case-sort-order/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-08 | [생성 컬럼 — 계산 결과를 컬럼처럼, VIRTUAL과 STORED](posts/Database/sql-basics/2026-10-08-generated-column-virtual-stored/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-08 | [EXPLAIN QUERY PLAN 읽는 법 — SCAN, SEARCH, USE TEMP B-TREE](posts/Database/sql-basics/2026-10-08-explain-query-plan-reading/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-07 | [UPSERT — INSERT ... ON CONFLICT](posts/Database/sql-basics/2026-10-07-sqlite-upsert-on-conflict/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-07 | [재귀 CTE — 조직도를 한 질의로 펴는 법](posts/Database/sql-basics/2026-10-07-recursive-cte-hierarchy/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-07 | [GROUP_CONCAT — 여러 행을 한 줄로 합치는 법](posts/Database/sql-basics/2026-10-07-group-concat-rows-to-one-line/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-07 | [CTE — WITH 절로 질의에 이름 붙이기](posts/Database/sql-basics/2026-10-07-cte-with-clause/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [누적합과 이동평균 — SUM OVER의 프레임](posts/Database/sql-basics/2026-10-06-sum-over-frame-rows-range/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [자료형 — SQLite의 동적 타입](posts/Database/sql-basics/2026-10-06-sqlite-dynamic-typing-affinity/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [LIKE와 와일드카드 — % 와 _ 가 걸리는 자리](posts/Database/sql-basics/2026-10-06-sql-like-wildcard-escape/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [RANK와 DENSE_RANK — 동점을 어떻게 셀까](posts/Database/sql-basics/2026-10-06-rank-dense-rank-ties/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [GROUP BY 여러 컬럼 — 묶는 단위가 달라질 때](posts/Database/sql-basics/2026-10-06-group-by-multiple-columns/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-03 | [윈도우 함수 입문 — ROW_NUMBER로 그룹별 1등 뽑기](posts/Database/sql-basics/2026-10-03-window-function-row-number-top-per-group/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-03 | [NOT NULL과 DEFAULT — 값이 없을 때](posts/Database/sql-basics/2026-10-03-not-null-default-empty-string/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-03 | [인덱스 만들기 — CREATE INDEX 기본](posts/Database/sql-basics/2026-10-03-create-index-write-cost-storage/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-02 | [기본 키와 UNIQUE 제약](posts/Database/sql-basics/2026-10-02-primary-key-vs-unique/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-02 | [NULL 비교 — = NULL이 안 되는 이유](posts/Database/sql-basics/2026-10-02-null-comparison-three-valued-logic/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-02 | [COUNT(*)와 COUNT(컬럼)이 다른 값을 내는 이유](posts/Database/sql-basics/2026-10-02-count-star-vs-column-null/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-01 | [외래 키 — 참조 무결성과 ON DELETE](posts/Database/sql-basics/2026-10-01-sqlite-foreign-key-on-delete/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-01 | [숫자 타입과 반올림 — 돈을 다룰 때](posts/Database/sql-basics/2026-10-01-sql-numeric-types-rounding-money/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-01 | [날짜와 시간 다루기 — 저장과 연산](posts/Database/sql-basics/2026-10-01-sql-date-time-storage-arithmetic/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-30 | [트랜잭션 기본 — COMMIT, ROLLBACK, SAVEPOINT](posts/Database/sql-basics/2026-09-30-transaction-commit-rollback-savepoint/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-30 | [VIEW — 만들고 쓰는 법, 그리고 한계](posts/Database/sql-basics/2026-09-30-sqlite-view-updatable/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-30 | [문자열 함수 기본 — 자르기, 붙이기, 바꾸기](posts/Database/sql-basics/2026-09-30-sql-string-functions-basics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-30 | [ALTER TABLE — 컬럼을 바꿀 때의 제약](posts/Database/sql-basics/2026-09-30-alter-table-sqlite-limits/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [UPDATE — 조건 없는 UPDATE를 막는 습관](posts/Database/sql-basics/2026-09-29-update-where-count-first/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [INSERT — 단건, 다건, SELECT로 넣기](posts/Database/sql-basics/2026-09-29-insert-single-multi-select/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [DELETE, TRUNCATE, DROP — 무엇이 어디까지 지우는가](posts/Database/sql-basics/2026-09-29-delete-truncate-drop/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [CREATE TABLE — 타입과 기본 제약조건](posts/Database/sql-basics/2026-09-29-create-table-constraints-when-checked/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-28 | [UNION과 UNION ALL — 중복 제거 비용](posts/Database/sql-basics/2026-09-28-union-vs-union-all/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-28 | [IN, EXISTS, NOT IN — 결과가 갈리는 지점](posts/Database/sql-basics/2026-09-28-in-exists-not-in-null/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-28 | [COALESCE와 NULLIF — NULL을 다루는 두 함수](posts/Database/sql-basics/2026-09-28-coalesce-nullif-null-handling/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-28 | [CASE WHEN — 조건부 값과 피벗](posts/Database/sql-basics/2026-09-28-case-when-conditional-pivot/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [서브쿼리 세 가지 — 스칼라, 인라인 뷰, 상관](posts/Database/sql-basics/2026-09-23-subquery-scalar-inline-correlated/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [LEFT JOIN — 없는 쪽을 남기는 조인](posts/Database/sql-basics/2026-09-23-left-join-basics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [INNER JOIN — 두 테이블을 잇는 기본](posts/Database/sql-basics/2026-09-23-inner-join-basics/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-23 | [CROSS JOIN과 SELF JOIN — 언제 쓰는가](posts/Database/sql-basics/2026-09-23-cross-join-and-self-join/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-22 | [LIMIT과 OFFSET — 결과를 잘라내는 문법](posts/Database/sql-basics/2026-09-22-limit-offset-pagination/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [HAVING과 WHERE — 어느 단계에서 걸러지는가](posts/Database/sql-basics/2026-09-22-having-vs-where/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-22 | [GROUP BY와 집계 함수 — 묶는 기준 정하기](posts/Database/sql-basics/2026-09-22-group-by-aggregate-null/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [DISTINCT — 중복 제거가 정렬을 부르는 이유](posts/Database/sql-basics/2026-09-22-distinct-and-sorting/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [WHERE 조건 — AND와 OR의 우선순위](posts/Database/sql-basics/2026-09-21-where-and-or-precedence/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [ORDER BY — 다중 정렬과 NULL이 놓이는 자리](posts/Database/sql-basics/2026-09-21-order-by-null-placement/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [SELECT 기본 — 컬럼 고르기와 별칭](posts/Database/sql-basics/2026-09-18-select-columns-and-aliases/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |

## DB기능 (product) — 19편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-14 | [Tibero 7 시노님 — 공용과 전용이 놓인 자리가 다르다](posts/Database/tibero/2026-10-14-tibero7-synonym-public-private/index.md) | 입문 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-13 | [Tibero 7 머티리얼라이즈드 뷰 — 갱신 방식 고르기](posts/Database/tibero/2026-10-13-materialized-view-refresh-modes/index.md) | 심화 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-12 | [Tibero 7 제약조건 — 종류와 검증 시점](posts/Database/tibero/2026-10-12-tibero7-constraints-state-deferrable/index.md) | 입문 | Tibero 7.2.6 매뉴얼, SQLite 3.49.1 (비교 절) | 문서 근거 |
| 2026-10-08 | [Tibero 7 페이징 — ROWNUM이 정렬보다 먼저 붙는 이유와 OFFSET·FETCH](posts/Database/tibero/2026-10-08-tibero7-rownum-paging/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-07 | [Tibero 7 WITH 절 — 이름 붙인 부질의와 재귀 질의, SEARCH·CYCLE 절](posts/Database/tibero/2026-10-07-tibero7-with-clause-recursive-cte/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-07 | [Tibero 7 날짜·시간 타입 — DATE와 TIMESTAMP의 차이](posts/Database/tibero/2026-10-07-tibero7-date-timestamp-types/index.md) | 입문 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-06 | [Tibero 7 LOB — CLOB/BLOB 저장과 조회](posts/Database/tibero/2026-10-06-tibero7-lob-clob-blob/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-03 | [Tibero 7 딕셔너리 뷰 — 무엇을 어디서 찾는가](posts/Database/tibero/2026-10-03-tibero7-dictionary-views/index.md) | 입문 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-02 | [Tibero 7 외부 테이블 — 파일을 테이블처럼 읽기](posts/Database/tibero/2026-10-02-tibero7-external-table/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-10-01 | [Tibero 7 PSM — 저장 프로시저 기본 문법](posts/Database/tibero/2026-10-01-tibero7-psm-stored-procedure/index.md) | 입문 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-09-30 | [Tibero 7 트랜잭션 격리 수준 — 지원 범위와 설정](posts/Database/tibero/2026-09-30-tibero7-transaction-isolation/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-09-30 | [Tibero 7 실행계획 보기 — EXPLAIN PLAN과 DBMS_XPLAN](posts/Database/tibero/2026-09-30-tibero7-explain-plan-dbms-xplan/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-09-29 | [Tibero 7 옵티마이저 힌트 — 문법과 적용 확인](posts/Database/tibero/2026-09-29-tibero7-optimizer-hints/index.md) | 심화 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-09-28 | [Tibero 7 인덱스 종류 — B-Tree 말고 무엇이 있는가](posts/Database/tibero/2026-09-28-tibero7-index-types/index.md) | 중급 | Tibero 7.2.6 매뉴얼 | 문서 근거 |
| 2026-09-23 | [Tibero 7 분석 함수의 윈도우 절 — ROWS와 RANGE는 어디서 갈리는가](posts/Database/tibero/2026-09-23-tibero7-window-clause/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-23 | [Tibero 7 파티션 테이블 — 종류별로 언제 쓰는가](posts/Database/tibero/2026-09-23-tibero7-partition-table-types/index.md) | 심화 | Tibero 7.2 | 실행 검증 |
| 2026-09-22 | [Tibero 7 MERGE 문 — UPSERT를 한 문장으로, 그리고 DELETE 절의 함정](posts/Database/tibero/2026-09-22-tibero7-merge-upsert/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-22 | [Tibero 7 계층 질의 — CONNECT BY와 순환 참조](posts/Database/tibero/2026-09-22-tibero7-connect-by-hierarchy/index.md) | 중급 | Tibero 7.2 | 실행 검증 |
| 2026-09-18 | [Tibero 7 시퀀스 — 생성, 캐시, 그리고 값이 건너뛰는 순간](posts/Database/tibero/2026-09-18-tibero7-sequence-cache/index.md) | 입문 | Tibero 7.2 | 실행 검증 |

## 기술사 (pe) — 155편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-25 | [트라이와 PATRICIA — 비교 대신 비트로 분기하는 탐색 구조](posts/PE/software-engineering/2026-10-25-trie-and-patricia-bit-branching/index.md) | 중급 | Python 3.13.5, Journal of the ACM Vol. 15 No. 4 (1968-10), pp. 514-534, Communications of the ACM Vol. 3 No. 9 (1960-09), pp. 490-499, IEEE JSAC Vol. 17 No. 6 (1999-06), pp. 1083-1092, Dr. Dobb's Journal (1998-08) | 실행 검증 |
| 2026-10-25 | [우선순위 역전과 우선순위 상속 프로토콜 — 차단 시간에 상한을 거는 두 가지 방법](posts/PE/system/2026-10-25-priority-inversion-and-inheritance-protocols/index.md) | 중급 | Sha·Rajkumar·Lehoczky, IEEE Transactions on Computers 39(9) pp.1175-1185 (1990), POSIX.1-2017 (IEEE Std 1003.1-2017), Open Group Base Specifications Issue 7 2018 Edition | 문서 근거 |
| 2026-10-25 | [최장 접두사 일치와 포워딩 테이블 탐색](posts/PE/network/2026-10-25-longest-prefix-match-forwarding-lookup/index.md) | 중급 | RFC 1812 (1995-06), RFC 4632 (2006-08, BCP 122), RFC 7608 (2015-07, BCP 198), RFC 1519 (1993-09) | 문서 근거 |
| 2026-10-25 | [ISO/IEC 25024 데이터 품질 측정 — 품질 측정원소와 측정함수](posts/PE/data-analysis/2026-10-25-iso-25024-data-quality-measurement-qme/index.md) | 중급 | ISO/IEC 25024:2015, ISO/IEC 25012:2008, ISO/IEC 25020:2019, ISO/IEC 5259-2:2024 | 문서 근거 |
| 2026-10-25 | [DBSCAN — 군집과 잡음을 같은 정의에서 뽑아내는 여섯 단계](posts/PE/data-analysis/2026-10-25-dbscan-density-based-clustering-definitions/index.md) | 중급 | Python 3.13.5, Ester·Kriegel·Sander·Xu, KDD-96 Proceedings pp.226-231 (1996) | 실행 검증 |
| 2026-10-25 | [협업 필터링 — 사용자 기반·아이템 기반·행렬 분해가 먼저 계산하는 것](posts/PE/data-analysis/2026-10-25-collaborative-filtering-user-item-matrix-factorization/index.md) | 중급 | Python 3.13.5, Sarwar·Karypis·Konstan·Riedl, WWW10 Proceedings pp.285-295 (2001), Koren·Bell·Volinsky, IEEE Computer 42(8) pp.30-37 (2009) | 실행 검증 |
| 2026-10-23 | [객체지향 설계 원칙 SOLID 5가지](posts/PE/software-engineering/2026-10-23-solid-design-principles/index.md) | 중급 | Robert C. Martin, Design Principles and Design Patterns (2000), Liskov & Wing, ACM TOPLAS 16(6) (1994) | 문서 근거 |
| 2026-10-23 | [소프트웨어 재공학과 역공학](posts/PE/software-engineering/2026-10-23-software-reengineering-reverse-engineering/index.md) | 중급 | Chikofsky & Cross, IEEE Software 7(1) (1990-01), Fowler, Refactoring (refactoring.com, 2026년 10월 확인) | 문서 근거 |
| 2026-10-23 | [심슨의 역설 — 집단별 결론과 전체 결론이 뒤집히는 구조](posts/PE/data-analysis/2026-10-23-simpsons-paradox-confounder-collapsibility/index.md) | 중급 | Python 3.13.5, Simpson, JRSS Series B 13(2) (1951), Bickel·Hammel·O'Connell, Science 187(4175) (1975) | 실행 검증 |
| 2026-10-23 | [소프트웨어 개발 보안 — 시큐어 코딩과 SDL](posts/PE/software-engineering/2026-10-23-secure-coding-and-sdl/index.md) | 중급 | 소프트웨어 개발보안 가이드 2021년 12월판, NIST SP 800-218 SSDF 버전 1.1 (2022년 2월), Microsoft SDL (2026년 10월 확인) | 문서 근거 |
| 2026-10-23 | [강건 통계량 — 중앙값, MAD, 절사평균의 붕괴점](posts/PE/data-analysis/2026-10-23-robust-statistics-breakdown-point/index.md) | 중급 | Python 3.13.5, Davies·Gather, Annals of Statistics 33(3) (2005), NIST/SEMATECH e-Handbook of Statistical Methods (2012) | 실행 검증 |
| 2026-10-23 | [요구사항 스멜 — 언어 기준 9가지와 자동 탐지의 한계](posts/PE/software-engineering/2026-10-23-requirements-smells/index.md) | 중급 | ISO/IEC/IEEE 29148:2011, Femmer 외, Journal of Systems and Software 123 (2017) | 문서 근거 |
| 2026-10-23 | [MC/DC — 조건마다 독립 영향을 보이는 커버리지와 안전필수 소프트웨어](posts/PE/software-engineering/2026-10-23-mcdc-modified-condition-decision-coverage/index.md) | 심화 | NASA/TM-2001-210876 (2001-05), ISO/IEC/IEEE 29119-4:2021 (2판), Python 3.13.5 | 실행 검증 |
| 2026-10-23 | [결정 테이블 테스팅 — 조건 조합을 빠짐없이 케이스로 바꾸는 절차](posts/PE/software-engineering/2026-10-23-decision-table-testing/index.md) | 중급 | ISTQB CTFL Syllabus v4.0.1 (2024-09-15), ISO/IEC/IEEE 29119-4:2021 (2판), Python 3.13.5 | 실행 검증 |
| 2026-10-23 | [계약망 프로토콜 — 공고·입찰·낙찰로 과업을 나누는 분산 조정 규약](posts/PE/software-engineering/2026-10-23-contract-net-protocol-task-allocation/index.md) | 중급 | Smith, IEEE Transactions on Computers C-29(12) (1980), FIPA SC00029H Standard (2002-12-03) | 문서 근거 |
| 2026-10-20 | [SLA 지표 설계와 측정 — 99.9%가 실제로 허용하는 장애 시간](posts/PE/it-management/2026-10-20-sla-metrics-design-and-measurement/index.md) | 중급 | Python 3.13.5, ISO/IEC 19086-1:2016, IEC 61078:2016 (제3판), Windows 11 | 실행 검증 |
| 2026-10-20 | [ISO/IEC 38505-1 데이터 거버넌스 — 데이터 책임 지도와 가치·위험·제약](posts/PE/it-management/2026-10-20-iso-iec-38505-1-data-accountability-map/index.md) | 중급 | ISO/IEC 38505-1:2026 (제2판, 2026-08), ISO/IEC 38505-1:2017 (제1판), ISO/IEC 38500:2024 (제3판), ISO/IEC TR 38505-2:2018 | 문서 근거 |
| 2026-10-20 | [재해복구시스템 구축 수준 — 목표 시간을 백업 주기·복제 방식·훈련으로 옮기는 일](posts/PE/system/2026-10-20-dr-readiness-levels-backup-and-drills/index.md) | 중급 | NIST SP 800-34 Rev.1 (2010-05), NIST SP 800-84 (2006-09), FIPS 199 (2004-02) | 문서 근거 |
| 2026-10-20 | [데이터 자산화 — 관리적 자산화와 재무적 자산화](posts/PE/data-analysis/2026-10-20-data-assetization-managerial-vs-financial/index.md) | 중급 | IAS 38 / AASB 138 Intangible Assets (2015-09-30 공표본), ISO/IEC 38505-1:2026 (제2판), ISO/IEC 25012:2008, ISO/IEC 11179-1:2023 (제4판), 데이터산업법 (2022-04-20 시행) | 문서 근거 |
| 2026-10-20 | [에이전트 간 상호운용 프로토콜 — 능력 공표와 과업 수명주기](posts/PE/emerging-tech/2026-10-20-agent-interop-capability-and-task-lifecycle/index.md) | 중급 | A2A Protocol Specification v1.0.0, Model Context Protocol 사양 개정판 2026-07-28 | 문서 근거 |
| 2026-10-19 | [벡터 양자화와 율-왜곡 이론 — 비트를 줄이면 무엇을 잃는가](posts/PE/data-analysis/2026-10-19-vector-quantization-rate-distortion/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-19 | [SLA·SLO·SLI와 서비스수준관리(SLM) — 재는 것, 목표, 그리고 계약](posts/PE/it-management/2026-10-19-sla-slo-sli-service-level-management/index.md) | 중급 | ISO/IEC 20000-1:2018 (제3판), Google SRE Book ch.4 Service Level Objectives, Google SRE Workbook ch.2 Implementing SLOs, 행정기관 및 공공기관 정보시스템 안정성 고시(행정안전부고시 제2026-23호, 2026.4.13. 시행) | 문서 근거 |
| 2026-10-19 | [KV 캐시 — 트랜스포머 추론의 메모리 병목](posts/PE/emerging-tech/2026-10-19-kv-cache-transformer-inference/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-19 | [존슨-린덴스트라우스 보조정리와 랜덤 투영 — 차원을 줄여도 거리가 남는 이유](posts/PE/data-analysis/2026-10-19-johnson-lindenstrauss-random-projection/index.md) | 중급 | Python 3.13.5, Johnson·Lindenstrauss, Contemporary Mathematics 26 (1984), Dasgupta·Gupta, Random Structures & Algorithms 22(1) (2003), Achlioptas, JCSS 66(4) (2003) | 실행 검증 |
| 2026-10-19 | [소프트웨어 비용 산정 — 기능점수와 COCOMO](posts/PE/software-engineering/2026-10-19-function-point-cocomo-cost-estimation/index.md) | 중급 | Python 3.13.5, Windows 11, SW사업 대가산정 가이드 2024년 개정판, COCOMO 81 | 실행 검증 |
| 2026-10-17 | [IT 투자 평가 — TCO와 ROI](posts/PE/it-management/2026-10-17-it-investment-tco-roi/index.md) | 중급 | Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [설명가능 AI(XAI) 기법 분류 — 내재적 해석과 사후 설명의 신뢰도 차이](posts/PE/emerging-tech/2026-10-16-xai-method-taxonomy/index.md) | 중급 | NIST IR 8312 (2021-09), ISO/IEC TS 6254:2025 | 문서 근거 |
| 2026-10-16 | [ITSM과 ITIL 4 — 서비스 가치 시스템](posts/PE/it-management/2026-10-16-itsm-itil4-service-value-system/index.md) | 중급 | ITIL 4 (2019년판), ISO/IEC 20000-1:2018 (제3판) | 문서 근거 |
| 2026-10-16 | [IT 거버넌스 — COBIT 2019 구성요소](posts/PE/it-management/2026-10-16-it-governance-cobit-2019/index.md) | 중급 | COBIT 2019 | 문서 근거 |
| 2026-10-16 | [ISP와 ISMP — 산출물과 발주 시점이 갈리는 지점](posts/PE/it-management/2026-10-16-isp-vs-ismp/index.md) | 중급 | ISP·ISMP 수립 공통가이드 제9판 (2025), 경영정보학연구 14권 1호 (2012) | 문서 근거 |
| 2026-10-15 | [양자 내성 암호(PQC)와 전환 전략](posts/PE/emerging-tech/2026-10-15-post-quantum-cryptography-transition/index.md) | 중급 | NIST FIPS 203 (2024-08-13), NIST FIPS 204 (2024-08-13), NIST FIPS 205 (2024-08-13), NIST IR 8547 ipd (2024-11-12) | 문서 근거 |
| 2026-10-15 | [MLOps 파이프라인과 모델 드리프트 대응](posts/PE/emerging-tech/2026-10-15-mlops-pipeline-model-drift/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-15 | [엣지 컴퓨팅과 클라우드 연계 구조](posts/PE/emerging-tech/2026-10-15-edge-cloud-continuum-architecture/index.md) | 중급 | NIST SP 500-325 (2018), ETSI GS MEC 003 V2.2.1 (2020-12) | 문서 근거 |
| 2026-10-15 | [디지털 트윈 — ISO 23247 프레임워크](posts/PE/emerging-tech/2026-10-15-digital-twin-iso-23247/index.md) | 중급 | ISO/FDIS 23247-1:2021, ISO/FDIS 23247-2:2021, ISO/IEC 30141 (IoT 참조 아키텍처) | 문서 근거 |
| 2026-10-14 | [RAG 구성요소와 검색 품질 지표](posts/PE/emerging-tech/2026-10-14-rag-components-retrieval-metrics/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-14 | [대규모 언어 모델(LLM)의 구조와 한계](posts/PE/emerging-tech/2026-10-14-llm-architecture-limits/index.md) | 중급 | Python 3.13.5 | 실행 검증 |
| 2026-10-14 | [람다 아키텍처와 카파 아키텍처](posts/PE/database/2026-10-14-lambda-vs-kappa-architecture/index.md) | 중급 | Nathan Marz, How to beat the CAP theorem (2011-10-13), Marz·Warren, Big Data (Manning, 2015), Jay Kreps, Questioning the Lambda Architecture (2014-07-02), Apache Kafka 공식 문서 (2026-10-14 확인) | 문서 근거 |
| 2026-10-14 | [데이터 계보(Data Lineage)와 메타데이터 카탈로그](posts/PE/database/2026-10-14-data-lineage-metadata-catalog/index.md) | 중급 | W3C PROV-DM (REC 2013-04-30), W3C DCAT 3 (REC 2024-08-22), ISO/IEC 11179-1:2023 (4판), BCBS 239 (2013-01-09, Basel Framework SRP36 2019-12-15판), Apache Atlas 2.0.0, OpenLineage 스펙 (2026-10-14 확인), DataHub 문서 (2026-10-14 확인), dbt 문서 (2026-10-14 확인) | 문서 근거 |
| 2026-10-13 | [RLHF — 사람 피드백 강화학습의 SFT·보상 모델·PPO 3단계](posts/PE/emerging-tech/2026-10-13-rlhf-sft-reward-model-ppo/index.md) | 중급 | Christiano et al., arXiv:1706.03741 (2017-06), Ouyang et al., arXiv:2203.02155 (2022-03), Rafailov et al., arXiv:2305.18290 (2023-05), Bai et al., arXiv:2212.08073 (2022-12) | 문서 근거 |
| 2026-10-13 | [랜섬웨어 대응 체계 — 예방·탐지·복구](posts/PE/security/2026-10-13-ransomware-defense-prevention-detection-recovery/index.md) | 중급 | NIST CSF 2.0 (2024-02-26), NIST IR 8374r1 (2026-06), CISA #StopRansomware Guide (2023-09), US-CERT Data Backup Options (2012) | 문서 근거 |
| 2026-10-13 | [RAID 레벨별 특성과 선택 기준 — 쓰기 페널티를 I/O 수로 세기](posts/PE/system/2026-10-13-raid-levels-write-penalty/index.md) | 중급 | Python 3.13.5, Patterson·Gibson·Katz, A Case for RAID (SIGMOD 1988), Arpaci-Dusseau, OSTEP v1.10 Ch.38, Anvin, The mathematics of RAID-6 (2011-12-20판) | 실행 검증 |
| 2026-10-13 | [매개변수 효율적 미세조정(PEFT) — LoRA·어댑터·프롬프트 튜닝](posts/PE/emerging-tech/2026-10-13-peft-lora-adapter-prompt-tuning/index.md) | 중급 | Houlsby et al., ICML 2019 (arXiv:1902.00751), Li & Liang, ACL 2021 (arXiv:2101.00190), Lester et al., EMNLP 2021 (arXiv:2104.08691), Hu et al., arXiv:2106.09685v2 (2021-10), Lialin et al., arXiv:2303.15647 (2024) | 문서 근거 |
| 2026-10-13 | [메모리 계층과 캐시 일관성 프로토콜 — MESI 네 상태와 전이](posts/PE/system/2026-10-13-memory-hierarchy-cache-coherence-mesi/index.md) | 중급 | Intel 64 and IA-32 SDM Vol. 3A 253668-082US (2023-12), ISCA 1984 논문 원문 | 문서 근거 |
| 2026-10-13 | [멤버십 추론 공격과 학습 데이터 암기 — 모델 질의만으로 생기는 프라이버시 리스크](posts/PE/security/2026-10-13-membership-inference-memorization/index.md) | 중급 | NIST AI 100-2 E2025 (2025-03), 개인정보보호위원회 AI 프라이버시 리스크 관리 모델 (2024-12-19 공개) | 문서 근거 |
| 2026-10-13 | [ISMS-P 인증 체계와 통제 항목 구조](posts/PE/security/2026-10-13-isms-p-certification-control-structure/index.md) | 중급 | ISMS-P 인증기준 안내서 (2023.11, 개인정보보호위원회·과학기술정보통신부), ISO/IEC 27001:2022 | 문서 근거 |
| 2026-10-13 | [적대적 머신러닝 공격 분류 — 회피·오염·프라이버시·오용 허용](posts/PE/security/2026-10-13-adversarial-ml-attack-taxonomy/index.md) | 중급 | NIST AI 100-2 E2025 (2025-03) | 문서 근거 |
| 2026-10-12 | [변분 양자 알고리즘(VQA)과 양자머신러닝 — 하이브리드 루프와 기울기 소실 고원](posts/PE/ai/2026-10-12-vqa-hybrid-loop-barren-plateau/index.md) | 중급 | Cerezo et al., Nature Reviews Physics 3 (2021), Python 3.13.5 | 실행 검증 |
| 2026-10-12 | [공급망 보안과 SBOM — 목록이 막는 것과 못 막는 것](posts/PE/security/2026-10-12-sbom-supply-chain-limits/index.md) | 중급 | NTIA SBOM Minimum Elements (2021-07-12), CISA SBOM Types (2023-04-21), CISA 2025 SBOM Minimum Elements 공개 의견 수렴 초안 (2025-08-22), SLSA v1.2 | 문서 근거 |
| 2026-10-12 | [가명처리용 암호 기법 — 형태보존·순서보존·동형 암호가 분석에서 남기는 것과 새는 것](posts/PE/security/2026-10-12-pseudonymization-ope-fpe-he-leakage/index.md) | 중급 | 가명정보 처리 가이드라인 2022.4, NIST SP 800-38G Rev.1 2nd Public Draft 2025.2, Python 3.13.5 | 실행 검증 |
| 2026-10-12 | [페이지 교체 알고리즘과 벨레이디의 이상현상](posts/PE/system/2026-10-12-page-replacement-belady-anomaly/index.md) | 중급 | Python 3.13.5, Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018) Ch.10 슬라이드 (S. Weiss 2020 개정판), Arpaci-Dusseau, Operating Systems: Three Easy Pieces v1.10 Ch.22 | 실행 검증 |
| 2026-10-12 | [교착상태 4조건과 해결 기법](posts/PE/system/2026-10-12-deadlock-conditions-bankers-algorithm/index.md) | 중급 | Python 3.13.5, Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018) Ch.8 슬라이드 (S. Weiss 2020 개정판), Arpaci-Dusseau, Operating Systems: Three Easy Pieces v1.20 Ch.32 | 실행 검증 |
| 2026-10-12 | [프로세스 스케줄링 알고리즘과 평균 대기시간 계산](posts/PE/system/2026-10-12-cpu-scheduling-waiting-time/index.md) | 중급 | Python 3.13.5, Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018) Ch.5 슬라이드 (S. Weiss 2020 개정판), Arpaci-Dusseau, Operating Systems: Three Easy Pieces v1.10 Ch.7 | 실행 검증 |
| 2026-10-10 | [Wi-Fi 7 다중 링크 동작(MLO) — 동기·비동기 다중 링크와 링크 간 간섭](posts/PE/network/2026-10-10-wi-fi-7-multi-link-operation-str-nstr/index.md) | 중급 | IEEE 802.11be-2024 (2024-09 승인), Deng et al., arXiv:2007.13401v3 (2020-08), López-Raventós·Bellalta, arXiv:2201.07499 (2022-01), Carrascosa-Zamacois et al., arXiv:2210.07695 (2022-10) | 문서 근거 |
| 2026-10-10 | [CTEM과 노출 관리 — 취약점 관리에서 검증·동원 단계를 더한 이유](posts/PE/security/2026-10-10-ctem-exposure-management-vs-vm-asm-bas/index.md) | 중급 | Gartner G00796532 (2023-10-16), NIST SP 800-40r4 (2022-04), FIRST EPSS (2026-10-10 조회), CISA KEV (BOD 22-01, BOD 26-04 2026-06-10), IBM Think CTEM (2026-06-05), HackerOne CTEM Guide (2026-07-02), Infosecurity Europe CTEM (2026-08-14) | 문서 근거 |
| 2026-10-10 | [편향-분산 트레이드오프와 규제 — 모형 용량을 고르는 방법](posts/PE/data-analysis/2026-10-10-bias-variance-tradeoff-regularization/index.md) | 중급 | Python 3.13.5, Geman·Bienenstock·Doursat, Neural Computation 4(1) (1992), Srivastava et al., JMLR 15 (2014) | 실행 검증 |
| 2026-10-10 | [기본 경로 테스트 — 순환복잡도로 테스트 경로를 고르는 절차](posts/PE/software-engineering/2026-10-10-basis-path-testing-baseline-method/index.md) | 중급 | Python 3.13.5, NIST SP 500-235 (1996) | 실행 검증 |
| 2026-10-09 | [무중단 배포 전략 — 롤링·블루그린·카나리와 확장-축소 스키마 변경](posts/PE/software-engineering/2026-10-09-zero-downtime-deployment-expand-contract/index.md) | 중급 | Kubernetes v1.37 문서 (apps/v1 Deployment), Google SRE Workbook (2018), Sadalage·Fowler, Evolutionary Database Design (2016-05 갱신) | 문서 근거 |
| 2026-10-09 | [Modular RAG — 모듈·연산자 3계층과 흐름 패턴](posts/PE/emerging-tech/2026-10-09-modular-rag-operators-flow-patterns/index.md) | 중급 | Gao et al., arXiv:2407.21059v1 (2024-07-26), Gao et al., arXiv:2312.10997v5 (2024-03-27), Lewis et al., NeurIPS 2020 | 문서 근거 |
| 2026-10-09 | [엣지·포그·MEC 컴퓨팅 — NIST 포그 모델과 ETSI MEC 참조 구조](posts/PE/cloud/2026-10-09-edge-fog-mec-computing/index.md) | 중급 | NIST SP 500-325 (2018-03), ETSI GS MEC 003 V3.1.1 (2022-03), ISO/IEC TR 23188:2020 | 문서 근거 |
| 2026-10-08 | [제로 트러스트 아키텍처 — NIST SP 800-207의 7원칙과 3구성요소](posts/PE/security/2026-10-08-zero-trust-architecture-nist-sp-800-207/index.md) | 중급 | NIST SP 800-207 Zero Trust Architecture (2020-08), CISA Zero Trust Maturity Model Version 2.0 (2023-04), 제로트러스트 가이드라인 2.0 (과학기술정보통신부·KISA, 2024-12) | 문서 근거 |
| 2026-10-08 | [개인정보 비식별·가명처리 절차와 적정성 평가 — k-익명성·ℓ-다양성·t-근접성이 막는 공격과 못 막는 공격](posts/PE/security/2026-10-08-pseudonymization-steps-k-anonymity-limits/index.md) | 중급 | 개인정보 비식별 조치 가이드라인 2016.6, 가명정보 처리 가이드라인 2022.4, Python 3.13.5 | 실행 검증 |
| 2026-10-08 | [공개키 기반구조(PKI)와 인증서 검증 경로](posts/PE/security/2026-10-08-pki-certificate-path-validation-revocation/index.md) | 중급 | RFC 5280 (2008-05), RFC 6960 (2013-06), RFC 6066 (2011-01), CA/B Forum BR 2.0.1 (2024-03-15), OpenSSL 3.5.6 | 실행 검증 |
| 2026-10-08 | [대수의 법칙과 중심극한정리 — 전제가 깨지는 운영 데이터에서 무엇이 틀어지는가](posts/PE/data-analysis/2026-10-08-lln-clt-assumptions-in-operational-data/index.md) | 중급 | Python 3.13.5, Grinstead & Snell, Introduction to Probability 2nd ed. (AMS, 2003), Shevtsova, arXiv:1111.6554 (2011) | 실행 검증 |
| 2026-10-08 | [컴플라이언스 경영시스템 ISO 37301 — 의무 식별과 위험 평가](posts/PE/it-management/2026-10-08-iso-37301-compliance-management-system/index.md) | 중급 | ISO 37301:2021 (2021-04-13 발행), ISO 19600:2014 (철회), ISO/IEC 27001:2022, OCEG GRC Capability Model 3.5 (2023) | 문서 근거 |
| 2026-10-08 | [데이터센터 효율 지표 — PUE·WUE와 ISO/IEC 30134 시리즈](posts/PE/system/2026-10-08-data-center-pue-wue-iso-iec-30134/index.md) | 중급 | ISO/IEC 30134-2:2026 (2nd ed.), ISO/IEC 30134-9:2022, The Green Grid WP#49 (2012), The Green Grid WP#35 (2011-03), Uptime Institute Global Data Center Survey 2025 | 문서 근거 |
| 2026-10-08 | [데이터센터 액체 냉각 — 콜드플레이트·액침과 ASHRAE 시설수 온도 등급](posts/PE/system/2026-10-08-data-center-liquid-cooling-ashrae-w-classes/index.md) | 중급 | ASHRAE TC 9.9 Liquid Cooling White Paper (2021-05-07), ASHRAE Thermal Guidelines for Data Processing Environments 5th ed. (2021-03), Uptime Institute Cooling Systems Survey 2024 (2024-05), NVIDIA DGX SuperPOD GB200 Reference Architecture (2025-11) | 문서 근거 |
| 2026-10-07 | [QUIC와 HTTP/3 — TCP 위에서 못 풀던 세 가지를 UDP로 내려가 푼 이유](posts/PE/network/2026-10-07-quic-http3-udp-transport/index.md) | 중급 | RFC 9000 (2021-05), RFC 9001 (2021-05), RFC 9002 (2021-05), RFC 9114 (2022-06), RFC 8446 (2018-08), Python 3.13.5 | 실행 검증 |
| 2026-10-07 | [시계열 이상 탐지 평가 — 점 조정(point-adjust)이 성능을 부풀리는 이유](posts/PE/data-analysis/2026-10-07-point-adjust-evaluation-inflation/index.md) | 중급 | Python 3.13.5, Kim et al., AAAI 2022, Xu et al., WWW 2018, Ren et al., KDD 2019, Tatbul et al., NeurIPS 2018 | 실행 검증 |
| 2026-10-07 | [로드 밸런싱 — L4와 L7, 분배 알고리즘, 그리고 세션 고정의 비용](posts/PE/network/2026-10-07-load-balancing-l4-l7-algorithms/index.md) | 중급 | RFC 2391 (1998-08), RFC 9110 (2022-06), Karger et al. STOC 1997, Eisenbud et al. NSDI 2016, Python 3.13.5 | 실행 검증 |
| 2026-10-07 | [Isolation Forest — 고립에 필요한 분할 횟수로 이상치를 찾는 원리](posts/PE/data-analysis/2026-10-07-isolation-forest-path-length/index.md) | 중급 | Python 3.13.5, Liu, Ting & Zhou, ICDM 2008, scikit-learn 1.9.1 User Guide | 실행 검증 |
| 2026-10-07 | [ISMS-P 인증 — 3개 영역 인증기준과 의무 대상](posts/PE/security/2026-10-07-isms-p-certification-three-domains/index.md) | 중급 | 정보통신망법 법률 제21988호 (2026-10-02 시행), 정보통신망법 시행령 대통령령 제36728호 (2026-10-02 시행), 개인정보 보호법 법률 제21445호 (2026-09-11 시행), 정보보호 및 개인정보보호 관리체계 인증 등에 관한 고시 (2024-07-24 시행), ISMS-P 인증기준 안내서 2023.11, ISO/IEC 27001:2022 | 문서 근거 |
| 2026-10-07 | [IPv6 전환 기술 3가지 — 듀얼스택·터널링·변환은 언제 쓰는가](posts/PE/network/2026-10-07-ipv6-transition-dual-stack-tunneling-translation/index.md) | 중급 | RFC 4213 (2005-10), RFC 6144 (2011-04), RFC 6052 (2010-10), RFC 6146 (2011-04), RFC 3056 (2001-02), Python 3.13.5 | 실행 검증 |
| 2026-10-07 | [오토인코더 기반 이상 탐지 — 재구성 오차로 정상에서 벗어난 것을 찾는 원리](posts/PE/data-analysis/2026-10-07-autoencoder-reconstruction-anomaly-detection/index.md) | 중급 | Python 3.13.5, An & Cho, SNU DM TR 2015, Zhou & Paffenroth, KDD 2017, Goodfellow et al., Deep Learning (2016) ch.14 | 실행 검증 |
| 2026-10-07 | [5G 네트워크 슬라이싱](posts/PE/network/2026-10-07-5g-network-slicing/index.md) | 중급 | 3GPP TS 23.501 V17.15.0 (ETSI TS 123 501, 2026-01), 3GPP TS 28.530 V17.3.0 (ETSI TS 128 530, 2022-10) | 문서 근거 |
| 2026-10-06 | [트랜잭션 ACID와 2단계 커밋(2PC)](posts/PE/database/2026-10-06-two-phase-commit-blocking-window/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Bernstein·Hadzilacos·Goodman, Concurrency Control and Recovery in Database Systems 7장 (1987), X/Open XA Specification (1991) | 실행 검증 |
| 2026-10-06 | [TCP 혼잡 제어 알고리즘 비교 — Reno·CUBIC·BBR은 무엇을 신호로 삼는가](posts/PE/network/2026-10-06-tcp-congestion-control-reno-cubic-bbr/index.md) | 중급 | RFC 5681 (2009-09), RFC 9438 (2023-08), draft-ietf-ccwg-bbr-06 (2026-07), Python 3.13.5 | 실행 검증 |
| 2026-10-06 | [표본추출 — 확률·비확률 표본설계와 포함확률·가중치](posts/PE/data-analysis/2026-10-06-sampling-design-inclusion-probability-weights/index.md) | 중급 | Python 3.13.5, Statistics Canada, Survey Methods and Practices 12-587-X (2003), Horvitz & Thompson, JASA 47(260) (1952) | 실행 검증 |
| 2026-10-06 | [NoSQL 4가지 유형과 선택 기준](posts/PE/database/2026-10-06-nosql-four-types-access-pattern/index.md) | 중급 | NIST SP 1500-1r2 (2019-10), DeCandia 외, Dynamo, SOSP 2007, Chang 외, Bigtable, OSDI 2006, MongoDB Manual 9.0, ISO/IEC 39075:2024 (GQL), Microsoft Azure Architecture Center (2025-08-21) | 문서 근거 |
| 2026-10-06 | [데이터 웨어하우스·데이터 레이크·레이크하우스](posts/PE/database/2026-10-06-dw-lake-lakehouse-schema-timing/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Chaudhuri·Dayal, SIGMOD Record 1997, Armbrust 외, CIDR 2021, Delta Transaction Log Protocol (master, 2026-10-06 열람) | 실행 검증 |
| 2026-10-06 | [데이터 누수 — 학습·평가 분할에서 묶음·시간 단위를 지키는 이유](posts/PE/data-analysis/2026-10-06-data-leakage-group-time-split/index.md) | 중급 | Python 3.13.5, scikit-learn 1.9.1 User Guide, Kaufman et al., ACM TKDD 6(4) (2012), Kapoor & Narayanan, arXiv:2207.07048 (2022) | 실행 검증 |
| 2026-10-06 | [데이터 거버넌스와 데이터 품질 관리 체계](posts/PE/database/2026-10-06-data-governance-quality-dimensions-roles/index.md) | 중급 | DAMA-DMBOK2 (2017), DAMA UK DQ Dimensions White Paper (2013-10), UK Government Data Quality Framework (2020-12-03), Federal Data Strategy Data Governance Playbook (2020-07), ISO/IEC 25012:2008, CNSSI 4009-2022 | 문서 근거 |
| 2026-10-06 | [분산 데이터베이스 — CAP 정리와 BASE](posts/PE/database/2026-10-06-cap-theorem-base-pacelc/index.md) | 중급 | Python 3.13.5, Brewer, PODC 2000 기조연설, Gilbert·Lynch, IEEE Computer 2012, Brewer, IEEE Computer 2012, Abadi, IEEE Computer 2012 | 실행 검증 |
| 2026-10-06 | [브랜치·병합 전략 — 트렁크 기반 개발과 기능 브랜치](posts/PE/software-engineering/2026-10-06-branching-merging-strategy-trunk-feature/index.md) | 중급 | ISO/IEC TR 19759:2016 (SWEBOK V3.0), DORA Capabilities (2026-10 확인), Pro Git 2판 (2014) | 문서 근거 |
| 2026-10-05 | [인공지능 기본법과 EU AI법 — 위험 기반 규제 구조 비교](posts/PE/it-management/2026-10-05-korea-ai-basic-act-vs-eu-ai-act/index.md) | 중급 | 인공지능 기본법 법률 제21311호 (2026-01-20 일부개정), 인공지능 기본법 시행령 대통령령 제36580호, Regulation (EU) 2024/1689 (AI Act), Regulation (EU) 2026/1744 (Digital Omnibus on AI, 2026-07-27 발효) | 문서 근거 |
| 2026-10-05 | [데이터 가치평가 — 수익·원가·시장접근법과 데이터산업법 가치평가 제도](posts/PE/data-analysis/2026-10-05-data-valuation-income-cost-market-approach/index.md) | 중급 | 데이터 산업진흥 및 이용촉진에 관한 기본법 제14조 (2022-04-20 시행), 과기정통부 데이터 가치평가 안내서 (2024-07-04), IVS 210 Intangible Assets 공개초안 (IVS 2017 개정용), OECD Digital Economy Papers No. 345 (2022-12) | 문서 근거 |
| 2026-10-05 | [프로젝트 일정 관리 — CPM과 PERT](posts/PE/software-engineering/2026-10-05-cpm-pert-critical-path-float/index.md) | 중급 | Python 3.13.5, NASA/SP-2010-3403 Schedule Management Handbook (2010-01), GAO-16-89G Schedule Assessment Guide (2015-12) | 실행 검증 |
| 2026-10-05 | [AI 시스템 영향평가 — ISO/IEC 42005와 기본권 영향평가](posts/PE/it-management/2026-10-05-ai-system-impact-assessment-iso-42005/index.md) | 중급 | ISO/IEC 42005:2025 (제1판, 2025-05), ISO/IEC 42001:2023, 인공지능 기본법 시행령 대통령령 제36580호, Regulation (EU) 2024/1689 (AI Act), Regulation (EU) 2026/1744 개정 반영 | 문서 근거 |
| 2026-10-04 | [무선 다중 접속 방식 — FDMA·TDMA·CDMA·OFDMA](posts/PE/network/2026-10-04-wireless-multiple-access-fdma-tdma-cdma-ofdma/index.md) | 중급 | 3GPP TS 45.005 V13.4.0 (2017-04), 3GPP TS 45.002 V13.2.0 (2016-08), 3GPP TS 25.213 V4.0.0 (2001-03), 3GPP TS 36.211 V8.9.0 (2010-01), 3GPP TS 36.300 V8.12.0 (2010-04), Python 3.13.5 | 실행 검증 |
| 2026-10-04 | [블록·파일·오브젝트 스토리지 — 접근 모델 3가지와 SAN·NAS·DAS](posts/PE/system/2026-10-04-storage-access-models-das-san-nas/index.md) | 중급 | NIST SP 800-209 (2020-10), Amazon S3 User Guide (2026-10 확인), Amazon EBS User Guide (2026-10 확인), Ceph Documentation latest (2026-10 확인) | 문서 근거 |
| 2026-10-04 | [병렬 파일 시스템 — Lustre의 MDS·OSS 분리와 스트라이핑](posts/PE/system/2026-10-04-parallel-file-system-lustre-pnfs/index.md) | 심화 | Lustre Software Release 2.x Operations Manual (2026-10 확인), RFC 8881 (2020-08), RFC 8434 (2018-08), NIST SP 800-209 (2020-10) | 문서 근거 |
| 2026-10-04 | [IEEE 802.11 DCF와 CSMA/CA — IFS·백오프·RTS/CTS](posts/PE/network/2026-10-04-ieee-802-11-dcf-csma-ca/index.md) | 중급 | RFC 8325 (2018-02), Bianchi, IEEE JSAC Vol.18 No.3 (2000-03), Inan·Keceli·Ayanoglu, arXiv:0704.1838 (2007-04), Python 3.13.5 | 실행 검증 |
| 2026-10-03 | [기술부채 — 측정 방법과 상환 전략](posts/PE/software-engineering/2026-10-03-technical-debt-measurement-repayment/index.md) | 중급 | Dagstuhl Seminar 16162 Report (2016), Kruchten·Nord·Ozkaya, IEEE Software 29(6) (2012-11), SonarQube Server 문서 (2026-10 열람) | 문서 근거 |
| 2026-10-03 | [합성데이터 — 유용성과 안전성의 상충, 구별·연결·추론 위험도](posts/PE/data-analysis/2026-10-03-synthetic-data-utility-privacy-tradeoff/index.md) | 중급 | 개인정보보호위원회 합성데이터 생성·활용 안내서 (2024-12), NIST SP 800-188 (2023-09), NIST SP 800-226 (2025-03), Python 3.13.5 | 실행 검증 |
| 2026-10-03 | [리팩토링 — 코드 스멜 분류와 적용 시점](posts/PE/software-engineering/2026-10-03-refactoring-code-smells-when-to-apply/index.md) | 중급 | Fowler, Refactoring 2nd ed. (2018), Mäntylä & Lassenius, Empirical Software Engineering 11(3) (2006), Chikofsky & Cross, IEEE Software 7(1) (1990-01) | 문서 근거 |
| 2026-10-03 | [메타모픽 테스트와 테스트 오라클 문제](posts/PE/software-engineering/2026-10-03-metamorphic-testing-test-oracle-problem/index.md) | 중급 | ISO/IEC/IEEE 29119-4:2021, Barr et al., IEEE TSE 41(5) (2015-05), Chen et al., ACM Computing Surveys 51(1) (2018-01), ISTQB CT-AI Syllabus v1.0 (2021-10-01) | 문서 근거 |
| 2026-10-03 | [차분 프라이버시(Differential Privacy) — 프라이버시 손실 매개변수 ε과 누적 손실](posts/PE/security/2026-10-03-differential-privacy-epsilon-composition/index.md) | 중급 | NIST SP 800-226 (2025-03), Python 3.13.5 | 실행 검증 |
| 2026-10-03 | [DevOps 파이프라인 구성요소와 DORA 지표 — 지표마다 재는 구간](posts/PE/software-engineering/2026-10-03-devops-pipeline-dora-metrics/index.md) | 중급 | DORA software delivery metrics 가이드 (2026-01-05 갱신), Fowler, Continuous Integration (2024-01-18 갱신), Humble, continuousdelivery.com (2026-10 열람) | 문서 근거 |
| 2026-10-03 | [소프트웨어 품질 비용(COQ)과 결함 제거 효율](posts/PE/software-engineering/2026-10-03-cost-of-quality-defect-removal-efficiency/index.md) | 중급 | Python 3.13.5, SWEBOK V3.0 (2014), Capers Jones, Software Defect Removal Efficiency (2011) | 실행 검증 |
| 2026-10-02 | [사가(Saga) 패턴 — 분산 트랜잭션 대신 보상 트랜잭션](posts/PE/software-engineering/2026-10-02-saga-pattern-compensating-transaction/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Garcia-Molina & Salem, Sagas (SIGMOD 1987), Microsoft Azure Architecture Center, Saga design pattern (2025-02-25) | 실행 검증 |
| 2026-10-02 | [GoF 디자인 패턴 23개의 3분류](posts/PE/software-engineering/2026-10-02-gof-design-patterns-three-purposes/index.md) | 중급 | Gamma·Helm·Johnson·Vlissides, Design Patterns (Addison-Wesley, 1994) | 문서 근거 |
| 2026-10-02 | [재해복구 전략 — RTO·RPO·MTD와 4가지 복구 방식](posts/PE/system/2026-10-02-disaster-recovery-mtd-rto-rpo-strategies/index.md) | 중급 | NIST SP 800-34 Rev.1 (2010-05), AWS Disaster Recovery of Workloads on AWS (2021-02), Azure Well-Architected Framework RE:09 (2026-08 갱신) | 문서 근거 |
| 2026-10-02 | [클린 아키텍처와 헥사고날 아키텍처](posts/PE/software-engineering/2026-10-02-clean-vs-hexagonal-architecture/index.md) | 중급 | Python 3.13.5, Cockburn, Hexagonal Architecture (2005), Martin, The Clean Architecture (2012) | 실행 검증 |
| 2026-10-02 | [AI 통제(AI Control) — 오정렬을 전제로 에이전트를 감독하는 설계](posts/PE/security/2026-10-02-ai-control-untrusted-model-oversight/index.md) | 중급 | Greenblatt et al., AI Control (ICML 2024, arXiv 2312.06942v5), Korbak et al., A sketch of an AI control safety case (arXiv 2501.17315, 2025-01), OpenAI Preparedness Framework v2 (2025-04-15), International AI Safety Report 2026 (2026-02-03) | 문서 근거 |
| 2026-10-01 | [PMBOK 지식 영역과 프로세스 그룹](posts/PE/it-management/2026-10-01-pmbok-knowledge-areas-process-groups/index.md) | 중급 | PMBOK Guide 6th Edition (2017), PMBOK Guide 7th Edition (2021), PMBOK Guide 8th Edition (2025), PMI Process Groups: A Practice Guide (2022) | 문서 근거 |
| 2026-10-01 | [패킷 스케줄링 기법 — PQ·WRR·DRR·WFQ](posts/PE/network/2026-10-01-packet-scheduling-pq-wrr-drr-wfq/index.md) | 중급 | Shreedhar & Varghese, DRR, ACM SIGCOMM 1995, Parekh & Gallager, GPS, IEEE/ACM ToN 1993, Katevenis et al., WRR, IEEE JSAC 1991, Cisco IOS 12.2SR QoS Configuration Guide, Python 3.13.5 | 실행 검증 |
| 2026-10-01 | [GPU 클러스터 인터커넥트 — NVLink·InfiniBand·RoCE](posts/PE/network/2026-10-01-gpu-cluster-interconnect-nvlink-infiniband-roce/index.md) | 심화 | NVIDIA DGX SuperPOD Reference Architecture H100 · GB200 (2025-11 갱신), IBTA RoCEv2 Annex A17 (2014), Guo et al., RDMA over Commodity Ethernet at Scale, SIGCOMM 2016, Narayanan et al., Megatron-LM, SC21 | 문서 근거 |
| 2026-10-01 | [프런티어 AI 안전 프레임워크 — 역량 임계치와 안전장치로 배포를 정하는 구조](posts/PE/security/2026-10-01-frontier-ai-safety-frameworks/index.md) | 중급 | OpenAI Preparedness Framework v2 (2025-04-15), Google DeepMind Frontier Safety Framework 3.1 (2026-04-17), Anthropic Responsible Scaling Policy 3.4 (2026-07-08), 인공지능 기본법 법률 제20676호 (2026-01-22 시행) | 문서 근거 |
| 2026-10-01 | [애자일과 폭포수 — 무엇을 기준으로 고르는가](posts/PE/software-engineering/2026-10-01-agile-vs-waterfall-selection-criteria/index.md) | 중급 | IEEE Std 610.12-1990, Royce (1970) WESCON, Boehm·Turner (2003) IEEE Computer 36(6), 애자일 선언문 (2001), 소프트웨어 진흥법 (2020-12-10 시행) | 문서 근거 |
| 2026-10-01 | [능동 큐 관리(AQM) — RED와 CoDel](posts/PE/network/2026-10-01-active-queue-management-red-codel/index.md) | 중급 | Floyd & Jacobson, RED, IEEE/ACM ToN 1993, RFC 7567 (BCP 197, 2015-07), RFC 8289 (2018-01), Python 3.13.5 | 실행 검증 |
| 2026-09-30 | [오픈웨이트 모델과 오픈소스 AI 정의(OSAID 1.0)](posts/PE/emerging-tech/2026-09-30-open-weight-vs-osaid/index.md) | 중급 | OSI Open Source AI Definition 1.0 (2024-10-28), OSI Open Source Definition 1.9, EU AI Act (Regulation (EU) 2024/1689), Llama 3.1 Community License (2024-07-23), Model Openness Framework v6 (2024-10) | 문서 근거 |
| 2026-09-30 | [머신러닝 모델 평가 지표 — 혼동행렬에서 정밀도와 재현율이 갈리는 곳](posts/PE/emerging-tech/2026-09-30-ml-evaluation-metrics-confusion-matrix/index.md) | 중급 | Python 3.13.5, scikit-learn 1.9.1 문서, Google Machine Learning Crash Course (2026-09-30 열람) | 실행 검증 |
| 2026-09-30 | [LLM 분산 학습 병렬화 — 데이터·텐서·파이프라인 병렬](posts/PE/system/2026-09-30-llm-parallelism-data-tensor-pipeline/index.md) | 중급 | Narayanan et al., Megatron-LM, SC21 (arXiv 2104.04473), Rajbhandari et al., ZeRO, SC20 (arXiv 1910.02054) | 문서 근거 |
| 2026-09-30 | [ISO/IEC 5259 — 분석·머신러닝용 데이터 품질 표준 시리즈](posts/PE/data-analysis/2026-09-30-iso-iec-5259-data-quality-series/index.md) | 중급 | ISO/IEC 5259-1:2024, ISO/IEC 5259-2:2024, ISO/IEC 5259-3:2024, ISO/IEC 5259-4:2024, ISO/IEC 5259-5:2025 | 문서 근거 |
| 2026-09-30 | [컨테이너와 가상머신 — 격리 수준의 차이](posts/PE/emerging-tech/2026-09-30-container-vs-vm-isolation/index.md) | 중급 | NIST SP 800-125 (2011-01), NIST SP 800-190 (2017-09), Linux man-pages 6.19 (2026-02-08) | 문서 근거 |
| 2026-09-30 | [클라우드 서비스 모델과 책임 공유](posts/PE/emerging-tech/2026-09-30-cloud-service-models-shared-responsibility/index.md) | 입문 | NIST SP 800-145 (2011-09), NIST SP 800-146 (2012-05), Microsoft Learn Shared responsibility in the cloud (2026-08-24), AWS Shared Responsibility Model (2026-09 확인) | 문서 근거 |
| 2026-09-30 | [블록체인 합의 알고리즘 — PoW, PoS, PBFT](posts/PE/emerging-tech/2026-09-30-blockchain-consensus-pow-pos-pbft/index.md) | 심화 | NIST IR 8202 (2018-10), Bitcoin 백서 (2008), Castro·Liskov PBFT (OSDI 1999), Python 3.13.5 | 실행 검증 |
| 2026-09-30 | [AI-BOM — SPDX 3.0 AI 프로필과 CycloneDX ML-BOM](posts/PE/software-engineering/2026-09-30-ai-bom-spdx-cyclonedx/index.md) | 중급 | SPDX 3.0.1 (2024), CycloneDX 1.6 = ECMA-424 1판 (2024-06), NTIA SBOM Minimum Elements (2021-07) | 문서 근거 |
| 2026-09-29 | [WBS와 범위 기준선 — 100% 규칙, 작업 패키지, 통제 계정](posts/PE/it-management/2026-09-29-wbs-scope-baseline-control-account/index.md) | 중급 | ISO 21511:2018, NASA/SP-2016-3404/REV1 (2018-01), DoD EVMSIG (2019-03-14), PMI Lexicon of Project Management Terms 4.0 (2024) | 문서 근거 |
| 2026-09-29 | [대칭키와 공개키 — 쓰임이 갈리는 지점](posts/PE/security/2026-09-29-symmetric-vs-public-key-hybrid/index.md) | 입문 | NIST SP 800-57 Part 1 Rev. 5 (2020-05), RFC 9180 (2022-02), Diffie·Hellman, IEEE Trans. IT-22(6) (1976-11) | 문서 근거 |
| 2026-09-29 | [서버리스 컴퓨팅 — FaaS·BaaS와 콜드 스타트](posts/PE/cloud/2026-09-29-serverless-computing-faas-baas/index.md) | 중급 | CNCF Serverless Whitepaper v1.0 (2018-02), UC Berkeley EECS-2019-3 (2019-02), AWS Lambda Developer Guide (2026-09 확인) | 문서 근거 |
| 2026-09-29 | [프로세스와 스레드 — 문맥 교환 비용](posts/PE/system/2026-09-29-process-thread-context-switch-cost/index.md) | 입문 | IEEE Std 1003.1-2024 (POSIX.1-2024), Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018), Linux man-pages — pthreads(7)·proc_pid_status(5), 2026-09-29 조회 | 문서 근거 |
| 2026-09-29 | [오픈소스 라이선스 컴플라이언스 — ISO/IEC 5230(OpenChain)과 라이선스 유형](posts/PE/it-management/2026-09-29-open-source-license-compliance-iso-5230/index.md) | 중급 | ISO/IEC 5230:2020 (OpenChain 2.1), GPL-3.0 · AGPL-3.0 (2007), MPL-2.0 (2012), Apache-2.0 (2004) | 문서 근거 |
| 2026-09-29 | [침해사고 대응 절차 6단계](posts/PE/security/2026-09-29-incident-response-six-phases/index.md) | 중급 | NIST SP 800-61r2 (2012-08), NIST SP 800-61r3 (2025-04), SANS Incident Handler's Handbook (2012-02), ISO/IEC 27035-1:2023 | 문서 근거 |
| 2026-09-29 | [컨텍스트 엔지니어링 — 추론 시점에 모델에 들어가는 토큰을 고르는 기술](posts/PE/emerging-tech/2026-09-29-context-engineering-token-curation/index.md) | 중급 | A Survey of Context Engineering arXiv:2507.13334v2 (2025-07), Claude Docs Context windows · Context editing (2026-09 조회), Anthropic Engineering (2025-09-29), LangChain Blog (2025-07-02), Manus Blog (2025-07-18) | 문서 근거 |
| 2026-09-29 | [접근통제 모델 — DAC, MAC, RBAC, ABAC](posts/PE/security/2026-09-29-access-control-dac-mac-rbac-abac/index.md) | 중급 | DoD 5200.28-STD TCSEC (1985-12), NIST SP 800-162 (2014-01, 2019-08 갱신), ANSI INCITS 359-2004 | 문서 근거 |
| 2026-09-28 | [TCP 3-way 핸드셰이크와 흐름·혼잡 제어](posts/PE/network/2026-09-28-tcp-handshake-flow-congestion-control/index.md) | 중급 | RFC 9293 (2022-08, STD 7), RFC 5681 (2009-09), RFC 9438 (2023-08), RFC 1122 (1989-10) | 문서 근거 |
| 2026-09-28 | [SDN과 NFV — 제어와 데이터 평면 분리](posts/PE/network/2026-09-28-sdn-nfv-control-data-plane/index.md) | 심화 | RFC 7426 (2015-01), ETSI GS NFV 002 V1.2.1 (2014-12), ETSI GS NFV 003 V1.2.1 (2014-12) | 문서 근거 |
| 2026-09-28 | [라우팅 프로토콜 — 거리벡터와 링크상태](posts/PE/network/2026-09-28-routing-distance-vector-vs-link-state/index.md) | 중급 | RFC 2453 (1998-11, STD 56), RFC 2328 (1998-04, STD 54), Python 3.13.5 | 실행 검증 |
| 2026-09-28 | [OSI 7계층과 TCP/IP 4계층 대응](posts/PE/network/2026-09-28-osi-7-layer-vs-tcpip-4-layer/index.md) | 입문 | ITU-T X.200 (07/1994) = ISO/IEC 7498-1:1994, RFC 1122 (1989-10, STD 3), RFC 1812 (1995-06), RFC 8446 (2018-08) | 문서 근거 |
| 2026-09-28 | [비인간 신원(NHI)과 워크로드 신원 관리](posts/PE/security/2026-09-28-non-human-identity-workload-identity/index.md) | 중급 | OWASP NHI Top 10 (2025), NIST SP 800-207A (2023-09), IETF draft-ietf-wimse-arch-08 (2026-07), RFC 6750 (2012-10), RFC 9449 (2023-09) | 문서 근거 |
| 2026-09-28 | [선로 부호화(Line Coding) — NRZ·NRZI·맨체스터·차등 맨체스터·4B5B](posts/PE/network/2026-09-28-line-coding-schemes/index.md) | 중급 | IEEE 802.3cg Draft D2.0 Clause 147 (2018-09), Intel UTMI Specification 1.05 (2001), Python 3.13.5 | 실행 검증 |
| 2026-09-28 | [하네스 엔지니어링 — 가이드·센서·세션 밖 상태로 에이전트를 통제하는 구조](posts/PE/emerging-tech/2026-09-28-harness-engineering-guides-sensors/index.md) | 중급 | martinfowler.com Harness engineering (2026-04-02), Anthropic Engineering (2025-11-26), Google Developers Blog (2026-09-09), Anthropic Engineering context engineering (2025-09-29) | 문서 근거 |
| 2026-09-28 | [디지털 포렌식 절차와 증거 무결성](posts/PE/security/2026-09-28-digital-forensics-process-evidence-integrity/index.md) | 중급 | NIST SP 800-86 (2006-08), ISO/IEC 27037:2012, ISO/IEC 27043:2015, RFC 3227 (2002-02) | 문서 근거 |
| 2026-09-23 | [프로세스 상태 전이 모델 — 5상태와 대기 큐](posts/PE/system/2026-09-23-process-state-transition-model/index.md) | 중급 | Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018), Stallings, Operating Systems: Internals and Design Principles §3.2, IEEE Std 1003.1-2024 (POSIX.1-2024), Linux man-pages — proc_pid_stat(5)·proc_loadavg(5), 2026-09-23 조회 | 문서 근거 |
| 2026-09-23 | [Physical AI — 인지·추론·행동 순환과 시뮬레이션 기반 학습](posts/PE/emerging-tech/2026-09-23-physical-ai-perception-action-loop/index.md) | 중급 | RT-2 arXiv:2307.15818 (2023-07), GR00T N1 arXiv:2503.14734 (2025-03), Tobin et al. arXiv:1703.06907 (2017-03), WEF Physical AI White Paper (2025-09), ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-23 | [정규화 1NF부터 BCNF까지](posts/PE/database/2026-09-23-normalization-1nf-to-bcnf/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Windows 11 | 실행 검증 |
| 2026-09-23 | [분산 데이터베이스 — 투명성 6가지](posts/PE/database/2026-09-23-distributed-database-transparency/index.md) | 심화 | Özsu & Valduriez, IEEE Computer 24(8) 1991, Oracle Database 19c 문서, Oracle Database 11g R2 문서 | 문서 근거 |
| 2026-09-23 | [데이터 모델링 3단계 — 개념·논리·물리](posts/PE/database/2026-09-23-data-modeling-three-stages/index.md) | 입문 | FIPS PUB 184 (IDEF1X, 1993), ISO/IEC/IEEE 31320-2:2012, Oracle SQL Developer Data Modeler 23.1 문서, Oracle Database 19c 문서 | 문서 근거 |
| 2026-09-23 | [트랜잭션 ACID와 격리 수준 — 이상현상으로 수준을 정의하는 방식](posts/PE/database/2026-09-23-acid-and-isolation-levels/index.md) | 중급 | PostgreSQL 16 문서, Berenson et al., SIGMOD 1995 | 문서 근거 |
| 2026-09-22 | [SQuaRE 표준군 구조 — 5개 부문과 확장 부문, 그리고 품질 모델 4종](posts/PE/software-engineering/2026-09-22-square-standard-family-structure/index.md) | 중급 | ISO/IEC 25000:2014 (2판), ISO/IEC 25002:2024 (1판), ISO/IEC 25010:2023 (2판), ISO/IEC 25019:2023 (1판) | 문서 근거 |
| 2026-09-22 | [MSA — 분해 기준과 감당해야 할 비용](posts/PE/software-engineering/2026-09-22-msa-decomposition-and-cost/index.md) | 심화 | NIST SP 800-204 (2019-08) | 문서 근거 |
| 2026-09-22 | [형상관리 — 4대 활동과 베이스라인](posts/PE/software-engineering/2026-09-22-configuration-management-baseline/index.md) | 중급 | ISO/IEC TR 19759:2016 (SWEBOK V3.0), ISO/IEC/IEEE 24765:2017, IEEE 828-2012 | 문서 근거 |
| 2026-09-22 | [CMMI 성숙도 레벨과 프랙티스 영역 — 0단계부터 5단계까지](posts/PE/software-engineering/2026-09-22-cmmi-maturity-levels/index.md) | 중급 | CMMI V3.0 (2023), CMMI V2.0 (2018), ISO/IEC 33001:2015, ISO/IEC 33004:2015 | 문서 근거 |
| 2026-09-22 | [부트스트랩 재표집 — 복원추출로 추정량의 분포를 세우는 절차](posts/PE/data-analysis/2026-09-22-bootstrap-resampling/index.md) | 중급 | Python 3.13.5, Efron, Ann. Statist. 7(1), 1979, Efron & Narasimhan, 2018 preprint | 실행 검증 |
| 2026-09-22 | [BM25 — 확률적 적합성 프레임워크가 낳은 순위 함수와 두 매개변수](posts/PE/software-engineering/2026-09-22-bm25-probabilistic-relevance/index.md) | 중급 | Robertson & Zaragoza, FnTIR 3(4), 2009, Apache Lucene 10.3.1, Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [근사 최근접 이웃 탐색과 HNSW 색인 — 정확한 답을 포기하고 얻는 것](posts/PE/database/2026-09-22-approximate-nearest-neighbor-hnsw/index.md) | 중급 | Python 3.13.5, Malkov & Yashunin, arXiv:1603.09320v4 (2018), pgvector 0.8.6 | 실행 검증 |
| 2026-09-22 | [애자일과 DevOps — 무엇이 같고 무엇이 다른가](posts/PE/software-engineering/2026-09-22-agile-and-devops-scope/index.md) | 중급 | ISO/IEC/IEEE 32675:2022, IEEE Std 2675-2021, 애자일 선언문 (2001), Scrum Guide 2020 | 문서 근거 |
| 2026-09-21 | [테스트 레벨과 테스트 기법 분류](posts/PE/software-engineering/2026-09-21-test-levels-and-techniques/index.md) | 중급 | ISTQB CTFL Syllabus v4.0.1 (2024-09-15), Python 3.13.5 | 실행 검증 |
| 2026-09-21 | [품질속성 시나리오와 유틸리티 트리](posts/PE/software-engineering/2026-09-21-quality-attribute-scenario-utility-tree/index.md) | 중급 | CMU/SEI-2000-TR-004 (2000.8), CMU/SEI-2003-TR-016 (2003.8) | 문서 근거 |
| 2026-09-21 | [정보시스템 감리 — 제3자 점검이 법으로 자리 잡은 구조](posts/PE/it-management/2026-09-21-information-system-audit/index.md) | 중급 | 전자정부법 (법률 제21394호, 2026.2.27. 일부개정), 전자정부법 시행령 (대통령령 제36605호, 2026.8.25. 일부개정), 정보시스템 감리기준 (행정안전부고시 제2024-53호, 2024.6.27.) | 문서 근거 |
| 2026-09-21 | [다크 팩토리 — 무인화가 성립하기 위한 전제](posts/PE/emerging-tech/2026-09-21-dark-factory-prerequisites/index.md) | 중급 | acatech Industrie 4.0 Maturity Index (2017, UPDATE 2020), IEC 62264-1:2013, ISO 13374-1:2003, ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-21 | [결합도와 응집도 — 등급별 판별 기준](posts/PE/software-engineering/2026-09-21-coupling-and-cohesion-levels/index.md) | 입문 | ISO/IEC/IEEE 24765:2017, ISO/IEC TR 19759:2016 (SWEBOK V3) | 문서 근거 |
| 2026-09-21 | [업무 프로세스 재설계(BPR) — 원안과 AI 도입 이후](posts/PE/it-management/2026-09-21-bpr-reengineering-and-ai/index.md) | 중급 | Hammer & Champy, Reengineering the Corporation (1993), Process Mining Manifesto (LNBIP 99, 2012), IEEE 1849-2016 (XES), ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023) | 문서 근거 |
| 2026-09-18 | [소프트웨어 아키텍처 4+1 뷰](posts/PE/software-engineering/2026-09-18-software-architecture-4plus1-views/index.md) | 중급 | IEEE Software 12(6) 1995, ISO/IEC/IEEE 42010:2022 | 문서 근거 |
| 2026-09-18 | [요구공학 — 도출부터 검증까지 4단계](posts/PE/software-engineering/2026-09-18-requirements-engineering-four-phases/index.md) | 중급 | SWEBOK Guide V3.0, ISO/IEC/IEEE 29148:2018 | 문서 근거 |

## 리눅스 (linux) — 18편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-15 | [ssh_config — 별칭, 점프 호스트, 포워딩이 실제로 풀리는 값](posts/Infra/linux/2026-10-15-ssh-config-host-alias-forwarding/index.md) | 중급 | OpenSSH_10.3p1, OpenSSL 3.5.6, GNU bash 5.3.9 (Git Bash on Windows 11) | 실행 검증 |
| 2026-10-13 | [locale과 iconv — 한글이 깨질 때](posts/Infra/linux/2026-10-13-locale-iconv-sort-encoding/index.md) | 중급 | GNU bash 5.3.9 (Git Bash on Windows 11), Cygwin locale 3.6.7, GNU libiconv 1.19, GNU coreutils 8.32 (sort, wc, cut, od) | 실행 검증 |
| 2026-10-12 | [tail -f와 -F — 로테이션 뒤에도 로그를 놓치지 않기](posts/Linux/command/2026-10-12-tail-follow-log-rotation/index.md) | 입문 | GNU coreutils tail 8.32, GNU grep 3.0, GNU bash 5.3.9 (Git Bash on Windows 11) | 실행 검증 |
| 2026-10-08 | [time으로 재는 세 가지 — real, user, sys](posts/Infra/linux/2026-10-08-time-real-user-sys/index.md) | 중급 | GNU bash 5.3.9 (Git Bash on Windows 11), GNU coreutils 8.32 (sha256sum, dd, sleep), Cygwin runtime 3.6.7 | 실행 검증 |
| 2026-10-07 | [split과 csplit — 큰 파일 쪼개기](posts/Infra/linux/2026-10-07-split-csplit-large-file/index.md) | 중급 | GNU coreutils 8.32 (split, csplit), bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-10-06 | [kill과 시그널 — TERM, KILL, HUP의 차이](posts/Linux/command/2026-10-06-kill-signals-term-kill-hup/index.md) | 중급 | GNU bash 5.3.9 (Git Bash on Windows 11), GNU coreutils 8.32 (timeout), Cygwin runtime 3.6.7 | 실행 검증 |
| 2026-10-06 | [diff와 patch — 설정 변경을 추적하기](posts/Infra/linux/2026-10-06-diff-patch-config-change-tracking/index.md) | 중급 | GNU diffutils 3.12, GNU patch 2.7.6, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-10-03 | [curl — API 디버깅에 필요한 옵션](posts/Linux/command/2026-10-03-curl-api-debugging-options-timing/index.md) | 입문 | curl 8.19.0 (Schannel), Python 3.13.5, OpenSSL 3.5.6 (2026-04-07), GNU bash 5.3.9 (Git Bash on Windows 11) | 실행 검증 |
| 2026-10-02 | [openssl s_client — 인증서 확인과 만료 점검](posts/Linux/command/2026-10-02-openssl-s-client-cert-chain-expiry/index.md) | 중급 | OpenSSL 3.5.6 (2026-04-07), GNU bash 5.3.9 (Git Bash on Windows 11) | 실행 검증 |
| 2026-10-01 | [환경변수와 셸 초기화 순서](posts/Linux/command/2026-10-01-bash-startup-files-env-vars/index.md) | 중급 | GNU bash 5.3.9 (Git Bash), GNU coreutils env 8.32, Windows 11 | 실행 검증 |
| 2026-09-30 | [tar와 gzip — 압축과 해제, 그리고 옵션 순서](posts/Linux/command/2026-09-30-tar-gzip-options-absolute-path/index.md) | 입문 | GNU tar 1.35, gzip 1.14, GNU bash 5.3.9 (Git Bash), Windows 11 | 실행 검증 |
| 2026-09-29 | [cut, paste, tr — 텍스트를 칼럼으로 다루기](posts/Infra/linux/2026-09-29-cut-paste-tr-columns/index.md) | 중급 | GNU coreutils 8.32 (cut, paste, tr), bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-28 | [xargs — 파이프로 인자를 넘기는 법](posts/Linux/command/2026-09-28-xargs-args-parallel-null/index.md) | 중급 | GNU findutils 4.10.0 (xargs), GNU bash 5.3.9 (Git Bash), Windows 11 | 실행 검증 |
| 2026-09-28 | [sort, uniq, wc — 텍스트 집계 조합](posts/Linux/command/2026-09-28-sort-uniq-wc-aggregation/index.md) | 입문 | GNU coreutils 8.32 (sort, uniq, wc), bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-23 | [sed — 파일 일괄 치환을 안전하게 하는 법](posts/Linux/command/2026-09-23-sed-safe-bulk-replace/index.md) | 중급 | GNU sed 4.9, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-22 | [grep — 로그에서 원하는 줄만 뽑기](posts/Linux/command/2026-09-22-grep-context-and-pcre/index.md) | 입문 | GNU grep 3.0, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-22 | [awk — 로그를 표로 집계하기](posts/Linux/command/2026-09-22-awk-log-aggregation/index.md) | 중급 | GNU Awk 5.4.0, bash 5.3.9, Windows 11 | 실행 검증 |
| 2026-09-21 | [TLS 핸드셰이크에서 실제로 오가는 것](posts/Infra/tls/2026-09-21-tls-handshake-openssl/index.md) | 중급 | OpenSSL 3.5.6 (2026-04-07), Git Bash on Windows 11, Python 3.13.5 | 실행 검증 |

## 일반 (general) — 32편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-23 | [자바스크립트 이벤트 루프에서 마이크로태스크가 먼저인 이유](posts/Language/javascript/2026-10-23-microtask-before-macrotask/index.md) | 중급 | Node.js v24.19.0, V8 13.6.233.17-node.51, Windows 11 | 실행 검증 |
| 2026-10-23 | [제너레이터가 실제로 아끼는 것 — tracemalloc 으로 본 메모리](posts/Performance/python/2026-10-23-generator-memory-tracemalloc/index.md) | 중급 | Python 3.13.5, CPython 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-23 | [압축 알고리즘 고르기 — gzip·bzip2·lzma 를 같은 데이터로 대조](posts/Performance/compression/2026-10-23-compression-gzip-bzip2-lzma/index.md) | 중급 | Python 3.13.5, zlib 1.3.1, Windows 11 | 실행 검증 |
| 2026-10-21 | [GC 로그에서 실제로 봐야 할 지표 — 할당률과 승격률로 힙을 역산한다](posts/Performance/java/2026-10-21-java8-gc-log-allocation-promotion-rate/index.md) | 심화 | Java 1.8.0_491 (HotSpot 25.491-b10), javac 1.8.0_202, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-19 | [이벤트 소싱이 감당해야 하는 진짜 비용](posts/Architecture/2026-10-19-event-sourcing-replay-cost/index.md) | 심화 | Python 3.13.5, SQLite 3.49.1, Windows 11 | 실행 검증 |
| 2026-10-17 | [아웃박스 패턴 없이 이벤트가 유실되는 경로](posts/Backend/kafka/2026-10-17-outbox-pattern-dual-write-loss/index.md) | 심화 | Python 3.13.5, SQLite 3.49.1 | 실행 검증 |
| 2026-10-16 | [SQL 인젝션은 이스케이프가 아니라 바인딩으로 막는다](posts/Security/2026-10-16-sql-injection-binding-not-escaping/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [git rebase와 merge가 만드는 히스토리의 차이](posts/Tooling/git/2026-10-16-git-rebase-merge-history/index.md) | 입문 | git 2.54.0.windows.1 | 실행 검증 |
| 2026-10-16 | [벤치마크가 거짓말하는 다섯 가지 방식](posts/Performance/2026-10-16-benchmark-five-lies/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-16 | [async/await가 숨기고 있는 상태 머신](posts/Language/python/2026-10-16-async-await-state-machine/index.md) | 심화 | CPython 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-15 | [타임아웃을 계층마다 다르게 줘야 하는 이유](posts/Backend/2026-10-15-timeout-budget-per-layer/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-15 | [p99가 평균보다 훨씬 나쁜 이유 — 큐잉 이론 최소한](posts/Performance/2026-10-15-p99-queueing-theory-utilization/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-15 | [캐시 스탬피드를 막는 세 가지 방법 비교](posts/Backend/2026-10-15-cache-stampede-three-strategies/index.md) | 심화 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-14 | [커넥션 풀은 왜 크게 잡을수록 느려지는가](posts/Backend/2026-10-14-connection-pool-size-littles-law/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-13 | [파티셔닝이 항상 빨라지지 않는 이유 — 프루닝이 깨진 뒤에 남는 비용](posts/Database/2026-10-13-partition-pruning-global-index-cost/index.md) | 심화 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-13 | [낙관적 잠금과 비관적 잠금 — 벽시계로는 안 갈리고, 버린 일로 갈린다](posts/Backend/2026-10-13-optimistic-vs-pessimistic-locking-crossover/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-12 | [HTTP Keep-Alive를 껐다 켰을 때 실제로 달라지는 것](posts/Backend/2026-10-12-http-keep-alive-connection-count/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-08 | [서킷 브레이커의 3상태는 각각 어떤 장애를 막는가](posts/Backend/2026-10-08-circuit-breaker-three-states/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-07 | [옵티마이저 힌트를 쓰기 전에 확인할 3가지 — 통계·데이터·스키마](posts/Database/2026-10-07-optimizer-hint-three-checks/index.md) | 심화 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [재시도에 지수 백오프와 지터가 둘 다 필요한 이유](posts/Backend/2026-10-06-retry-backoff-jitter/index.md) | 중급 | Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-06 | [멱등키(Idempotency Key)로 중복 결제를 막는 설계](posts/Backend/2026-10-06-idempotency-key-duplicate-payment/index.md) | 중급 | Python 3.13.5, SQLite 3.49.1, Windows 11 | 실행 검증 |
| 2026-10-03 | [NULL이 인덱스, 집계, 비교에서 각각 다르게 동작하는 이유](posts/Database/2026-10-03-null-index-group-unique-distinct/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-02 | [WAL은 왜 데이터 파일보다 먼저 쓰이는가](posts/Database/sqlite/2026-10-02-sqlite-wal-frames-before-data-file/index.md) | 심화 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-10-01 | [N+1 쿼리는 왜 반복해서 생기고 어떻게 잡아내는가](posts/Database/2026-10-01-n-plus-one-query-detection/index.md) | 입문 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-30 | [실행계획의 비용(cost)은 무엇을 세는 숫자인가](posts/Database/2026-09-30-optimizer-cost-stale-statistics/index.md) | 심화 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [데드락은 어떻게 만들어지고 SQLite는 누구에게 BUSY를 돌려주는가](posts/Database/2026-09-29-sqlite-deadlock-busy-victim/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-29 | [커서 기반 페이지네이션이 OFFSET을 이기는 지점 — SQLite 3.49.1로 잰 깊이별 비용](posts/Database/sqlite/2026-09-29-keyset-vs-offset-crossover/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-28 | [MVCC는 왜 읽기 잠금을 없앴고 무엇을 대가로 치르는가 — SQLite WAL로 잰 비용](posts/Database/2026-09-28-mvcc-wal-long-reader-cost/index.md) | 심화 | SQLite 3.49.1, Python 3.13.5, Windows 11 | 실행 검증 |
| 2026-09-21 | [트랜잭션 격리 수준별로 실제 무슨 이상 현상이 보이는가](posts/Database/sqlite/2026-09-21-isolation-level-anomalies/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [git bisect로 버그가 들어온 커밋을 자동으로 찾기](posts/Tooling/git/2026-09-18-git-bisect-run-automation/index.md) | 중급 | git 2.54.0.windows.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [복합 인덱스의 컬럼 순서가 성능을 가르는 이유](posts/Database/sqlite/2026-09-18-composite-index-column-order/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |
| 2026-09-18 | [B-Tree 인덱스를 못 타는 조건들](posts/Database/sqlite/2026-09-18-btree-index-not-used/index.md) | 중급 | SQLite 3.49.1, Python 3.13.5 | 실행 검증 |

## 기출문제 (exam) — 68편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-25 | [기출문제 — ISO/IEC 42001:2023 인공지능 경영시스템](posts/PE/exam/2026-10-25-iso-iec-42001-ai-management-system/index.md) | 중급 | ISO/IEC 42001:2023 (제1판, 2023-12), ISO/IEC 42006:2025 (제1판, 2025-07), ISO/IEC 42005:2025, ISO/IEC 23894:2023, ISO/IEC 17021-1:2015 | 문서 근거 |
| 2026-10-25 | [기출문제 — 안면인식 결제 서비스](posts/PE/exam/2026-10-25-facial-recognition-payment-biometric-standards/index.md) | 중급 | ISO/IEC 2382-37:2022, ISO/IEC 19795-1:2021, ISO/IEC 30107-3:2023, ISO/IEC 24745:2022, 개인정보 보호법 시행령 제18조 | 문서 근거 |
| 2026-10-25 | [기출문제 — 선도개발을 위한 개발방법론 테일러링](posts/PE/exam/2026-10-25-development-methodology-tailoring/index.md) | 중급 | ISO/IEC/IEEE 12207:2017, 행정안전부고시 제2022-31호 행정기관 및 공공기관 정보시스템 구축·운영 지침 | 문서 근거 |
| 2026-10-25 | [기출문제 — 베이즈 정리](posts/PE/exam/2026-10-25-bayes-theorem/index.md) | 중급 | Python 3.13.5, NIST/SEMATECH e-Handbook of Statistical Methods §8.1.10 | 실행 검증 |
| 2026-10-24 | [기출문제 — 프로젝트 위험관리](posts/PE/exam/2026-10-24-project-risk-management-processes/index.md) | 중급 | PMBOK Guide 6th Edition (PMI, 2017), PMBOK Guide 8th Edition (PMI, 2025-11), ISO 31000:2018, ISO 21502:2020 | 문서 근거 |
| 2026-10-24 | [기출문제 — NIST AI RMF의 핵심구조 4가지와 신뢰 가능한 AI 특성 7가지](posts/PE/exam/2026-10-24-nist-ai-rmf-core-and-trustworthy-characteristics/index.md) | 중급 | NIST AI 100-1 AI RMF 1.0 (2023-01), ISO/IEC TS 5723:2022, ISO 9000:2015, NIST SP 1270 (2022-03) | 문서 근거 |
| 2026-10-23 | [기출문제 — 가상발전소 전력수요 예측의 AI 기법: 시계열 딥러닝·강화학습·그래프신경망](posts/PE/exam/2026-10-23-vpp-demand-forecasting-ai-techniques/index.md) | 심화 | Hochreiter & Schmidhuber, Neural Computation 9(8) (1997), Lim et al., Temporal Fusion Transformers, arXiv:1912.09363 (2019-12, v3 2020-09), Sutton & Barto, Reinforcement Learning: An Introduction 2nd ed. (2018), Kipf & Welling, ICLR 2017, Liao et al., JMPSCE 10(2) (2022), 분산에너지 활성화 특별법 (2024-06-14 시행) | 문서 근거 |
| 2026-10-23 | [기출문제 — 서브네팅과 슈퍼네팅, /22를 네 팀에 VLSM으로 나누기](posts/PE/exam/2026-10-23-subnetting-supernetting-vlsm/index.md) | 중급 | RFC 950 (1985), RFC 1338 (1992), RFC 1878 (1995), RFC 4632 (2006), Python 3.13.5 | 실행 검증 |
| 2026-10-22 | [기출문제 — 가상메모리 관리기법과 단편화](posts/PE/exam/2026-10-22-virtual-memory-management-fragmentation/index.md) | 중급 | Denning, Virtual Memory, ACM Computing Surveys 2(3), 1970, Randell, CACM 12(7), 1969, Bonwick, USENIX Summer 1994, Linux kernel 7.3.0 문서 (docs.kernel.org) | 문서 근거 |
| 2026-10-22 | [기출문제 — 재난·전쟁에 대비한 데이터센터 위치 선정과 대응전략](posts/PE/exam/2026-10-22-idc-site-selection-and-disaster-response/index.md) | 심화 | NIST SP 800-34 Rev.1 (2010-05, 2010-11 갱신), NIST SP 800-53 Rev.5 (2020-09), IBM DS8900F Documentation 9.4.0, 과학기술정보통신부고시 제2024-19호 (시행 2024-06-01) | 문서 근거 |
| 2026-10-21 | [기출문제 — 뮤텍스, 세마포어, 모니터](posts/PE/exam/2026-10-21-mutex-semaphore-monitor/index.md) | 중급 | IEEE Std 1003.1-2017 (POSIX.1-2017, Issue 7 2018 Edition), Dijkstra, EWD123 (1965), Hoare, CACM 17(10), 1974, Lampson·Redell, CACM 23(2), 1980, Java SE 21 JLS §17.1, Sha·Rajkumar·Lehoczky, IEEE TC 39(9), 1990 | 문서 근거 |
| 2026-10-21 | [기출문제 — 빅데이터 분석기법: 클러스터링, 필터링, 이상치 탐지](posts/PE/exam/2026-10-21-bigdata-clustering-filtering-outlier-detection/index.md) | 중급 | ISO/IEC 20546:2019, ISO 16269-4:2010, NIST SP 1500-6r2 (2019), Ester et al., KDD-96, Chandola et al., ACM CSUR 41(3), 2009, Sarwar et al., WWW10, 2001 | 문서 근거 |
| 2026-10-20 | [기출문제 — 이진 탐색 트리와 라우팅 테이블 탐색 알고리즘의 상관관계](posts/PE/exam/2026-10-20-bst-and-routing-table-lookup/index.md) | 심화 | RFC 1812 (1995-06), ACM SIGCOMM '97 Proceedings (1997), pp. 25-36, IEEE INFOCOM 1998 / IEEE/ACM Transactions on Networking (1999), IEEE JSAC Vol. 17 No. 6 (1999-06), Journal of the ACM Vol. 15 No. 4 (1968-10) | 문서 근거 |
| 2026-10-20 | [기출문제 — AI 학습용 데이터의 특성과 품질관리 지표, 품질관리 활동](posts/PE/exam/2026-10-20-ai-training-data-quality-indicators/index.md) | 중급 | NIA 인공지능 학습용 데이터 품질관리 가이드라인 v3.1 제2권 (2024-01), ISO/IEC 5259-2:2024, ISO/IEC 5259-4:2024, ISO/IEC 25024 | 문서 근거 |
| 2026-10-19 | [기출문제 — 소프트웨어 테스트 7대 원리와 동등 분할·경계값 분석 테스트 케이스 설계](posts/PE/exam/2026-10-19-test-principles-equivalence-boundary/index.md) | 중급 | ISTQB CTFL Syllabus v4.0.1 (2024-09-15), ISO/IEC/IEEE 29119-4:2021 (2판), Python 3.13.5 | 실행 검증 |
| 2026-10-16 | [기출문제 — 불명확한 요구사항이 만드는 품질저하를 기술부채·코드스멜·리팩토링으로 설명하기](posts/PE/exam/2026-10-16-unclear-requirements-debt-smell-refactoring/index.md) | 중급 | ISO/IEC/IEEE 29148:2018 (2판), ISO/IEC 25010:2023 (2판), Fowler, Refactoring 2nd ed. (2018), Cunningham, OOPSLA'92 Experience Report (1992) | 문서 근거 |
| 2026-10-16 | [기출문제 — 데이터분석에서 이상치와 편향](posts/PE/exam/2026-10-16-outlier-and-bias-in-data-analysis/index.md) | 중급 | Python 3.13.5, JCGM 200:2012 (국제 측정학 용어집 제3판), NIST/SEMATECH e-Handbook of Statistical Methods (2012), NIST SP 1270 (2022-03), ISO 16269-4:2010, ISO/IEC TR 24027:2021 | 실행 검증 |
| 2026-10-16 | [기출문제 — 다중 에이전트 시스템(MAS)의 정의·비교·효과](posts/PE/exam/2026-10-16-multi-agent-system-enterprise/index.md) | 중급 | FIPA Agent Management Specification SC00023K(2004-03-18, 표준), A2A Protocol Specification v1.0.0, Model Context Protocol 사양 개정판 2026-07-28, NIST COSAiS 프로젝트(개념 문서 2025-08-14, 페이지 갱신 2026-01-08) | 문서 근거 |
| 2026-10-15 | [기출문제 — 데이터 가치평가와 데이터 자산화](posts/PE/exam/2026-10-15-data-valuation-and-assetization/index.md) | 중급 | 데이터 산업진흥 및 이용촉진에 관한 기본법(2021년 제정, 2022.4.20. 시행), ISO/IEC 38505-1:2026(제2판), ISO/IEC 25012:2008, ISO/IEC 11179-1:2023(제4판), 데이터 가치평가 안내서(과학기술정보통신부·한국데이터산업진흥원, 2024) | 문서 근거 |
| 2026-10-14 | [기출문제 — 터보퀀트(TurboQuant) 벡터 양자화](posts/PE/exam/2026-10-14-turboquant-vector-quantization/index.md) | 심화 | Zandieh et al., arXiv:2504.19874v1 (2025-04-28), Google Research Blog (2026-03-24), Zandieh et al., QJL, AAAI 2025 (arXiv:2406.03482), Jégou et al., IEEE TPAMI 33(1), 2011 | 문서 근거 |
| 2026-10-14 | [기출문제 — 공공 SLA와 정보시스템 등급제](posts/PE/exam/2026-10-14-public-sla-and-system-grade/index.md) | 중급 | 행정기관 및 공공기관 정보시스템 안정성 고시(행정안전부고시 제2026-23호, 2026.4.13. 시행), 전자정부법(법률 제20654호, 2025.1.7. 일부개정) | 문서 근거 |
| 2026-10-13 | [기출문제 — 파인튜닝과 RAG, RLHF와 RAFT 학습 파이프라인 비교](posts/PE/exam/2026-10-13-finetuning-rag-rlhf-vs-raft/index.md) | 심화 | Ouyang et al., arXiv:2203.02155 (2022-03), Zhang et al., arXiv:2403.10131v2 (2024-06), Lewis et al., NeurIPS 2020, Hu et al., arXiv:2106.09685v2 (2021-10) | 문서 근거 |
| 2026-10-13 | [기출문제 — 데이터 레이크 아키텍처와 데이터 스웜프](posts/PE/exam/2026-10-13-data-lake-architecture-data-swamp/index.md) | 중급 | Sawadogo·Darmont, Journal of Intelligent Information Systems 56(1), 2021, NIST SP 1500-6r2 (2019-10), ISO/IEC 38505-1:2017, James Dixon 원 게시글 (2010-10-14) | 문서 근거 |
| 2026-10-12 | [기출문제 — AI 리스크: 개념, 보안·프라이버시·사회적 리스크](posts/PE/exam/2026-10-12-ai-risk-security-privacy-social/index.md) | 중급 | NIST AI 100-1 AI RMF 1.0 (2023-01), NIST AI 100-2 E2025 (2025-03), NIST AI 600-1 (2024-07), 개인정보보호위원회 AI 프라이버시 리스크 관리 모델 (2024-12-19 공개), International AI Safety Report 2026 (2026-02-03), 인공지능 기본법 법률 제21311호 | 문서 근거 |
| 2026-10-11 | [기출문제 — 양자머신러닝(QML)](posts/PE/exam/2026-10-11-quantum-machine-learning/index.md) | 심화 | Biamonte et al., Nature 549 (2017), Cerezo et al., Nature Reviews Physics 3 (2021), PennyLane 0.45.1 문서 | 문서 근거 |
| 2026-10-11 | [기출문제 — 개인정보보호를 위한 가명처리 기법](posts/PE/exam/2026-10-11-pseudonymization-techniques/index.md) | 중급 | 가명정보 처리 가이드라인 2022.4, ENISA Pseudonymisation techniques and best practices 2019.12, Python 3.13.5 | 실행 검증 |
| 2026-10-10 | [기출문제 — Wi-Fi 7(IEEE 802.11be)](posts/PE/exam/2026-10-10-wi-fi-7-ieee-802-11be/index.md) | 중급 | IEEE 802.11be-2024 (2024-09 승인, 2025-07 발행), Wi-Fi CERTIFIED 7 (Wi-Fi Alliance, 2024-01), Deng et al., arXiv:2007.13401v3 (2020-08) | 문서 근거 |
| 2026-10-10 | [기출문제 — 과적합과 과소적합의 발생 원인과 해결 방안](posts/PE/exam/2026-10-10-overfitting-underfitting-causes-remedies/index.md) | 중급 | Python 3.13.5, Goodfellow·Bengio·Courville, Deep Learning §5.2 (MIT Press, 2016), Google ML Crash Course Overfitting (2025) | 실행 검증 |
| 2026-10-10 | [기출문제 — 맥케이브 순환복잡도](posts/PE/exam/2026-10-10-mccabe-cyclomatic-complexity/index.md) | 중급 | Python 3.13.5, NIST SP 500-235 (1996), McCabe, IEEE TSE SE-2(4) (1976) | 실행 검증 |
| 2026-10-10 | [기출문제 — CTEM(지속적 위협 노출 관리)](posts/PE/exam/2026-10-10-continuous-threat-exposure-management/index.md) | 중급 | Gartner G00796532 (2023-10-16), IBM Think CTEM (2026-06-05), HackerOne CTEM Guide (2026-07-02), Infosecurity Europe CTEM (2026-08-14) | 문서 근거 |
| 2026-10-09 | [기출문제 — 소프트웨어 무중단 배포 방식: 롤링·블루그린·카나리](posts/PE/exam/2026-10-09-zero-downtime-deployment-strategies/index.md) | 중급 | Kubernetes v1.37 문서 (apps/v1 Deployment), Google SRE Workbook (2018), Fowler, BlueGreenDeployment (2010-03-01) | 문서 근거 |
| 2026-10-09 | [기출문제 — IT 프로젝트의 부정적 위험과 대응 전략 5가지](posts/PE/exam/2026-10-09-negative-risk-response-strategies/index.md) | 중급 | PMBOK Guide 6th ed. (PMI, 2017), ISO 31000:2018, NIST SP 800-39 (2011-03) | 문서 근거 |
| 2026-10-09 | [기출문제 — 엣지 컴퓨팅과 클라우드 컴퓨팅의 차이](posts/PE/exam/2026-10-09-edge-vs-cloud-computing/index.md) | 중급 | NIST SP 800-145 (2011-09), NIST SP 500-325 (2018-03), ETSI GS MEC 003 V2.2.1 (2020-12) | 문서 근거 |
| 2026-10-09 | [기출문제 — 분산 데이터베이스의 투명성](posts/PE/exam/2026-10-09-distributed-database-transparency/index.md) | 중급 | Özsu & Valduriez, IEEE Computer 24(8) 1991, Oracle Database 19c 관리자 안내서, Oracle Database 11g R2 관리자 안내서 | 문서 근거 |
| 2026-10-08 | [기출문제 — 대수의 법칙과 중심극한정리](posts/PE/exam/2026-10-08-law-of-large-numbers-central-limit-theorem/index.md) | 중급 | Python 3.13.5, Grinstead & Snell, Introduction to Probability 2nd ed. (AMS, 2003), NIST/SEMATECH e-Handbook §6.3.2.1 (2012) | 실행 검증 |
| 2026-10-08 | [기출문제 — AI 데이터센터, 기존 데이터센터와 무엇이 다른가](posts/PE/exam/2026-10-08-ai-data-center-vs-traditional/index.md) | 심화 | ISO/IEC 22237-1:2021, ISO/IEC 30134-2:2026, IEA Energy and AI (2025-04), Uptime Institute Global Data Center Survey 2024, ASHRAE TC 9.9 Liquid Cooling White Paper (2021-05), NVIDIA DGX SuperPOD Reference Architecture GB200 (2025-11), OCP Open Rack Base Frame V3 Specification (2022-08) | 문서 근거 |
| 2026-10-08 | [기출문제 — Advanced RAG와 Modular RAG 비교](posts/PE/exam/2026-10-08-advanced-rag-vs-modular-rag/index.md) | 중급 | Lewis et al., NeurIPS 2020, Gao et al., arXiv:2312.10997v5 (2024-03), Gao et al., arXiv:2407.21059v1 (2024-07) | 문서 근거 |
| 2026-10-07 | [기출문제 — 시계열 데이터의 이상치 유형, 탐지 방식, 딥러닝 기반 탐지 기법](posts/PE/exam/2026-10-07-time-series-anomaly-detection/index.md) | 중급 | Chandola et al., Anomaly Detection: A Survey, ACM CSUR 41(3), 2009, Blázquez-García et al., A Review on Outlier/Anomaly Detection in Time Series Data, ACM CSUR 54(3), 2021, Lai et al., Revisiting Time Series Outlier Detection, NeurIPS 2021 Datasets and Benchmarks, Darban et al., Deep Learning for Time Series Anomaly Detection: A Survey, arXiv:2211.05244v3 (2024), Hundman et al., KDD 2018, Kim et al., AAAI 2022 | 문서 근거 |
| 2026-10-07 | [기출문제 — 국내 규제에 따른 정보보호 컴플라이언스의 개념, 필요성, 대응 방안](posts/PE/exam/2026-10-07-information-security-compliance-korea/index.md) | 중급 | ISO 37301:2021, ISO/IEC 27001:2022, NIST CSWP 29 CSF 2.0 (2024-02-26), 정보통신망법 법률 제21500호 (2026-10-01 시행), 개인정보 보호법 (2023-09-15 시행 개정), ISMS-P 인증기준 101개 항목 | 문서 근거 |
| 2026-10-06 | [기출문제 — 소프트웨어 형상관리의 절차, 기준선, 도구](posts/PE/exam/2026-10-06-software-configuration-management-baseline-tools/index.md) | 중급 | ISO/IEC TR 19759:2016 (SWEBOK V3.0), ISO/IEC/IEEE 24765:2017, IEEE 828-2012, SEBoK v2.14 (2026-05), Pro Git 2판 (2014) | 문서 근거 |
| 2026-10-06 | [기출문제 — 표본추출의 절차, 확률·비확률 기법 비교, AI 학습데이터 구축에의 적용](posts/PE/exam/2026-10-06-sampling-ai-training-data/index.md) | 중급 | Statistics Canada, Survey Methods and Practices, Catalogue 12-587-X (2003), NIST/SEMATECH e-Handbook of Statistical Methods §3.3.3.3 (2012), AAPOR Task Force Report on Non-Probability Sampling (2013-06), Regulation (EU) 2024/1689 Art. 10, Gebru et al., Datasheets for Datasets, CACM 64(12), 2021, scikit-learn 1.9.1 User Guide §3.1 | 문서 근거 |
| 2026-10-05 | [기출문제 — 인공지능 기본법의 고영향 인공지능: 정의, 활용 영역, 사업자의 안전성·신뢰성 확보 활동](posts/PE/exam/2026-10-05-high-impact-ai-basic-act/index.md) | 심화 | 인공지능 기본법 법률 제21311호 (2026-01-20 일부개정), 인공지능 기본법 시행령 대통령령 제36580호 (2026-08-20 시행), Regulation (EU) 2024/1689 (AI Act), ISO/IEC 42001:2023, ISO/IEC 23894:2023, ISO/IEC 42005:2025 | 문서 근거 |
| 2026-10-05 | [기출문제 — 데이터 가치평가의 평가 요인, 방법론, 객관성을 정하는 핵심변수](posts/PE/exam/2026-10-05-data-valuation-factors-methods/index.md) | 중급 | 데이터 산업진흥 및 이용촉진에 관한 기본법 제14조 (2022-04-20 시행), 과기정통부 데이터 가치평가 안내서 (2024-07), OECD Digital Economy Papers No. 345 (2022-12), IVS 210 Intangible Assets (IVS 2022), ISO/IEC 25012:2008 | 문서 근거 |
| 2026-10-04 | [기출문제 — 무선 매체를 나눠 쓰는 세 방식 (CSMA/CA·CDMA·TDMA)](posts/PE/exam/2026-10-04-wireless-multiple-access-csma-ca-cdma-tdma/index.md) | 중급 | 3GPP TS 45.002 V13.2.0 (2016-08), 3GPP TS 25.213 V4.0.0 (2001-03), 3GPP TS 25.214 V5.3.0 (2002-12), Bianchi, IEEE JSAC Vol.18 No.3 (2000-03) | 문서 근거 |
| 2026-10-04 | [기출문제 — 블록·파일·오브젝트 스토리지 비교와 AI 학습 데이터·서비스 인프라 활용](posts/PE/exam/2026-10-04-block-file-object-storage-ai/index.md) | 중급 | NIST SP 800-209 (2020-10), Amazon S3 User Guide (2026-10 확인), Amazon FSx for Lustre User Guide (2026-10 확인), Google Cloud AI Hypercomputer 스토리지 가이드 (2026-10-02 갱신) | 문서 근거 |
| 2026-10-03 | [기출문제 — 합성데이터의 개념과 생성 기법, 품질 평가 지표](posts/PE/exam/2026-10-03-synthetic-data-generation-quality-metrics/index.md) | 중급 | 개인정보보호위원회 합성데이터 생성·활용 안내서 (2024-12), NIST SP 800-188 (2023-09), Alaa et al., ICML 2022 | 문서 근거 |
| 2026-10-03 | [기출문제 — AI 시스템 신뢰성과 메타모픽 테스트 (테스트 오라클 문제, 메타모픽 관계, 전통적 테스트와의 차이)](posts/PE/exam/2026-10-03-metamorphic-testing-ai-systems/index.md) | 중급 | ISO/IEC/IEEE 29119-4:2021, ISTQB CT-AI Syllabus v1.0 (2021-10-01), Chen et al., ACM Computing Surveys 51(1) (2018) | 문서 근거 |
| 2026-10-02 | [기출문제 — 클라우드 네이티브 환경의 재해복구 전략 (RTO·RPO, Active-Active·Active-Passive·Pilot Light)](posts/PE/exam/2026-10-02-disaster-recovery-rto-rpo-strategies/index.md) | 중급 | NIST SP 800-34 Rev.1 (2010-05), AWS Disaster Recovery of Workloads on AWS (2021-02), Azure Well-Architected Framework RE:09 (2026-08 갱신) | 문서 근거 |
| 2026-10-01 | [기출문제 — FIFO와 WFQ(Weighted Fair Queuing) 비교](posts/PE/exam/2026-10-01-fifo-vs-weighted-fair-queuing/index.md) | 중급 | Parekh & Gallager, GPS, IEEE/ACM ToN 1993, Demers·Keshav·Shenker, Fair Queueing, SIGCOMM 1989, RFC 7567 (2015-07), Cisco IOS 12.2SR QoS Configuration Guide, Python 3.13.5 | 실행 검증 |
| 2026-10-01 | [기출문제 — AI 보안: 사이버 공격 지원 위협과 자율성에 따른 통제 상실](posts/PE/exam/2026-10-01-ai-security-cyber-offense-loss-of-control/index.md) | 심화 | International AI Safety Report 2026 (2026-02-03), OpenAI Preparedness Framework v2 (2025-04-15), Google DeepMind Frontier Safety Framework v3 (2025-09-22), OWASP Top 10 for LLM Applications 2025, 인공지능 기본법 법률 제20676호 (2026-01-22 시행) | 문서 근거 |
| 2026-09-30 | [기출문제 — 인공지능 학습용 데이터 품질관리](posts/PE/exam/2026-09-30-ai-training-data-quality-management/index.md) | 중급 | NIA 인공지능 학습용 데이터 품질관리 가이드라인 v3.1 제2권 (2024-01), ISO/IEC 5259-4:2024, ISO/IEC 5259-1:2024, ISO/IEC 8183:2023 | 문서 근거 |
| 2026-09-30 | [기출문제 — AI 슈퍼컴퓨팅 플랫폼](posts/PE/exam/2026-09-30-ai-supercomputing-platform/index.md) | 심화 | Gartner Top Strategic Technology Trends for 2026 (2025-10), Jouppi et al., TPU v4, ISCA 2023, NVIDIA DGX SuperPOD Reference Architecture GB200 (2025-11), NIST SP 800-145 (2011-09) | 문서 근거 |
| 2026-09-29 | [기출문제 — 서버리스 컴퓨팅](posts/PE/exam/2026-09-29-serverless-computing/index.md) | 중급 | CNCF Serverless Whitepaper v1.0 (2018-02), UC Berkeley EECS-2019-3 (2019-02), AWS Lambda Developer Guide (2026-09 확인) | 문서 근거 |
| 2026-09-29 | [기출문제 — AI 생성 코드와 오픈웨이트 모델의 오픈소스 라이선스 컴플라이언스](posts/PE/exam/2026-09-29-ai-code-open-weight-license-compliance/index.md) | 심화 | ISO/IEC 5230:2020 (OpenChain 2.1), ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023), SPDX 3.0.1 (2024), OSI Open Source AI Definition 1.0 (2024-10), Llama 3.1 Community License (2024-07-23), U.S. Copyright Office, Copyright and AI Part 2 (2025-01) | 문서 근거 |
| 2026-09-28 | [기출문제 — WBS 작성 방법](posts/PE/exam/2026-09-28-wbs-construction/index.md) | 중급 | ISO 21511:2018, NASA/SP-2016-3404/REV1 (2018-01), PMBOK Guide 6th Edition (2017) | 문서 근거 |
| 2026-09-28 | [기출문제 — 프롬프트 엔지니어링과 하네스 엔지니어링 비교](posts/PE/exam/2026-09-28-prompt-vs-harness-engineering/index.md) | 중급 | The Prompt Report arXiv:2406.06608v6 (2025-02), Anthropic Engineering (2025-11-26), martinfowler.com Harness engineering (2026-04-02), Google Developers Blog (2026-09-09) | 문서 근거 |
| 2026-09-28 | [기출문제 — 비인간 신원(NHI)의 보안 취약점](posts/PE/exam/2026-09-28-non-human-identity-security-weaknesses/index.md) | 중급 | OWASP NHI Top 10 (2025), NIST SP 800-207A (2023-09), IETF draft-ietf-wimse-arch-08 (2026-07) | 문서 근거 |
| 2026-09-28 | [기출문제 — 디지털 포렌식](posts/PE/exam/2026-09-28-digital-forensics/index.md) | 중급 | NIST SP 800-86 (2006-08), ISO/IEC 27037:2012, RFC 3227 (2002-02) | 문서 근거 |
| 2026-09-23 | [기출문제 — Physical AI와 생성형 AI 비교](posts/PE/exam/2026-09-23-physical-ai-vs-generative-ai/index.md) | 중급 | NIST AI 600-1 (2024-07), RT-2 arXiv:2307.15818 (2023-07), WEF Physical AI White Paper (2025-09) | 문서 근거 |
| 2026-09-23 | [기출문제 — 차등 맨체스터(Differential Manchester) 부호화](posts/PE/exam/2026-09-23-differential-manchester-encoding/index.md) | 중급 | IEEE 802.5 (Token Ring), IEEE 802.3cg Draft D0.3 (2017-11), Python 3.13.5 | 실행 검증 |
| 2026-09-22 | [기출문제 — 좀비 프로세스](posts/PE/exam/2026-09-22-zombie-process/index.md) | 중급 | IEEE Std 1003.1-2024 (POSIX.1-2024), Linux man-pages — wait(2)·proc(5)·pid_namespaces(7), 2026-09-22 조회, Docker Engine CLI 문서 (docker run --init), 2026-09-22 조회 | 문서 근거 |
| 2026-09-22 | [기출문제 — 잭나이프 기법의 편향 감소와 분산 추정](posts/PE/exam/2026-09-22-jackknife-resampling/index.md) | 중급 | Python 3.13.5, Efron & Stein, Ann. Statist. 9(3), 1981, Shao & Wu, Ann. Statist. 17(3), 1989 | 실행 검증 |
| 2026-09-22 | [기출문제 — ISO/IEC 25010 제품 품질 모델의 주특성과 부특성](posts/PE/exam/2026-09-22-iso-iec-25010-product-quality-model/index.md) | 중급 | ISO/IEC 25010:2023 (2판, 2023-11), ISO/IEC 25010:2011 (1판) | 문서 근거 |
| 2026-09-22 | [기출문제 — 어휘 검색과 의미 검색을 결합한 하이브리드 검색](posts/PE/exam/2026-09-22-hybrid-search-lexical-vector/index.md) | 중급 | Cormack et al., SIGIR 2009 (RRF), Karpukhin et al., EMNLP 2020 (DPR), Bruch et al., ACM TOIS 2023 | 문서 근거 |
| 2026-09-21 | [기출문제 — PMC와 PMO 비교](posts/PE/exam/2026-09-21-pmc-pmo/index.md) | 중급 | 전자정부법 제64조의2, 전자정부사업관리 위탁에 관한 규정 (2024.6.27 일부개정), PMBOK Guide 5th Edition (2013) | 문서 근거 |
| 2026-09-21 | [기출문제 — 다크 팩토리(Dark Factory)](posts/PE/exam/2026-09-21-dark-factory/index.md) | 중급 | IEC 62264-1:2013, ISO 23247-1:2021, ISO 10218-1:2025 | 문서 근거 |
| 2026-09-21 | [기출문제 — ATAM(Architecture Trade-off Analysis Method)](posts/PE/exam/2026-09-21-atam/index.md) | 중급 | CMU/SEI-2000-TR-004 (2000.8), Evaluating Software Architectures (2002) | 문서 근거 |
| 2026-09-21 | [기출문제 — AI 기반 업무 프로세스 재설계(BPR) 도입 효과](posts/PE/exam/2026-09-21-ai-driven-bpr/index.md) | 중급 | Hammer & Champy, Reengineering the Corporation (1993), IEEE 1849-2023 (XES), ISO/IEC 22989:2022, ISO/IEC 42001:2023, NIST AI RMF 1.0 (2023) | 문서 근거 |

## 주식·재무 (finance) — 86편

| 날짜 | 제목 | 난이도 | 환경 | 검증 |
|---|---|---|---|---|
| 2026-10-25 | [운전자본 증감 — 이익과 현금흐름을 가장 크게 벌리는 항목](posts/Finance/ratios/2026-10-25-working-capital-change-and-operating-cash-flow/index.md) | 중급 | Python 3.13.5, K-IFRS 제1007호 현금흐름표, 한국은행 기업경영분석 통계정보보고서(2019.12) | 실행 검증 |
| 2026-10-25 | [주식기준보상 — 현금이 나가지 않는데 비용으로 잡히는 구조](posts/Finance/statements/2026-10-25-share-based-payment-vesting-expense/index.md) | 중급 | Python 3.13.5, K-IFRS 제1102호 주식기준보상, IFRS 2 Share-based Payment (2023년판) | 실행 검증 |
| 2026-10-25 | [특수관계자 거래 주석 — 연결에서 사라지는 거래와 별도에 남는 거래](posts/Finance/statements/2026-10-25-related-party-disclosures-consolidation/index.md) | 입문 | Python 3.13.5, K-IFRS 제1024호 특수관계자 공시, IAS 24 Related Party Disclosures (2022년판) | 실행 검증 |
| 2026-10-25 | [순차입금과 Net Debt/EBITDA — 빚의 크기를 이익으로 재기](posts/Finance/ratios/2026-10-25-net-debt-and-ebitda-multiple/index.md) | 중급 | Python 3.13.5, K-IFRS 제1007호 현금흐름표, K-IFRS 제1116호 리스, K-IFRS 제1118호 재무제표 표시와 공시(2027.1.1 시행), 한국은행 기업경영분석 통계정보보고서(2019.12) | 실행 검증 |
| 2026-10-25 | [업종 평균과 비교할 때 — 공표된 집계를 쓰는 법과 그 한계](posts/Finance/ratios/2026-10-25-industry-average-aggregate-vs-median/index.md) | 중급 | Python 3.13.5, 한국은행 『기업경영분석』 통계정보보고서(2019.12), 통계청 제10차 한국표준산업분류(고시 제2017-13호, 2017.7.1 시행) | 실행 검증 |
| 2026-10-25 | [EBITDA 마진 — 편하지만 틀리기 쉬운 지표](posts/Finance/ratios/2026-10-25-ebitda-margin-and-capex-gap/index.md) | 중급 | Python 3.13.5, K-IFRS 제1001호 재무제표 표시, K-IFRS 제1007호 현금흐름표, K-IFRS 제1116호 리스, K-IFRS 제1118호 재무제표 표시와 공시(2027.1.1 시행) | 실행 검증 |
| 2026-10-25 | [배당할인모형(DDM) — 배당만으로 값을 매길 때](posts/Finance/valuation/2026-10-25-dividend-discount-model-gordon-growth/index.md) | 중급 | Python 3.13.5, Gordon & Shapiro(1956), Management Science 3(1), 102-110 | 실행 검증 |
| 2026-10-25 | [매출원가율과 판관비율 — 이익률이 깎이는 자리 찾기](posts/Finance/ratios/2026-10-25-cogs-ratio-vs-sga-ratio/index.md) | 중급 | Python 3.13.5, K-IFRS 제1001호 재무제표 표시, 한국은행 기업경영분석 통계정보보고서(2019.12) | 실행 검증 |
| 2026-10-23 | [부문별 정보 — 합쳐진 숫자를 쪼개 보는 자리](posts/Finance/statements/2026-10-23-operating-segments-disclosure/index.md) | 중급 | Python 3.13.5, K-IFRS 제1108호 영업부문 | 실행 검증 |
| 2026-10-23 | [현금흐름표 직접법과 간접법 — 같은 현금, 다른 서술](posts/Finance/statements/2026-10-23-cash-flow-direct-vs-indirect/index.md) | 중급 | Python 3.13.5, K-IFRS 제1007호 현금흐름표 | 실행 검증 |
| 2026-10-22 | [연구개발비 — 어디까지가 자산이고 어디부터가 비용인가](posts/Finance/statements/2026-10-22-rnd-capitalisation-vs-expense/index.md) | 중급 | Python 3.13.5, K-IFRS 제1038호 무형자산, K-IFRS 제1036호 자산손상, K-IFRS 제1007호 현금흐름표 | 실행 검증 |
| 2026-10-22 | [유형자산 재평가모형 — 장부가를 다시 매길 때 어디로 들어가는가](posts/Finance/statements/2026-10-22-ppe-revaluation-model/index.md) | 중급 | Python 3.13.5, K-IFRS 제1016호 유형자산 | 실행 검증 |
| 2026-10-22 | [퇴직급여 — 확정기여형과 확정급여형이 재무제표에 다르게 찍히는 이유](posts/Finance/statements/2026-10-22-pension-dc-vs-db/index.md) | 중급 | Python 3.13.5, K-IFRS 제1019호 종업원급여 | 실행 검증 |
| 2026-10-22 | [전환사채와 신주인수권부사채 — 한 장의 증권을 부채와 자본으로 쪼개는 이유](posts/Finance/statements/2026-10-22-convertible-bond-liability-equity-split/index.md) | 중급 | Python 3.13.5, K-IFRS 제1032호 금융상품: 표시, K-IFRS 제1109호 금융상품 | 실행 검증 |
| 2026-10-21 | [시간외거래와 단일가매매 — 정규장 밖에서 가격이 정해지는 방식](posts/Finance/market/2026-10-21-single-price-auction-and-after-hours/index.md) | 입문 | Python 3.13.5, 유가증권시장 업무규정 2026-09-09 개정·2026-09-14 시행, 법제처 찾기쉬운 생활법령정보 2026-09-15 기준 | 실행 검증 |
| 2026-10-21 | [금리가 바뀌면 무엇이 먼저 움직이는가](posts/Finance/market/2026-10-21-interest-rate-to-valuation/index.md) | 입문 | Python 3.13.5, 한국은행 통화정책 효과의 파급(2026-10-21 조회), 한국은행 기준금리 안내(2026-10-21 조회) | 실행 검증 |
| 2026-10-21 | [임원·주요주주 소유보고 — 누가 언제 사고팔았는지](posts/Finance/disclosure/2026-10-21-insider-ownership-reporting/index.md) | 중급 | Python 3.13.5, 자본시장법 제173조의3 — 2024-07-24 시행, 금융감독원 기업공시 길라잡이 — 2026-10-21 조회분 | 실행 검증 |
| 2026-10-21 | [지배구조보고서와 ESG 공시 — 무엇을 어떻게 비교하는가](posts/Finance/disclosure/2026-10-21-governance-report-and-esg-disclosure/index.md) | 중급 | Python 3.13.5, 기업지배구조 보고서 가이드라인 2025.12 (한국거래소), 지속가능성(ESG) 공시 제도화 방안 최종안 — 2026-07-08 발표 | 실행 검증 |
| 2026-10-21 | [채권 기초 — 표면금리·만기수익률·듀레이션](posts/Finance/market/2026-10-21-bond-coupon-ytm-duration/index.md) | 입문 | Python 3.13.5, 한국은행 「2020 경제금융용어 700선」(2020-08 발간), 기획재정부 국채시장 국채종류(2026-10-21 조회) | 실행 검증 |
| 2026-10-21 | [감사의견 변형과 상장폐지 사유 — 숫자 밖의 위험 신호](posts/Finance/disclosure/2026-10-21-audit-opinion-and-delisting/index.md) | 중급 | ISA 705 (Revised) — 2016-12-15 이후 종료 회계기간 적용, 유가증권시장 상장규정 — 2025-07-01 시행 개정분 | 문서 근거 |
| 2026-10-20 | [호가 스프레드 — 체결 비용이 수익률을 깎는 정도](posts/Finance/market/2026-10-20-spread-and-round-trip-cost/index.md) | 입문 | Python 3.13.5 | 실행 검증 |
| 2026-10-20 | [지수 편입과 리밸런싱 — 지수가 바뀔 때 생기는 수급](posts/Finance/market/2026-10-20-index-inclusion-rebalancing-flow/index.md) | 입문 | Python 3.13.5 | 실행 검증 |
| 2026-10-20 | [괴리율 — ETF·ETN 가격이 기준가와 벌어질 때](posts/Finance/market/2026-10-20-disparity-ratio-etf-etn/index.md) | 입문 | Python 3.13.5, 한국거래소 유가증권시장 업무규정 2026-08-19 시행 개정 | 실행 검증 |
| 2026-10-20 | [액티브와 패시브 — 보수가 장기 수익률을 깎는 정도](posts/Finance/market/2026-10-20-active-vs-passive-fee-drag/index.md) | 입문 | Python 3.13.5, 금융투자협회 전자공시 펀드별 보수비용비교(2026-10-21 조회) | 실행 검증 |
| 2026-10-16 | [총주주수익률(TSR) — 배당과 자사주를 합쳐 보기](posts/Finance/valuation/2026-10-16-tsr-dividend-buyback/index.md) | 중급 | Python 3.13.5, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-16 | [상·하한가와 변동성완화장치(VI) — 어느 장치가 먼저 걸리는가](posts/Finance/market/2026-10-16-price-limit-volatility-interruption/index.md) | 중급 | Python 3.13.5 | 실행 검증 |
| 2026-10-15 | [WACC — 할인율은 어떻게 만들어지는가](posts/Finance/valuation/2026-10-15-wacc-capital-structure/index.md) | 중급 | Python 3.13.5, K-IFRS 제1036호 자산손상, K-IFRS 제1012호 법인세 | 실행 검증 |
| 2026-10-15 | [잔여이익모형(RIM) — 장부가에서 출발하는 평가](posts/Finance/valuation/2026-10-15-residual-income-model-book-value/index.md) | 중급 | Python 3.13.5, K-IFRS 제1001호 재무제표 표시, K-IFRS 제1036호 자산손상 | 실행 검증 |
| 2026-10-15 | [PEG — 성장률로 PER을 나눌 때 생기는 함정](posts/Finance/valuation/2026-10-15-peg-growth-rate-choice/index.md) | 중급 | Python 3.13.5, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-15 | [지배주주지분 순이익 — 연결에서 EPS를 계산할 때](posts/Finance/valuation/2026-10-15-controlling-interest-net-income-eps/index.md) | 중급 | Python 3.13.5, K-IFRS 제1110호 연결재무제표, K-IFRS 제1033호 주당이익, K-IFRS 제1001호 재무제표 표시 | 실행 검증 |
| 2026-10-14 | [세 가지 마진 — 매출총이익률·영업이익률·순이익률](posts/Finance/ratios/2026-10-14-three-margins-step-by-step/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 통계정보보고서(2019.12), K-IFRS 제1001호, IFRS 18 | 실행 검증 |
| 2026-10-14 | [비율 분석이 틀리는 세 가지 경우 — 업종, 회계정책, 시점](posts/Finance/ratios/2026-10-14-ratio-distortions-industry-policy-timing/index.md) | 중급 | Python 3.13.5, K-IFRS 제1002호, K-IFRS 제1016호, K-IFRS 제1116호(2019-01-01 시행), K-IFRS 제1008호, 한국은행 기업경영분석 통계정보보고서(2019.12) | 실행 검증 |
| 2026-10-14 | [PSR과 PCR — 이익이 적자일 때 분모를 어디서 가져오는가](posts/Finance/valuation/2026-10-14-psr-pcr-when-earnings-negative/index.md) | 중급 | Python 3.13.5, K-IFRS 제1007호, K-IFRS 제1115호, CFA Program Curriculum 2026 Level II | 실행 검증 |
| 2026-10-14 | [자기자본비율과 차입금의존도 — 안정성을 보는 다른 각도](posts/Finance/ratios/2026-10-14-equity-ratio-and-borrowing-dependency/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 통계정보보고서(2019.12), 한국은행 기업경영분석 2024년 1/4분기 | 실행 검증 |
| 2026-10-13 | [중단영업 — 접기로 한 사업은 어떻게 표시되는가](posts/Finance/statements/2026-10-13-discontinued-operations/index.md) | 중급 | Python 3.13.5, K-IFRS 제1105호 매각예정비유동자산과 중단영업 | 실행 검증 |
| 2026-10-13 | [유동비율과 당좌비율 — 재고를 빼고 보는 이유](posts/Finance/ratios/2026-10-13-current-ratio-vs-quick-ratio/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 통계정보보고서(2019.12), K-IFRS 제1002호 | 실행 검증 |
| 2026-10-13 | [어디까지가 현금인가 — 현금성자산과 단기금융상품](posts/Finance/statements/2026-10-13-cash-equivalents-and-short-term-deposits/index.md) | 입문 | Python 3.13.5, K-IFRS 제1007호 현금흐름표, K-IFRS 제1001호 재무제표 표시 | 실행 검증 |
| 2026-10-13 | [현금전환주기 — 돈이 묶여 있는 날수, 그리고 음수가 되는 구조](posts/Finance/ratios/2026-10-13-cash-conversion-cycle-negative/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 통계정보보고서(2019.12), K-IFRS 제1115호 | 실행 검증 |
| 2026-10-12 | [재고자산 평가 — 선입선출과 가중평균이 이익을 가르는 자리](posts/Finance/statements/2026-10-12-inventory-cost-formula-fifo-average/index.md) | 중급 | Python 3.13.5, K-IFRS 제1002호 재고자산 | 실행 검증 |
| 2026-10-12 | [외화환산 — 환율이 바뀌면 재무제표 어디가 움직이는가](posts/Finance/statements/2026-10-12-foreign-currency-translation/index.md) | 중급 | Python 3.13.5, K-IFRS 제1021호 환율변동효과 | 실행 검증 |
| 2026-10-12 | [금융자산 세 분류 — 상각후원가·FVOCI·FVPL](posts/Finance/statements/2026-10-12-financial-assets-three-classes/index.md) | 중급 | Python 3.13.5, K-IFRS 제1109호 금융상품 | 실행 검증 |
| 2026-10-12 | [지분법 — 관계기업 투자가 한 줄로만 보이는 이유](posts/Finance/statements/2026-10-12-equity-method-associates/index.md) | 중급 | Python 3.13.5, K-IFRS 제1028호 관계기업과 공동기업에 대한 투자 | 실행 검증 |
| 2026-10-12 | [자본잠식 — 자본총계가 자본금보다 작아진다는 말](posts/Finance/statements/2026-10-12-capital-impairment-ratio/index.md) | 입문 | Python 3.13.5, 상법 제438조·제451조·제460조, 한국거래소 유가증권시장 정기결산 유의사항(2026-02) | 실행 검증 |
| 2026-10-12 | [차입금과 사채 — 조달 수단이 재무제표에 남기는 자국](posts/Finance/statements/2026-10-12-bonds-effective-interest/index.md) | 중급 | Python 3.13.5, K-IFRS 제1109호 금융상품, K-IFRS 제1001호 재무제표 표시 | 실행 검증 |
| 2026-10-10 | [수익 인식 5단계 — 묶어 판 상품의 매출은 언제 얼마씩 잡히는가](posts/Finance/statements/2026-10-10-revenue-recognition-five-steps/index.md) | 중급 | Python 3.13.5, K-IFRS 제1115호 고객과의 계약에서 생기는 수익 | 실행 검증 |
| 2026-10-10 | [충당부채와 우발부채 — 아직 나가지 않은 돈을 부채로 잡는 기준](posts/Finance/statements/2026-10-10-provisions-and-contingent-liabilities/index.md) | 중급 | Python 3.13.5, K-IFRS 제1037호 충당부채, 우발부채, 우발자산 | 실행 검증 |
| 2026-10-10 | [리스 회계 — 임차료가 부채로 올라가면 부채비율과 이익이 어떻게 움직이는가](posts/Finance/statements/2026-10-10-lease-liability-right-of-use/index.md) | 중급 | Python 3.13.5, K-IFRS 제1116호 리스 (2019.1.1 이후 시작 회계연도 적용), K-IFRS 제1007호 현금흐름표 | 실행 검증 |
| 2026-10-10 | [영업권 — 인수 대가가 순자산보다 클 때 남는 숫자와 손상검사](posts/Finance/statements/2026-10-10-goodwill-impairment-test/index.md) | 중급 | Python 3.13.5, K-IFRS 제1103호 사업결합, K-IFRS 제1036호 자산손상, K-IFRS 제1038호 무형자산 | 실행 검증 |
| 2026-10-10 | [배당락과 권리락 — 기준일보다 하루 먼저 주가가 내려가는 이유](posts/Finance/market/2026-10-10-ex-dividend-ex-rights/index.md) | 입문 | Python 3.13.5, 상법 제354조(1984-09-01 시행)·제464조의2(2012-04-15 시행), 소득세법 제129조(2026-07-01 시행), 한국거래소 결제 주기 T+2(2026-10 기준) | 실행 검증 |
| 2026-10-10 | [이연법인세 — 회계이익과 과세소득이 다를 때 생기는 자산과 부채](posts/Finance/statements/2026-10-10-deferred-tax-temporary-difference/index.md) | 심화 | Python 3.13.5, K-IFRS 제1012호 법인세 | 실행 검증 |
| 2026-10-10 | [손익분기점과 영업레버리지 — 고정비 비중이 이익 변동 폭을 키우는 이유](posts/Finance/ratios/2026-10-10-break-even-operating-leverage/index.md) | 중급 | Python 3.13.5, K-IFRS 제1001호 재무제표 표시 | 실행 검증 |
| 2026-10-10 | [사업보고서 읽는 순서 — 어디부터 펴는가](posts/Finance/disclosure/2026-10-10-annual-report-reading-order/index.md) | 입문 | 자본시장법 제159조(2018-03-30 시행), 자본시장법 시행령 제168조·제170조, 금융감독원 DART 기업공시 길라잡이(2026-10 열람), 기업공시서식 작성기준(2026-09-30 시행) | 문서 근거 |
| 2026-10-08 | [자사주 매입과 소각 — 주식 수가 줄 때 지표가 움직이는 이유](posts/Finance/market/2026-10-08-share-buyback-cancellation/index.md) | 입문 | Python 3.13.5, 상법 제341조·제462조(2012-04-15 시행), 개정 상법 제341조의4·제343조(2026-03-06 시행), K-IFRS 제1032호 금융상품: 표시, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-08 | [기본 EPS와 희석 EPS — 전환사채가 있을 때 주당이익](posts/Finance/valuation/2026-10-08-diluted-eps-convertible-bonds/index.md) | 중급 | Python 3.13.5, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-07 | [주가지수는 어떻게 계산되는가 — 주가 가중과 시가총액 가중](posts/Finance/market/2026-10-07-index-weighting-methods/index.md) | 입문 | Python 3.13.5, Nikkei 225 Index Guidebook(2025-07-24판), S&P DJI Index Mathematics Methodology(2014-11판) | 실행 검증 |
| 2026-10-07 | [잉여현금흐름(FCF) — 영업현금흐름에서 설비 투자를 뺀 뒤 남는 돈](posts/Finance/ratios/2026-10-07-free-cash-flow-after-capex/index.md) | 중급 | Python 3.13.5, K-IFRS 제1007호·제1116호, ESMA APM 가이드라인 ESMA/2015/1415 (2016.7.3 적용), SEC C&DI 102.07 (2016.5.17) | 실행 검증 |
| 2026-10-07 | [ETF — 바구니를 주식처럼 사고파는 구조](posts/Finance/market/2026-10-07-etf-nav-premium-tracking/index.md) | 입문 | Python 3.13.5, 자본시장법 제234조, ESMA Guidelines on ETFs and other UCITS issues(ESMA/2014/937), SEC Rule 6c-11(2019-12-23 시행) | 실행 검증 |
| 2026-10-07 | [자본변동표 — 자본은 무엇으로 늘고 무엇으로 줄었는가](posts/Finance/statements/2026-10-07-equity-changes-statement/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호·제1032호, 상법(법률 제10600호, 2012.4.15 시행) | 실행 검증 |
| 2026-10-07 | [공시 체계 — 정기·수시·공정공시, 그리고 시한을 세는 두 달력](posts/Finance/disclosure/2026-10-07-disclosure-deadlines/index.md) | 중급 | Python 3.13.5, 자본시장법 제159조(2018-03-30 시행)·제160조·제161조(2025-07-22 시행), 민법 제157조·제161조(2008-03-22 시행), 코스닥시장 공시·상장관리 해설(2025.9), 유가증권시장 12월 결산법인 정기결산 유의사항(2026.2) | 실행 검증 |
| 2026-10-07 | [K-IFRS 연결과 별도 — 같은 회사의 두 숫자, 어느 쪽을 봐야 하는가](posts/Finance/disclosure/2026-10-07-consolidated-vs-separate/index.md) | 중급 | Python 3.13.5, K-IFRS 제1110호·제1027호·제1028호·제1033호, 코스닥시장 공시·상장관리 해설(2025.9), 유가증권시장 12월 결산법인 정기결산 유의사항(2026.2) | 실행 검증 |
| 2026-10-06 | [거래량과 거래대금 — 어느 쪽을 봐야 하는가](posts/Finance/market/2026-10-06-trading-volume-vs-value/index.md) | 입문 | Python 3.13.5, 유가증권시장 상장규정 제47조·제48조 (생활법령 기준일 2026-09-15) | 실행 검증 |
| 2026-10-06 | [공매도 — 없는 주식을 파는 구조](posts/Finance/market/2026-10-06-short-selling-mechanics/index.md) | 입문 | Python 3.13.5, 자본시장법 제180조 (2026-10-02 시행본), 자본시장법 시행령 공매도 제도개선 (2025-03-31 시행) | 실행 검증 |
| 2026-10-06 | [유상증자 — 지분이 희석된다는 말의 뜻](posts/Finance/market/2026-10-06-rights-issue-dilution/index.md) | 입문 | Python 3.13.5, 상법 제418조(2012-04-15 시행), 자본시장법 제165조의6(2013-08-29 시행), 증권의 발행 및 공시 등에 관한 규정 제5-18조, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-06 | [호가와 체결 — 주문이 실제로 어떻게 맺어지는가](posts/Finance/market/2026-10-06-order-book-matching/index.md) | 입문 | Python 3.13.5, 유가증권시장 업무규정 제22조, 유가증권시장 업무규정 제21조 호가가격단위 | 실행 검증 |
| 2026-10-04 | [액면분할과 무상증자 — 주식 수가 늘 때](posts/Finance/market/2026-10-04-stock-split-and-bonus-issue/index.md) | 입문 | Python 3.13.5, 상법 제329조의2(2014-05-20 시행), 상법 제461조(2020-12-29 개정), K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-04 | [시가총액과 주가 — 비싼 주식과 비싼 회사](posts/Finance/market/2026-10-04-market-cap-vs-share-price/index.md) | 입문 | Python 3.13.5, K-IFRS 제1033호 주당이익, 상법 제329조(2012-04-15 시행) | 실행 검증 |
| 2026-10-03 | [PBR과 청산가치 — 1배 아래가 뜻하는 것](posts/Finance/valuation/2026-10-03-pbr-below-book-value/index.md) | 중급 | Python 3.13.5, K-IFRS 제1036호 자산손상, K-IFRS 제1002호 재고자산 | 실행 검증 |
| 2026-10-03 | [EV/EBITDA — 빚까지 포함해 회사를 사는 값](posts/Finance/valuation/2026-10-03-ev-ebitda-debt-included/index.md) | 중급 | Python 3.13.5, K-IFRS 제1116호 리스, K-IFRS 제1007호 현금흐름표 | 실행 검증 |
| 2026-10-03 | [배당수익률과 배당성향 — 얼마를 나눠 주는가](posts/Finance/valuation/2026-10-03-dividend-yield-vs-payout/index.md) | 중급 | Python 3.13.5, 상법 제462조(2012-04-15 시행), 상법 제458조(2012-04-15 시행) | 실행 검증 |
| 2026-10-03 | [현금흐름할인(DCF) — 미래의 돈을 오늘 값으로](posts/Finance/valuation/2026-10-03-dcf-discount-rate-sensitivity/index.md) | 심화 | Python 3.13.5, K-IFRS 제1036호 자산손상, K-IFRS 제1113호 공정가치 측정 | 실행 검증 |
| 2026-10-02 | [PER — 이익 대비 주가를 재는 법](posts/Finance/valuation/2026-10-02-per-trailing-vs-forward/index.md) | 중급 | Python 3.13.5, K-IFRS 제1033호 주당이익 | 실행 검증 |
| 2026-10-02 | [이자보상배율 — 빚을 감당하는가](posts/Finance/ratios/2026-10-02-interest-coverage-ratio/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 분석지표 해설(2019.12), 한국은행 2024년 기업경영분석(2025.10.29 발표) | 실행 검증 |
| 2026-10-02 | [듀폰 분석 — ROE를 세 조각으로 쪼개기](posts/Finance/ratios/2026-10-02-dupont-roe-three-factors/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 지표 해설(2019.12), CFA Institute 2026 Curriculum | 실행 검증 |
| 2026-10-02 | [활동성 비율 — 자산을 얼마나 굴리는가](posts/Finance/ratios/2026-10-02-activity-ratios-three-years/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 지표 해설(2019.12), CFA Institute 2026 Curriculum | 실행 검증 |
| 2026-10-01 | [수익성 비율 — ROE와 ROA는 무엇이 다른가](posts/Finance/ratios/2026-10-01-roe-vs-roa/index.md) | 중급 | Python 3.13.5, 한국은행 기업경영분석 지표 해설(2019.12) | 실행 검증 |
| 2026-10-01 | [매출채권과 재고자산 — 자산인데 위험한 자산](posts/Finance/statements/2026-10-01-receivables-inventory-turnover/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호·제1002호·제1109호 | 실행 검증 |
| 2026-10-01 | [주석과 감사보고서 — 본문보다 중요한 자리](posts/Finance/statements/2026-10-01-notes-and-audit-opinion/index.md) | 입문 | K-IFRS 제1001호·제1024호·제1037호, ISA 700·705(2016 개정)·570, 유가증권시장 상장규정(2025.7 개정) | 문서 근거 |
| 2026-10-01 | [안정성 비율 — 부채비율과 유동비율](posts/Finance/ratios/2026-10-01-leverage-and-current-ratio/index.md) | 중급 | Python 3.13.5, K-IFRS 제1001호, 한국은행 기업경영분석 2024년 1/4분기 | 실행 검증 |
| 2026-09-30 | [영업이익과 당기순이익이 크게 벌어질 때](posts/Finance/statements/2026-09-30-operating-vs-net-income-gap/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호·제1021호·제1036호 | 실행 검증 |
| 2026-09-30 | [감가상각 — 현금이 나가지 않는 비용](posts/Finance/statements/2026-09-30-depreciation-non-cash-expense/index.md) | 입문 | Python 3.13.5, K-IFRS 제1016호·제1007호 | 실행 검증 |
| 2026-09-30 | [영업·투자·재무 활동 — 현금흐름 세 갈래 읽기](posts/Finance/statements/2026-09-30-cash-flow-three-activities/index.md) | 입문 | Python 3.13.5, K-IFRS 제1007호 | 실행 검증 |
| 2026-09-30 | [현금흐름표 — 이익이 나는데 돈이 없는 이유](posts/Finance/statements/2026-09-30-cash-flow-profit-without-cash/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호·제1007호·제1115호 | 실행 검증 |
| 2026-09-29 | [재무제표 세 장은 서로 어떻게 이어지는가](posts/Finance/statements/2026-09-29-three-statements-linkage/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호·제1007호 | 실행 검증 |
| 2026-09-29 | [손익계산서 — 매출에서 순이익까지 다섯 단계](posts/Finance/statements/2026-09-29-income-statement-five-steps/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호, K-IFRS 제1118호(2027년 시행) | 실행 검증 |
| 2026-09-29 | [유동과 비유동을 왜 나누는가](posts/Finance/statements/2026-09-29-current-vs-noncurrent/index.md) | 입문 | Python 3.13.5, K-IFRS 제1001호 | 실행 검증 |
| 2026-09-29 | [재무상태표 — 자산은 어디서 왔는가](posts/Finance/statements/2026-09-29-balance-sheet-debt-vs-equity/index.md) | 입문 | Python 3.13.5, 재무보고를 위한 개념체계(2018), K-IFRS 제1032호 | 실행 검증 |

## 같은 기능을 여러 환경에서 다룬 글

**`constraints`**

- [CREATE TABLE — 타입과 기본 제약조건](posts/Database/sql-basics/2026-09-29-create-table-constraints-when-checked/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 제약조건 — 종류와 검증 시점](posts/Database/tibero/2026-10-12-tibero7-constraints-state-deferrable/index.md) — Tibero 7

**`cte`**

- [CTE — WITH 절로 질의에 이름 붙이기](posts/Database/sql-basics/2026-10-07-cte-with-clause/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [임시 테이블과 CTE — 어느 쪽을 쓸까](posts/Database/sql-basics/2026-10-14-temp-table-vs-cte/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 WITH 절 — 이름 붙인 부질의와 재귀 질의, SEARCH·CYCLE 절](posts/Database/tibero/2026-10-07-tibero7-with-clause-recursive-cte/index.md) — Tibero 7

**`datetime-types`**

- [날짜와 시간 다루기 — 저장과 연산](posts/Database/sql-basics/2026-10-01-sql-date-time-storage-arithmetic/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 날짜·시간 타입 — DATE와 TIMESTAMP의 차이](posts/Database/tibero/2026-10-07-tibero7-date-timestamp-types/index.md) — Tibero 7

**`deadlock`**

- [데드락은 어떻게 만들어지고 SQLite는 누구에게 BUSY를 돌려주는가](posts/Database/2026-09-29-sqlite-deadlock-busy-victim/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [교착상태 4조건과 해결 기법](posts/PE/system/2026-10-12-deadlock-conditions-bankers-algorithm/index.md) — Python 3.13.5, Silberschatz·Galvin·Gagne, Operating System Concepts 10th ed. (2018) Ch.8 슬라이드 (S. Weiss 2020 개정판), Arpaci-Dusseau, Operating Systems: Three Easy Pieces v1.20 Ch.32

**`explain-plan`**

- [실행계획의 비용(cost)은 무엇을 세는 숫자인가](posts/Database/2026-09-30-optimizer-cost-stale-statistics/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [EXPLAIN QUERY PLAN 읽는 법 — SCAN, SEARCH, USE TEMP B-TREE](posts/Database/sql-basics/2026-10-08-explain-query-plan-reading/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 실행계획 보기 — EXPLAIN PLAN과 DBMS_XPLAN](posts/Database/tibero/2026-09-30-tibero7-explain-plan-dbms-xplan/index.md) — Tibero 7

**`group-by`**

- [GROUP BY와 집계 함수 — 묶는 기준 정하기](posts/Database/sql-basics/2026-09-22-group-by-aggregate-null/index.md) — SQLite 3.49.1, Python 3.13.5
- [GROUP BY 여러 컬럼 — 묶는 단위가 달라질 때](posts/Database/sql-basics/2026-10-06-group-by-multiple-columns/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11

**`hierarchical-query`**

- [재귀 CTE — 조직도를 한 질의로 펴는 법](posts/Database/sql-basics/2026-10-07-recursive-cte-hierarchy/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 계층 질의 — CONNECT BY와 순환 참조](posts/Database/tibero/2026-09-22-tibero7-connect-by-hierarchy/index.md) — Tibero 7

**`null-semantics`**

- [NULL이 인덱스, 집계, 비교에서 각각 다르게 동작하는 이유](posts/Database/2026-10-03-null-index-group-unique-distinct/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [COALESCE와 NULLIF — NULL을 다루는 두 함수](posts/Database/sql-basics/2026-09-28-coalesce-nullif-null-handling/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [COUNT(*)와 COUNT(컬럼)이 다른 값을 내는 이유](posts/Database/sql-basics/2026-10-02-count-star-vs-column-null/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [NULL 비교 — = NULL이 안 되는 이유](posts/Database/sql-basics/2026-10-02-null-comparison-three-valued-logic/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11

**`optimizer-hint`**

- [옵티마이저 힌트를 쓰기 전에 확인할 3가지 — 통계·데이터·스키마](posts/Database/2026-10-07-optimizer-hint-three-checks/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 옵티마이저 힌트 — 문법과 적용 확인](posts/Database/tibero/2026-09-29-tibero7-optimizer-hints/index.md) — Tibero 7

**`row-limiting`**

- [LIMIT과 OFFSET — 결과를 잘라내는 문법](posts/Database/sql-basics/2026-09-22-limit-offset-pagination/index.md) — SQLite 3.49.1, Python 3.13.5
- [커서 기반 페이지네이션이 OFFSET을 이기는 지점 — SQLite 3.49.1로 잰 깊이별 비용](posts/Database/sqlite/2026-09-29-keyset-vs-offset-crossover/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 페이징 — ROWNUM이 정렬보다 먼저 붙는 이유와 OFFSET·FETCH](posts/Database/tibero/2026-10-08-tibero7-rownum-paging/index.md) — Tibero 7

**`table-partitioning`**

- [파티셔닝이 항상 빨라지지 않는 이유 — 프루닝이 깨진 뒤에 남는 비용](posts/Database/2026-10-13-partition-pruning-global-index-cost/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [Tibero 7 파티션 테이블 — 종류별로 언제 쓰는가](posts/Database/tibero/2026-09-23-tibero7-partition-table-types/index.md) — Tibero 7

**`transaction-isolation`**

- [트랜잭션 격리 수준별로 실제 무슨 이상 현상이 보이는가](posts/Database/sqlite/2026-09-21-isolation-level-anomalies/index.md) — SQLite 3.49.1, Python 3.13.5
- [Tibero 7 트랜잭션 격리 수준 — 지원 범위와 설정](posts/Database/tibero/2026-09-30-tibero7-transaction-isolation/index.md) — Tibero 7
- [트랜잭션 ACID와 격리 수준 — 이상현상으로 수준을 정의하는 방식](posts/PE/database/2026-09-23-acid-and-isolation-levels/index.md) — PostgreSQL 16 문서, Berenson et al., SIGMOD 1995

**`window-function`**

- [윈도우 함수 입문 — ROW_NUMBER로 그룹별 1등 뽑기](posts/Database/sql-basics/2026-10-03-window-function-row-number-top-per-group/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [RANK와 DENSE_RANK — 동점을 어떻게 셀까](posts/Database/sql-basics/2026-10-06-rank-dense-rank-ties/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [누적합과 이동평균 — SUM OVER의 프레임](posts/Database/sql-basics/2026-10-06-sum-over-frame-rows-range/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [LAG와 LEAD — 앞뒤 행의 값을 같은 줄에 놓기](posts/Database/sql-basics/2026-10-12-lag-lead-previous-next-row/index.md) — SQLite 3.49.1, Python 3.13.5, Windows 11
- [FIRST_VALUE와 LAST_VALUE — 구간의 처음과 끝](posts/Database/sql-basics/2026-10-16-first-value-last-value-window-frame/index.md) — SQLite 3.49.1, Python 3.13.5
- [NTILE — 데이터를 n등분하는 법](posts/Database/sql-basics/2026-10-16-ntile-quartile-remainder/index.md) — SQLite 3.49.1, Python 3.13.5
- [Tibero 7 분석 함수의 윈도우 절 — ROWS와 RANGE는 어디서 갈리는가](posts/Database/tibero/2026-09-23-tibero7-window-clause/index.md) — Tibero 7

