PROMPT ==== Tibero 7 WITH 절 — 보통 CTE 와 재귀 CTE, SEARCH / CYCLE 절
PROMPT 빈 스키마에서 돌린다. 표 두 개만 만들고 끝나면 지운다.

SELECT product_major, product_minor FROM v$version;

CREATE TABLE dept_unit (
    unit_id   NUMBER        PRIMARY KEY,
    unit_name VARCHAR2(40)  NOT NULL,
    parent_id NUMBER
);

CREATE TABLE unit_sales (
    unit_id NUMBER NOT NULL,
    amount  NUMBER NOT NULL
);

INSERT INTO dept_unit VALUES (1, '본사',       NULL);
INSERT INTO dept_unit VALUES (2, '개발본부',   1);
INSERT INTO dept_unit VALUES (3, '영업본부',   1);
INSERT INTO dept_unit VALUES (4, '플랫폼팀',   2);
INSERT INTO dept_unit VALUES (5, '데이터팀',   2);
INSERT INTO dept_unit VALUES (6, '영업1팀',    3);
INSERT INTO unit_sales VALUES (4, 300);
INSERT INTO unit_sales VALUES (5, 200);
INSERT INTO unit_sales VALUES (6, 500);
INSERT INTO unit_sales VALUES (6, 100);
COMMIT;

DESC dept_unit
SELECT * FROM dept_unit ORDER BY unit_id;
SELECT * FROM unit_sales ORDER BY unit_id, amount;

PROMPT ==== 1. 보통 CTE — 집계에 이름을 붙이고 두 번 읽는다
WITH unit_total (unit_id, total) AS (
    SELECT unit_id, SUM(amount) FROM unit_sales GROUP BY unit_id
)
SELECT u.unit_name, t.total
FROM unit_total t JOIN dept_unit u ON u.unit_id = t.unit_id
WHERE t.total > (SELECT AVG(total) FROM unit_total)
ORDER BY t.total DESC;

PROMPT ==== 2. CTE 를 이어 쓰기 — 뒤의 query_name 이 앞의 것을 읽는다
WITH unit_total (unit_id, total) AS (
    SELECT unit_id, SUM(amount) FROM unit_sales GROUP BY unit_id
),
avg_total (avg_value) AS (
    SELECT AVG(total) FROM unit_total
)
SELECT t.unit_id, t.total, a.avg_value
FROM unit_total t, avg_total a
ORDER BY t.unit_id;

PROMPT ==== 3. 재귀 CTE — 본사부터 아래로. col_alias 목록은 필수, UNION ALL 로 잇는다
WITH org (unit_id, unit_name, parent_id, depth, path) AS (
    SELECT unit_id, unit_name, parent_id, 1, unit_name
    FROM dept_unit WHERE parent_id IS NULL
    UNION ALL
    SELECT c.unit_id, c.unit_name, c.parent_id, o.depth + 1, o.path || '/' || c.unit_name
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SELECT depth, LPAD(' ', 2 * (depth - 1)) || unit_name AS tree, path
FROM org
ORDER BY path;

PROMPT ==== 4. SEARCH DEPTH FIRST — 자식 먼저, 형제는 unit_name 순. ordering_column 으로 정렬
WITH org (unit_id, unit_name, parent_id, depth) AS (
    SELECT unit_id, unit_name, parent_id, 1
    FROM dept_unit WHERE parent_id IS NULL
    UNION ALL
    SELECT c.unit_id, c.unit_name, c.parent_id, o.depth + 1
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SEARCH DEPTH FIRST BY unit_name SET seq
SELECT seq, depth, LPAD(' ', 2 * (depth - 1)) || unit_name AS tree
FROM org
ORDER BY seq;

PROMPT ==== 5. SEARCH BREADTH FIRST — 같은 깊이를 다 낸 뒤 다음 깊이
WITH org (unit_id, unit_name, parent_id, depth) AS (
    SELECT unit_id, unit_name, parent_id, 1
    FROM dept_unit WHERE parent_id IS NULL
    UNION ALL
    SELECT c.unit_id, c.unit_name, c.parent_id, o.depth + 1
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SEARCH BREADTH FIRST BY unit_name SET seq
SELECT seq, depth, unit_name
FROM org
ORDER BY seq;

PROMPT ==== 6. 같은 트리를 CONNECT BY 로 — 결과를 4번과 나란히 비교한다
SELECT LEVEL AS depth,
       LPAD(' ', 2 * (LEVEL - 1)) || unit_name AS tree,
       SYS_CONNECT_BY_PATH(unit_name, '/') AS path
FROM dept_unit
START WITH parent_id IS NULL
CONNECT BY PRIOR unit_id = parent_id
ORDER SIBLINGS BY unit_name;

PROMPT ==== 7. 재귀 CTE 에서 단계마다 합계 — 아래 조직의 매출을 위로 올려 더한다
WITH org (unit_id, root_id) AS (
    SELECT unit_id, unit_id FROM dept_unit
    UNION ALL
    SELECT c.unit_id, o.root_id
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SELECT u.unit_name, SUM(s.amount) AS subtree_total
FROM org o
JOIN dept_unit u ON u.unit_id = o.root_id
JOIN unit_sales s ON s.unit_id = o.unit_id
GROUP BY u.unit_name
ORDER BY subtree_total DESC;

PROMPT ==== 8. 순환 데이터 — 본사의 부모를 영업1팀으로 바꿔 고리를 만든다
UPDATE dept_unit SET parent_id = 6 WHERE unit_id = 1;

PROMPT ==== 8-A. CYCLE 절 없이 — 매뉴얼: 순환이 검출되면 에러
WITH org (unit_id, unit_name, parent_id, depth) AS (
    SELECT unit_id, unit_name, parent_id, 1
    FROM dept_unit WHERE unit_id = 1
    UNION ALL
    SELECT c.unit_id, c.unit_name, c.parent_id, o.depth + 1
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SELECT depth, unit_name FROM org;

PROMPT ==== 8-B. CYCLE 절 — 순환이 검출된 행에 표시를 남기고 그 가지만 멈춘다
WITH org (unit_id, unit_name, parent_id, depth) AS (
    SELECT unit_id, unit_name, parent_id, 1
    FROM dept_unit WHERE unit_id = 1
    UNION ALL
    SELECT c.unit_id, c.unit_name, c.parent_id, o.depth + 1
    FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SEARCH DEPTH FIRST BY unit_name SET seq
CYCLE unit_id SET is_cycle TO 'Y' DEFAULT 'N'
SELECT seq, depth, unit_name, is_cycle
FROM org
ORDER BY seq;

PROMPT ==== 8-C. 같은 고리를 CONNECT BY 로 — NOCYCLE 없이, 그리고 NOCYCLE 과 CONNECT_BY_ISCYCLE
SELECT LEVEL, unit_name FROM dept_unit
START WITH unit_id = 1
CONNECT BY PRIOR unit_id = parent_id;

SELECT LEVEL, unit_name, CONNECT_BY_ISCYCLE AS is_cycle FROM dept_unit
START WITH unit_id = 1
CONNECT BY NOCYCLE PRIOR unit_id = parent_id;

ROLLBACK;

PROMPT ==== 9. 재귀 WITH 를 INSERT 의 원본으로 — 하위 조직 전체를 임시 표에 넣는다
CREATE TABLE unit_snapshot (unit_id NUMBER, depth NUMBER);
INSERT INTO unit_snapshot
WITH org (unit_id, depth) AS (
    SELECT unit_id, 1 FROM dept_unit WHERE unit_id = 2
    UNION ALL
    SELECT c.unit_id, o.depth + 1 FROM dept_unit c JOIN org o ON c.parent_id = o.unit_id
)
SELECT unit_id, depth FROM org;
SELECT * FROM unit_snapshot ORDER BY unit_id;
ROLLBACK;

PROMPT ==== 정리
DROP TABLE unit_snapshot;
DROP TABLE unit_sales;
DROP TABLE dept_unit;
SELECT COUNT(*) AS remaining_objects FROM user_objects;
EXIT
