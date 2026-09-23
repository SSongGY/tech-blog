SET LINESIZE 140
SET PAGESIZE 200
SET FEEDBACK ON
SET ECHO ON

PROMPT ===== 0. 시작 전 스키마가 비어 있는지 =====
SELECT COUNT(*) AS obj_before FROM user_objects;
COLUMN name FORMAT A16
COLUMN value FORMAT A10
SELECT name, value FROM v$version WHERE name IN ('PRODUCT_MAJOR', 'PRODUCT_MINOR');

PROMPT ===== 1. RANGE - MAXVALUE 없이 범위 밖 값을 넣으면 =====
CREATE TABLE sale_range (
  sale_id NUMBER NOT NULL,
  sold_on DATE,
  amount  NUMBER NOT NULL
)
PARTITION BY RANGE (sold_on) (
  PARTITION p2026q1 VALUES LESS THAN (DATE '2026-04-01'),
  PARTITION p2026q2 VALUES LESS THAN (DATE '2026-07-01'),
  PARTITION p2026q3 VALUES LESS THAN (DATE '2026-10-01')
);
INSERT INTO sale_range VALUES (1, DATE '2026-01-15', 100);
INSERT INTO sale_range VALUES (2, DATE '2026-03-31', 200);
INSERT INTO sale_range VALUES (3, DATE '2026-04-01', 300);
INSERT INTO sale_range VALUES (4, DATE '2026-09-30', 400);
INSERT INTO sale_range VALUES (5, DATE '2026-10-01', 500);
INSERT INTO sale_range VALUES (6, NULL, 600);
COMMIT;

PROMPT ===== 1-B. 각 파티션에 들어간 행 =====
SELECT 'P2026Q1' AS part, sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range PARTITION (p2026q1)
UNION ALL
SELECT 'P2026Q2', sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range PARTITION (p2026q2)
UNION ALL
SELECT 'P2026Q3', sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range PARTITION (p2026q3)
ORDER BY 2;

PROMPT ===== 1-C. MAXVALUE 파티션을 더하면 NULL 도 들어간다 =====
ALTER TABLE sale_range ADD PARTITION pmax VALUES LESS THAN (MAXVALUE);
INSERT INTO sale_range VALUES (5, DATE '2026-10-01', 500);
INSERT INTO sale_range VALUES (6, NULL, 600);
COMMIT;
SELECT sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range PARTITION (pmax) ORDER BY sale_id;

PROMPT ===== 1-D. 파티션 키를 바꾸는 UPDATE =====
UPDATE sale_range SET sold_on = DATE '2026-05-10' WHERE sale_id = 1;
ROLLBACK;
ALTER TABLE sale_range ENABLE ROW MOVEMENT;
UPDATE sale_range SET sold_on = DATE '2026-05-10' WHERE sale_id = 1;
SELECT sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range PARTITION (p2026q2) ORDER BY sale_id;
ROLLBACK;

PROMPT ===== 1-E. 파티션 키 조건과 실행계획 =====
SET AUTOTRACE TRACEONLY EXPLAIN
SELECT sale_id, amount FROM sale_range WHERE sold_on >= DATE '2026-07-01';
SELECT sale_id, amount FROM sale_range WHERE TO_CHAR(sold_on, 'YYYYMM') >= '202607';
SET AUTOTRACE OFF

PROMPT ===== 1-F. 오래된 분기를 통째로 지운다 =====
ALTER TABLE sale_range DROP PARTITION p2026q1;
SELECT sale_id, TO_CHAR(sold_on, 'YYYY-MM-DD') AS sold_on FROM sale_range ORDER BY sale_id;

PROMPT ===== 2. INTERVAL - 선언하지 않은 범위가 들어오면 =====
CREATE TABLE sale_interval (
  sale_id NUMBER NOT NULL,
  sold_on DATE NOT NULL
)
PARTITION BY RANGE (sold_on) INTERVAL (NUMTOYMINTERVAL(1, 'MONTH')) (
  PARTITION p202609 VALUES LESS THAN (DATE '2026-10-01')
);
INSERT INTO sale_interval VALUES (1, DATE '2026-09-10');
INSERT INTO sale_interval VALUES (2, DATE '2026-10-05');
INSERT INTO sale_interval VALUES (3, DATE '2027-01-20');
COMMIT;
COLUMN partition_name FORMAT A16
COLUMN bound FORMAT A40
SELECT partition_no, partition_name, bound
  FROM user_tab_partitions
 WHERE table_name = 'SALE_INTERVAL'
 ORDER BY partition_no;

PROMPT ===== 3. LIST - 목록에 없는 값과 DEFAULT =====
CREATE TABLE store_list (
  store_id NUMBER NOT NULL,
  region   VARCHAR(10)
)
PARTITION BY LIST (region) (
  PARTITION p_capital VALUES ('SEOUL', 'GYEONGGI'),
  PARTITION p_south   VALUES ('BUSAN', 'ULSAN')
);
INSERT INTO store_list VALUES (1, 'SEOUL');
INSERT INTO store_list VALUES (2, 'BUSAN');
INSERT INTO store_list VALUES (3, 'JEJU');
INSERT INTO store_list VALUES (4, NULL);
ALTER TABLE store_list ADD PARTITION p_etc VALUES (DEFAULT);
INSERT INTO store_list VALUES (3, 'JEJU');
INSERT INTO store_list VALUES (4, NULL);
COMMIT;
SELECT 'P_CAPITAL' AS part, store_id, region FROM store_list PARTITION (p_capital)
UNION ALL
SELECT 'P_SOUTH', store_id, region FROM store_list PARTITION (p_south)
UNION ALL
SELECT 'P_ETC', store_id, region FROM store_list PARTITION (p_etc)
ORDER BY 2;

PROMPT ===== 3-B. LIST 키는 컬럼 하나만 =====
CREATE TABLE store_list2 (
  store_id NUMBER NOT NULL,
  region   VARCHAR(10),
  channel  VARCHAR(10)
)
PARTITION BY LIST (region, channel) (
  PARTITION p1 VALUES (('SEOUL', 'WEB'))
);

PROMPT ===== 4. HASH - 1000 행을 4 개로 =====
CREATE TABLE member_hash (
  member_id NUMBER NOT NULL,
  name      VARCHAR(20)
)
PARTITION BY HASH (member_id) PARTITIONS 4;
INSERT INTO member_hash SELECT LEVEL, 'M' || LEVEL FROM dual CONNECT BY LEVEL <= 1000;
COMMIT;
EXEC DBMS_STATS.GATHER_TABLE_STATS('TIBERO', 'MEMBER_HASH');
SELECT partition_no, partition_name, num_rows
  FROM user_tab_partitions
 WHERE table_name = 'MEMBER_HASH'
 ORDER BY partition_no;

PROMPT ===== 4-B. 파티션 수를 3 개로 하면 =====
CREATE TABLE member_hash3 (
  member_id NUMBER NOT NULL
)
PARTITION BY HASH (member_id) PARTITIONS 3;
INSERT INTO member_hash3 SELECT LEVEL FROM dual CONNECT BY LEVEL <= 1000;
COMMIT;
EXEC DBMS_STATS.GATHER_TABLE_STATS('TIBERO', 'MEMBER_HASH3');
SELECT partition_no, partition_name, num_rows
  FROM user_tab_partitions
 WHERE table_name = 'MEMBER_HASH3'
 ORDER BY partition_no;

PROMPT ===== 4-C. 파티션 수를 5 개, 8 개로 하면 =====
CREATE TABLE member_hash5 (
  member_id NUMBER NOT NULL
)
PARTITION BY HASH (member_id) PARTITIONS 5;
INSERT INTO member_hash5 SELECT LEVEL FROM dual CONNECT BY LEVEL <= 1000;
CREATE TABLE member_hash8 (
  member_id NUMBER NOT NULL
)
PARTITION BY HASH (member_id) PARTITIONS 8;
INSERT INTO member_hash8 SELECT LEVEL FROM dual CONNECT BY LEVEL <= 1000;
COMMIT;
EXEC DBMS_STATS.GATHER_TABLE_STATS('TIBERO', 'MEMBER_HASH5');
EXEC DBMS_STATS.GATHER_TABLE_STATS('TIBERO', 'MEMBER_HASH8');
SELECT table_name, partition_no, num_rows
  FROM user_tab_partitions
 WHERE table_name IN ('MEMBER_HASH5', 'MEMBER_HASH8')
 ORDER BY table_name, partition_no;

PROMPT ===== 4-D. 파티션 종류 요약 =====
COLUMN table_name FORMAT A16
SELECT table_name, partitioning_type, subpartitioning_type, partition_count, partitioning_key_count
  FROM user_part_tables
 ORDER BY table_name;

PROMPT ===== 5. COMPOSITE - RANGE 아래 LIST =====
CREATE TABLE sale_composite (
  sale_id NUMBER NOT NULL,
  sold_on DATE NOT NULL,
  channel VARCHAR(10) NOT NULL
)
PARTITION BY RANGE (sold_on)
SUBPARTITION BY LIST (channel)
SUBPARTITION TEMPLATE (
  SUBPARTITION s_web   VALUES ('WEB'),
  SUBPARTITION s_store VALUES ('STORE'),
  SUBPARTITION s_etc   VALUES (DEFAULT)
) (
  PARTITION p2026h1 VALUES LESS THAN (DATE '2026-07-01'),
  PARTITION p2026h2 VALUES LESS THAN (DATE '2027-01-01')
);
INSERT INTO sale_composite VALUES (1, DATE '2026-02-01', 'WEB');
INSERT INTO sale_composite VALUES (2, DATE '2026-08-01', 'STORE');
INSERT INTO sale_composite VALUES (3, DATE '2026-08-02', 'PHONE');
COMMIT;
COLUMN subpartition_name FORMAT A20
SELECT partition_name, subpartition_name
  FROM user_tab_subpartitions
 WHERE table_name = 'SALE_COMPOSITE'
 ORDER BY partition_name, subpartition_no;
SELECT sale_id, channel FROM sale_composite SUBPARTITION (p2026h2_s_etc);

PROMPT ===== 6. 정리 =====
DROP TABLE sale_range PURGE;
DROP TABLE sale_interval PURGE;
DROP TABLE store_list PURGE;
DROP TABLE member_hash PURGE;
DROP TABLE member_hash3 PURGE;
DROP TABLE member_hash5 PURGE;
DROP TABLE member_hash8 PURGE;
DROP TABLE sale_composite PURGE;
SELECT COUNT(*) AS obj_left FROM user_objects;

EXIT
