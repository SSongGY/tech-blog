SET LINESIZE 140
SET PAGESIZE 200
SET FEEDBACK ON
SET ECHO ON

PROMPT ===== 0. 준비 =====
CREATE TABLE sale_daily (
  sale_day NUMBER NOT NULL,
  amount   NUMBER NOT NULL
);
INSERT INTO sale_daily VALUES (1, 10);
INSERT INTO sale_daily VALUES (2, 20);
INSERT INTO sale_daily VALUES (3, 30);
INSERT INTO sale_daily VALUES (3, 40);
INSERT INTO sale_daily VALUES (5, 50);
INSERT INTO sale_daily VALUES (8, 60);
INSERT INTO sale_daily VALUES (9, 70);
COMMIT;
SELECT sale_day, amount FROM sale_daily ORDER BY sale_day, amount;

PROMPT ===== 1. ORDER BY 만 쓰면 기본 윈도우가 RANGE 다 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day) AS default_win,
       SUM(amount) OVER (ORDER BY sale_day
            RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS range_win,
       SUM(amount) OVER (ORDER BY sale_day
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_win
  FROM sale_daily
 ORDER BY sale_day, amount;

PROMPT ===== 2. ORDER BY 가 없으면 파티션 전체가 윈도우다 =====
SELECT sale_day, amount,
       SUM(amount) OVER () AS whole_set
  FROM sale_daily
 ORDER BY sale_day, amount;

PROMPT ===== 3. ROWS 2 PRECEDING 과 RANGE 2 PRECEDING =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rows_2p,
       COUNT(*) OVER (ORDER BY sale_day
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rows_cnt,
       SUM(amount) OVER (ORDER BY sale_day
            RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_2p,
       COUNT(*) OVER (ORDER BY sale_day
            RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_cnt
  FROM sale_daily
 ORDER BY sale_day, amount;

PROMPT ===== 4. LAST_VALUE 는 기본 윈도우에서 현재 행까지만 본다 =====
SELECT sale_day, amount,
       FIRST_VALUE(amount) OVER (ORDER BY sale_day) AS first_default,
       LAST_VALUE(amount) OVER (ORDER BY sale_day) AS last_default,
       LAST_VALUE(amount) OVER (ORDER BY sale_day
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_full
  FROM sale_daily
 ORDER BY sale_day, amount;

PROMPT ===== 5. RANGE 에 정렬 키를 둘 주면 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day, amount
            RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS bad_range
  FROM sale_daily;

PROMPT ===== 6. ROWS 에 정렬 키를 둘 주면 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day, amount
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ok_rows
  FROM sale_daily
 ORDER BY sale_day, amount;

PROMPT ===== 7. 윈도우 절을 순위 함수에 붙이면 =====
SELECT sale_day, amount,
       RANK() OVER (ORDER BY sale_day
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_rank
  FROM sale_daily;

PROMPT ===== 8. RANGE 오프셋에 음수를 주면 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day
            RANGE BETWEEN -1 PRECEDING AND CURRENT ROW) AS bad_offset
  FROM sale_daily;

PROMPT ===== 9. 앞뒤를 뒤집어 주면 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ORDER BY sale_day
            ROWS BETWEEN CURRENT ROW AND 2 PRECEDING) AS bad_order
  FROM sale_daily;

PROMPT ===== 10. ORDER BY 없이 ROWS 를 쓰면 =====
SELECT sale_day, amount,
       SUM(amount) OVER (ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS no_order
  FROM sale_daily;

PROMPT ===== 11. 다른 순위·오프셋 함수에도 붙여 보면 =====
SELECT ROW_NUMBER() OVER (ORDER BY sale_day
         ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_rownum FROM sale_daily;
SELECT DENSE_RANK() OVER (ORDER BY sale_day
         ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_dense FROM sale_daily;
SELECT LEAD(amount) OVER (ORDER BY sale_day
         ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_lead FROM sale_daily;
SELECT LAG(amount) OVER (ORDER BY sale_day
         ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_lag FROM sale_daily;
SELECT NTILE(2) OVER (ORDER BY sale_day
         ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS bad_ntile FROM sale_daily;

PROMPT ===== 정리 =====
DROP TABLE sale_daily;
SELECT COUNT(*) AS obj_left FROM user_objects;
EXIT
