SET LINESIZE 120
SET PAGESIZE 100

PROMPT ===== 0. 버전 =====
SELECT * FROM V$VERSION WHERE NAME IN ('PRODUCT_MAJOR', 'PRODUCT_MINOR');

PROMPT ===== 1. 예제 표 =====
CREATE TABLE pg_post (
    post_id    NUMBER        PRIMARY KEY,
    title      VARCHAR2(40)  NOT NULL,
    view_count NUMBER        NOT NULL,
    posted_at  DATE          NOT NULL
);

INSERT INTO pg_post VALUES (1,  '글01', 120, DATE '2026-09-01');
INSERT INTO pg_post VALUES (2,  '글02',  80, DATE '2026-09-02');
INSERT INTO pg_post VALUES (3,  '글03', 300, DATE '2026-09-03');
INSERT INTO pg_post VALUES (4,  '글04',  80, DATE '2026-09-04');
INSERT INTO pg_post VALUES (5,  '글05',  45, DATE '2026-09-05');
INSERT INTO pg_post VALUES (6,  '글06', 210, DATE '2026-09-06');
INSERT INTO pg_post VALUES (7,  '글07',  80, DATE '2026-09-07');
INSERT INTO pg_post VALUES (8,  '글08',  15, DATE '2026-09-08');
INSERT INTO pg_post VALUES (9,  '글09', 120, DATE '2026-09-09');
INSERT INTO pg_post VALUES (10, '글10', 500, DATE '2026-09-10');
INSERT INTO pg_post VALUES (11, '글11',  80, DATE '2026-09-11');
INSERT INTO pg_post VALUES (12, '글12', 120, DATE '2026-09-12');
COMMIT;

DESC pg_post
SELECT * FROM pg_post ORDER BY post_id;

PROMPT ===== 2-A. ROWNUM 을 먼저 자르고 정렬한다 (잘못된 순서) =====
SELECT ROWNUM, post_id, view_count FROM pg_post WHERE ROWNUM <= 5 ORDER BY view_count DESC;

PROMPT ===== 2-B. 인라인 뷰에서 먼저 정렬하고 바깥에서 자른다 =====
SELECT ROWNUM, post_id, view_count
FROM (SELECT post_id, view_count FROM pg_post ORDER BY view_count DESC)
WHERE ROWNUM <= 5;

PROMPT ===== 3-A. ROWNUM > 1 은 한 행도 돌려주지 않는다 =====
SELECT post_id FROM pg_post WHERE ROWNUM > 1;

PROMPT ===== 3-B. ROWNUM = 2 도 마찬가지 =====
SELECT post_id FROM pg_post WHERE ROWNUM = 2;

PROMPT ===== 3-C. ROWNUM = 1 은 된다 =====
SELECT post_id FROM pg_post WHERE ROWNUM = 1;

PROMPT ===== 4. 2페이지 (한 페이지 5행, 6~10번째) — 세 겹 인라인 뷰 =====
SELECT rn, post_id, view_count
FROM (
    SELECT ROWNUM AS rn, sorted.*
    FROM (SELECT post_id, view_count FROM pg_post ORDER BY view_count DESC, post_id) sorted
    WHERE ROWNUM <= 10
)
WHERE rn > 5;

PROMPT ===== 5-A. 정렬 키에 동점이 있으면 페이지 경계가 흔들린다 (post_id 없음) =====
SELECT rn, post_id, view_count
FROM (
    SELECT ROWNUM AS rn, sorted.*
    FROM (SELECT post_id, view_count FROM pg_post ORDER BY view_count DESC) sorted
    WHERE ROWNUM <= 10
)
WHERE rn > 5;

PROMPT ===== 6. 같은 2페이지를 row_limiting_clause 로 =====
SELECT post_id, view_count FROM pg_post
ORDER BY view_count DESC, post_id
OFFSET 5 ROWS FETCH NEXT 5 ROWS ONLY;

PROMPT ===== 7. 같은 2페이지를 LIMIT offset, limitnum 으로 =====
SELECT post_id, view_count FROM pg_post
ORDER BY view_count DESC, post_id
LIMIT 5, 5;

PROMPT ===== 8. 같은 2페이지를 ROW_NUMBER 로 =====
SELECT rn, post_id, view_count
FROM (
    SELECT ROW_NUMBER() OVER (ORDER BY view_count DESC, post_id) AS rn, post_id, view_count
    FROM pg_post
)
WHERE rn BETWEEN 6 AND 10;

PROMPT ===== 9. 2페이지 계획 비교 =====
SET AUTOTRACE TRACEONLY EXPLAIN
SELECT rn, post_id, view_count
FROM (
    SELECT ROWNUM AS rn, sorted.*
    FROM (SELECT post_id, view_count FROM pg_post ORDER BY view_count DESC, post_id) sorted
    WHERE ROWNUM <= 10
)
WHERE rn > 5;
SELECT post_id, view_count FROM pg_post
ORDER BY view_count DESC, post_id
OFFSET 5 ROWS FETCH NEXT 5 ROWS ONLY;
SET AUTOTRACE OFF

PROMPT ===== 10. 정리 =====
DROP TABLE pg_post;
SELECT COUNT(*) FROM user_objects;

EXIT
