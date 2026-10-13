-- Tibero 7 물리화 뷰 — 갱신 방식별 전제 조건 확인
--
-- 아직 돌리지 않았다. tbsql 이 있는 환경에서 돌려 출력을 채운다.
-- 빈 스키마에 mv_* 객체만 만들고 끝에서 전부 지운다. 기존 객체는 조회하지 않는다.
--
--   tbsql -s <사용자>/<암호> @mview_refresh_modes.sql
--
-- tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 -- 주석을 달면 다음 문장이 깨지므로
-- 설명은 PROMPT 로 적는다. 파일 끝의 EXIT 가 없으면 프롬프트에서 대기한다.

SET SERVEROUTPUT ON
SET LINESIZE 200
SET PAGESIZE 100

PROMPT ===== 0. 버전 =====
SELECT * FROM v$version;

PROMPT ===== 1. 마스터 표 두 개 =====
CREATE TABLE mv_dept (
    dept_no   NUMBER(4)    PRIMARY KEY,
    dept_name VARCHAR2(30) NOT NULL,
    region    VARCHAR2(20) NOT NULL
);

CREATE TABLE mv_emp (
    emp_no   NUMBER(6)    PRIMARY KEY,
    emp_name VARCHAR2(30) NOT NULL,
    dept_no  NUMBER(4)    NOT NULL,
    salary   NUMBER(10)   NOT NULL
);

INSERT INTO mv_dept VALUES (10, '개발', '서울');
INSERT INTO mv_dept VALUES (20, '영업', '부산');
INSERT INTO mv_emp  VALUES (1, '김하늘', 10, 4200000);
INSERT INTO mv_emp  VALUES (2, '이도윤', 10, 3800000);
INSERT INTO mv_emp  VALUES (3, '박서준', 20, 3500000);
COMMIT;

PROMPT ===== 2. 로그 없이 REFRESH FAST — TBR-7315 가 나와야 한다 =====
CREATE MATERIALIZED VIEW mv_emp_cnt
  REFRESH FAST ON DEMAND
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

PROMPT ===== 3. 같은 정의를 REFRESH FORCE 로 — 성공하되 FAST 가 아닐 수 있다 =====
CREATE MATERIALIZED VIEW mv_emp_cnt
  REFRESH FORCE ON DEMAND
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

SELECT mview_name, refresh_mode, refresh_method, build_mode,
       fast_refreshable, last_refresh_type, staleness
  FROM user_mviews WHERE mview_name = 'MV_EMP_CNT';

PROMPT ===== 4. 로그를 건다 — 집계이므로 신규 값과 필터 컬럼까지 =====
DROP MATERIALIZED VIEW mv_emp_cnt;

CREATE MATERIALIZED VIEW LOG ON mv_emp
  WITH PRIMARY KEY, ROWID, SEQUENCE (dept_no, salary)
  INCLUDING NEW VALUES;

SELECT master, log_table, rowids, primary_key, filter_columns,
       sequence, include_new_values
  FROM user_mview_logs WHERE master = 'MV_EMP';

PROMPT ===== 5. 이제 REFRESH FAST 가 만들어지는지 =====
CREATE MATERIALIZED VIEW mv_emp_cnt
  REFRESH FAST ON DEMAND
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

SELECT * FROM mv_emp_cnt ORDER BY dept_no;

PROMPT ===== 6. 마스터만 바꾸고 커밋 — ON DEMAND 이므로 뷰는 그대로여야 한다 =====
INSERT INTO mv_emp VALUES (4, '최지아', 20, 4500000);
COMMIT;

SELECT * FROM mv_emp_cnt ORDER BY dept_no;
SELECT mview_name, staleness, last_refresh_type FROM user_mviews
 WHERE mview_name = 'MV_EMP_CNT';

PROMPT ===== 7. 손으로 새로고침 — 'F' 는 빠른 새로고침을 강제한다 =====
EXEC DBMS_MVIEW.REFRESH('MV_EMP_CNT', 'F');

SELECT * FROM mv_emp_cnt ORDER BY dept_no;
SELECT mview_name, staleness, last_refresh_type, last_refresh_date
  FROM user_mviews WHERE mview_name = 'MV_EMP_CNT';

PROMPT ===== 8. ON COMMIT 으로 다시 만든다 =====
DROP MATERIALIZED VIEW mv_emp_cnt;

CREATE MATERIALIZED VIEW mv_emp_cnt
  REFRESH FAST ON COMMIT
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

INSERT INTO mv_emp VALUES (5, '정민재', 10, 3200000);
COMMIT;

SELECT * FROM mv_emp_cnt ORDER BY dept_no;
SELECT mview_name, refresh_mode, last_refresh_type FROM user_mviews
 WHERE mview_name = 'MV_EMP_CNT';

PROMPT ===== 9. ON COMMIT 과 START WITH 를 함께 — 매뉴얼은 금지한다 =====
CREATE MATERIALIZED VIEW mv_bad
  REFRESH FAST ON COMMIT START WITH SYSDATE NEXT SYSDATE + 1
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

PROMPT ===== 10. 빠른 새로고침이 안 되는 정의 질의 — TBR-7318 =====
CREATE MATERIALIZED VIEW mv_complex
  REFRESH FAST ON DEMAND
  AS SELECT dept_no, emp_name,
            ROW_NUMBER() OVER (PARTITION BY dept_no ORDER BY salary DESC) AS rnk
       FROM mv_emp;

PROMPT ===== 11. NEVER REFRESH 를 손으로 새로고침 — TBR-7329 =====
CREATE MATERIALIZED VIEW mv_frozen
  NEVER REFRESH
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

EXEC DBMS_MVIEW.REFRESH('MV_FROZEN', 'C');

PROMPT ===== 12. BUILD DEFERRED — 만든 직후에는 비어 있어야 한다 =====
CREATE MATERIALIZED VIEW mv_later
  BUILD DEFERRED
  REFRESH COMPLETE ON DEMAND
  AS SELECT dept_no, COUNT(*) AS emp_cnt FROM mv_emp GROUP BY dept_no;

SELECT COUNT(*) AS rows_before FROM mv_later;
EXEC DBMS_MVIEW.REFRESH('MV_LATER', '?');
SELECT COUNT(*) AS rows_after FROM mv_later;
SELECT mview_name, build_mode, last_refresh_type FROM user_mviews
 WHERE mview_name = 'MV_LATER';

PROMPT ===== 13. 정리 — 만든 것만 지운다 =====
DROP MATERIALIZED VIEW mv_later;
DROP MATERIALIZED VIEW mv_frozen;
DROP MATERIALIZED VIEW mv_emp_cnt;
DROP MATERIALIZED VIEW LOG ON mv_emp;
DROP TABLE mv_emp;
DROP TABLE mv_dept;

SELECT COUNT(*) AS left_objects FROM user_objects;

EXIT
