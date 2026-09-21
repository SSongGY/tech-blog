SET LINESIZE 200
SET PAGESIZE 200
COLUMN emp_name FORMAT A10
COLUMN dept_name FORMAT A8
COLUMN root_name FORMAT A10
COLUMN path FORMAT A34
--
-- 0. 예제 객체 생성
--
CREATE TABLE emp_org (
  emp_id    NUMBER PRIMARY KEY,
  emp_name  VARCHAR(30) NOT NULL,
  mgr_id    NUMBER,
  dept_name VARCHAR(30)
);
INSERT INTO emp_org VALUES (1, '한지원', NULL, '경영');
INSERT INTO emp_org VALUES (2, '오세훈', 1, '개발');
INSERT INTO emp_org VALUES (3, '배수진', 1, '영업');
INSERT INTO emp_org VALUES (4, '노태경', 2, '개발');
INSERT INTO emp_org VALUES (5, '임하윤', 2, '개발');
INSERT INTO emp_org VALUES (6, '구민재', 4, '개발');
INSERT INTO emp_org VALUES (7, '서아린', 3, '영업');
CREATE TABLE ring_org (
  emp_id   NUMBER PRIMARY KEY,
  emp_name VARCHAR(30) NOT NULL,
  mgr_id   NUMBER
);
INSERT INTO ring_org VALUES (10, '문가영', 12);
INSERT INTO ring_org VALUES (11, '표진우', 10);
INSERT INTO ring_org VALUES (12, '연수아', 11);
COMMIT;
--
-- 1. 기본형 — 루트에서 아래로. ORDER SIBLINGS BY 로 형제만 정렬한다
--
SELECT LEVEL, emp_id, emp_name, mgr_id
  FROM emp_org
 START WITH mgr_id IS NULL
 CONNECT BY PRIOR emp_id = mgr_id
 ORDER SIBLINGS BY emp_id;
--
-- 2. 의사 컬럼 네 가지를 한 번에
--
SELECT LEVEL,
       emp_name,
       CONNECT_BY_ROOT emp_name AS root_name,
       CONNECT_BY_ISLEAF AS is_leaf,
       SYS_CONNECT_BY_PATH(emp_name, '/') AS path
  FROM emp_org
 START WITH mgr_id IS NULL
 CONNECT BY PRIOR emp_id = mgr_id
 ORDER SIBLINGS BY emp_id;
--
-- 3. PRIOR 를 반대쪽에 붙이면 잎에서 뿌리로 거슬러 올라간다
--
SELECT LEVEL, emp_name
  FROM emp_org
 START WITH emp_id = 6
 CONNECT BY PRIOR mgr_id = emp_id;
--
-- 4. WHERE 로 거르면 그 사람만 빠지고 부하는 남는다
--
SELECT LEVEL, emp_name
  FROM emp_org
 WHERE emp_name <> '오세훈'
 START WITH mgr_id IS NULL
 CONNECT BY PRIOR emp_id = mgr_id
 ORDER SIBLINGS BY emp_id;
--
-- 5. 같은 조건을 CONNECT BY 에 두면 가지째 잘린다
--
SELECT LEVEL, emp_name
  FROM emp_org
 START WITH mgr_id IS NULL
 CONNECT BY PRIOR emp_id = mgr_id AND emp_name <> '오세훈'
 ORDER SIBLINGS BY emp_id;
--
-- 6. 일반 ORDER BY 는 계층 순서를 무너뜨린다
--
SELECT LEVEL, emp_name
  FROM emp_org
 START WITH mgr_id IS NULL
 CONNECT BY PRIOR emp_id = mgr_id
 ORDER BY emp_name;
--
-- 7. START WITH 를 빼면 모든 행이 루트가 된다. 7행 테이블에서 18행
--
SELECT COUNT(*) AS NO_START_WITH_ROWS
  FROM emp_org
 CONNECT BY PRIOR emp_id = mgr_id;
--
-- 8. 순환 참조 — 에러로 멈춘다
--
SELECT LEVEL, emp_id, emp_name
  FROM ring_org
 START WITH emp_id = 10
 CONNECT BY PRIOR emp_id = mgr_id;
--
-- 9. NOCYCLE 을 붙이면 멈추고, CONNECT_BY_ISCYCLE 이 고리를 닫는 행을 가리킨다
--
SELECT LEVEL, emp_id, emp_name, CONNECT_BY_ISCYCLE AS is_cycle
  FROM ring_org
 START WITH emp_id = 10
 CONNECT BY NOCYCLE PRIOR emp_id = mgr_id;
--
-- 10. NOCYCLE 없이 CONNECT_BY_ISCYCLE 만 쓰면 막힌다
--
SELECT emp_id, CONNECT_BY_ISCYCLE AS is_cycle
  FROM ring_org
 START WITH emp_id = 10
 CONNECT BY PRIOR emp_id = mgr_id;
--
-- 11. LEVEL 을 CONNECT BY 에 두면 순환 테이블도 끝난다
--
SELECT LEVEL, emp_name
  FROM ring_org
 START WITH emp_id = 10
 CONNECT BY PRIOR emp_id = mgr_id AND LEVEL <= 3;
--
-- 12. 같은 LEVEL 조건을 WHERE 에 두면 순회가 멈추지 않아 에러다
--
SELECT LEVEL, emp_name
  FROM ring_org
 WHERE LEVEL <= 3
 START WITH emp_id = 10
 CONNECT BY PRIOR emp_id = mgr_id;
--
-- 13. PRIOR 가 없는 CONNECT BY. 매뉴얼은 에러라고 적었다
--
SELECT LEVEL, emp_name
  FROM emp_org
 START WITH mgr_id IS NULL
 CONNECT BY emp_id = mgr_id;
--
-- 14. PRIOR 가 둘인 CONNECT BY. 매뉴얼은 에러라고 적었다
--
SELECT LEVEL, emp_name, dept_name
  FROM emp_org
 START WITH emp_id = 2
 CONNECT BY PRIOR emp_id = mgr_id AND PRIOR dept_name = dept_name;
--
-- 15. 정리. 남은 객체가 0개여야 한다
--
DROP TABLE emp_org;
DROP TABLE ring_org;
SELECT COUNT(*) AS OBJ_LEFT FROM user_objects;
EXIT
