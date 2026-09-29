SET LINESIZE 200
SET PAGESIZE 200
SET ECHO ON
PROMPT ===== 0. 버전과 시작 시점 객체 수 =====
SELECT * FROM v$version;
SELECT COUNT(*) AS obj_before FROM user_objects;
PROMPT ===== 1. 예제 테이블과 통계 =====
CREATE TABLE hint_dept (
  dept_id    NUMBER       NOT NULL,
  dept_name  VARCHAR(30)  NOT NULL,
  CONSTRAINT pk_hint_dept PRIMARY KEY (dept_id)
);
CREATE TABLE hint_emp (
  emp_id     NUMBER       NOT NULL,
  dept_id    NUMBER       NOT NULL,
  emp_name   VARCHAR(30)  NOT NULL,
  CONSTRAINT pk_hint_emp PRIMARY KEY (emp_id)
);
CREATE INDEX ix_hint_emp_dept ON hint_emp (dept_id);
INSERT INTO hint_dept SELECT LEVEL, 'D' || LEVEL FROM dual CONNECT BY LEVEL <= 20;
INSERT INTO hint_emp SELECT LEVEL, MOD(LEVEL, 20) + 1, 'E' || LEVEL FROM dual CONNECT BY LEVEL <= 20000;
COMMIT;
EXEC DBMS_STATS.GATHER_TABLE_STATS(USER, 'HINT_DEPT');
EXEC DBMS_STATS.GATHER_TABLE_STATS(USER, 'HINT_EMP');
SET AUTOTRACE TRACEONLY EXPLAIN
PROMPT ===== 2. 힌트 없음 — 기준 계획 =====
SELECT e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 3. FULL — 별칭으로 적었다 =====
SELECT /*+ FULL(e) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 4. FULL — 별칭이 있는데 테이블 이름으로 적었다 =====
SELECT /*+ FULL(hint_emp) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 5. 주석 구분자와 + 사이에 공백 =====
SELECT /* +FULL(e) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 6. 힌트 이름 오타 — 오류 없이 주석이 되어야 한다 =====
SELECT /*+ FUL(e) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 7. 같은 인덱스에 INDEX 와 NO_INDEX — 둘 다 무시되어야 한다 =====
SELECT /*+ INDEX(e ix_hint_emp_dept) NO_INDEX(e ix_hint_emp_dept) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
PROMPT ===== 8. INDEX — 쓸 수 없는 인덱스를 지정 =====
SELECT /*+ INDEX(e pk_hint_emp) */ e.emp_name FROM hint_emp e WHERE e.emp_name = 'E7';
PROMPT ===== 9. 조인 순서 — LEADING 과 ORDERED 를 함께 =====
SELECT /*+ LEADING(e d) USE_NL(d) */ d.dept_name, e.emp_name FROM hint_dept d, hint_emp e WHERE d.dept_id = e.dept_id AND e.emp_id = 100;
SELECT /*+ ORDERED LEADING(e d) */ d.dept_name, e.emp_name FROM hint_dept d, hint_emp e WHERE d.dept_id = e.dept_id AND e.emp_id = 100;
PROMPT ===== 10. 인라인 뷰 안의 힌트 — 질의 블록마다 힌트 주석 하나 =====
SELECT * FROM hint_dept d, (SELECT /*+ NO_MERGE */ dept_id, COUNT(*) AS cnt FROM hint_emp GROUP BY dept_id) v WHERE d.dept_id = v.dept_id;
SET AUTOTRACE OFF
PROMPT ===== 11. IGNORE_ROW_ON_DUPKEY_INDEX — 인덱스를 빠뜨리면 오류가 나야 한다 =====
INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX */ INTO hint_dept VALUES (1, 'DUP');
INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX(hint_dept pk_hint_dept) */ INTO hint_dept SELECT dept_id + 18, 'NEW' FROM hint_dept WHERE dept_id <= 4;
SELECT COUNT(*) AS dept_cnt FROM hint_dept;
ROLLBACK;
PROMPT ===== 12. EXPLAIN PLAN 과 DBMS_XPLAN — OUTLINE 에 적용된 힌트가 보이는가 =====
EXPLAIN PLAN FOR SELECT /*+ FULL(e) */ e.emp_name FROM hint_emp e WHERE e.dept_id = 7;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('ALL'));
ROLLBACK;
PROMPT ===== 13. 정리 =====
DROP TABLE hint_emp;
DROP TABLE hint_dept;
SELECT COUNT(*) AS obj_left FROM user_objects;
EXIT
