SET LINESIZE 200
SET PAGESIZE 100

PROMPT ==== 0. 버전 ====
SELECT product_major, product_minor FROM v$version;

PROMPT ==== 1. 다섯 가지 제약조건을 가진 표 두 개 ====
CREATE TABLE cs_dept (
    dept_no   NUMBER        CONSTRAINT cs_dept_pk PRIMARY KEY,
    dept_name VARCHAR2(30)  NOT NULL
);

CREATE TABLE cs_emp (
    emp_no    NUMBER        CONSTRAINT cs_emp_pk PRIMARY KEY,
    email     VARCHAR2(40)  CONSTRAINT cs_emp_email_uk UNIQUE,
    salary    NUMBER,
    dept_no   NUMBER,
    CONSTRAINT cs_emp_salary_ck CHECK (salary >= 1000),
    CONSTRAINT cs_emp_dept_fk FOREIGN KEY (dept_no) REFERENCES cs_dept (dept_no)
);

INSERT INTO cs_dept VALUES (10, '개발');
INSERT INTO cs_dept VALUES (20, '영업');
INSERT INTO cs_emp VALUES (1, 'a@example.com', 3000, 10);
INSERT INTO cs_emp VALUES (2, 'b@example.com', 2500, 20);
COMMIT;

DESC cs_emp
SELECT * FROM cs_dept ORDER BY dept_no;
SELECT * FROM cs_emp ORDER BY emp_no;

PROMPT ==== 1-A. 생성 직후 상태 — 이름을 안 준 NOT NULL 은 시스템 이름 ====
COLUMN constraint_name FORMAT A22
COLUMN table_name FORMAT A8
COLUMN index_name FORMAT A22
SELECT constraint_name, table_name, constraint_type, status, validated,
       deferrable, deferred, generated, index_name
FROM user_constraints
WHERE table_name IN ('CS_DEPT', 'CS_EMP')
ORDER BY table_name, constraint_name;

PROMPT ==== 1-B. FOREIGN KEY 컬럼에 인덱스가 생겼는가 ====
SELECT index_name, table_name, uniqueness
FROM user_indexes
WHERE table_name IN ('CS_DEPT', 'CS_EMP')
ORDER BY table_name, index_name;

PROMPT ==== 2. ENABLE VALIDATE 상태에서 위반 — 문장 단위로 거부 ====
INSERT INTO cs_emp VALUES (3, 'c@example.com', 500, 10);
INSERT INTO cs_emp VALUES (3, 'c@example.com', 1500, 99);
INSERT INTO cs_emp VALUES (3, 'a@example.com', 1500, 10);
ROLLBACK;

PROMPT ==== 3. CHECK 를 끄고 위반 행을 넣는다 ====
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck DISABLE;
INSERT INTO cs_emp VALUES (3, 'c@example.com', 500, 10);
COMMIT;
SELECT constraint_name, status, validated FROM user_constraints
WHERE constraint_name = 'CS_EMP_SALARY_CK';

PROMPT ==== 3-A. ENABLE VALIDATE — 기존 위반 행 때문에 실패해야 한다 ====
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck ENABLE VALIDATE;
SELECT constraint_name, status, validated FROM user_constraints
WHERE constraint_name = 'CS_EMP_SALARY_CK';

PROMPT ==== 3-B. ENABLE NOVALIDATE — 기존 행은 두고 새 행만 검사 ====
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck ENABLE NOVALIDATE;
SELECT constraint_name, status, validated FROM user_constraints
WHERE constraint_name = 'CS_EMP_SALARY_CK';
INSERT INTO cs_emp VALUES (4, 'd@example.com', 700, 10);
UPDATE cs_emp SET salary = 600 WHERE emp_no = 3;
ROLLBACK;
SELECT * FROM cs_emp ORDER BY emp_no;

PROMPT ==== 3-C. 위반 행을 고친 뒤 VALIDATE ====
UPDATE cs_emp SET salary = 1000 WHERE emp_no = 3;
COMMIT;
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck ENABLE VALIDATE;
SELECT constraint_name, status, validated FROM user_constraints
WHERE constraint_name = 'CS_EMP_SALARY_CK';

PROMPT ==== 4. UNIQUE 를 끄고 중복을 넣은 뒤 ENABLE NOVALIDATE ====
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_email_uk DISABLE;
INSERT INTO cs_emp VALUES (5, 'a@example.com', 2000, 10);
COMMIT;
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_email_uk ENABLE NOVALIDATE;
SELECT constraint_name, status, validated, index_name FROM user_constraints
WHERE constraint_name = 'CS_EMP_EMAIL_UK';
DELETE FROM cs_emp WHERE emp_no = 5;
COMMIT;
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_email_uk ENABLE;
SELECT constraint_name, status, validated, index_name FROM user_constraints
WHERE constraint_name = 'CS_EMP_EMAIL_UK';

PROMPT ==== 5. DISABLE VALIDATE — DML 이 막혀야 한다 ====
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck DISABLE VALIDATE;
SELECT constraint_name, status, validated FROM user_constraints
WHERE constraint_name = 'CS_EMP_SALARY_CK';
INSERT INTO cs_emp VALUES (6, 'f@example.com', 5000, 10);
UPDATE cs_emp SET salary = salary + 1 WHERE emp_no = 1;
ROLLBACK;
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_salary_ck ENABLE VALIDATE;

PROMPT ---- 5-A. UNIQUE 를 DISABLE VALIDATE 로 — 인덱스가 남는가 ----
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_email_uk DISABLE VALIDATE;
SELECT constraint_name, status, validated, index_name FROM user_constraints
WHERE constraint_name = 'CS_EMP_EMAIL_UK';
SELECT index_name FROM user_indexes WHERE table_name = 'CS_EMP' ORDER BY index_name;
ALTER TABLE cs_emp MODIFY CONSTRAINT cs_emp_email_uk ENABLE;

PROMPT ==== 6. 참조되는 PK 를 CASCADE 없이 끄면 ====
ALTER TABLE cs_dept MODIFY CONSTRAINT cs_dept_pk DISABLE;

PROMPT ==== 7. DEFERRABLE INITIALLY DEFERRED — 좌석 번호 맞바꾸기 ====
CREATE TABLE cs_seat (
    guest   VARCHAR2(10) PRIMARY KEY,
    seat_no NUMBER CONSTRAINT cs_seat_no_uk UNIQUE DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE cs_seat_now (
    guest   VARCHAR2(10) PRIMARY KEY,
    seat_no NUMBER CONSTRAINT cs_seat_now_uk UNIQUE
);
INSERT INTO cs_seat VALUES ('kim', 1);
INSERT INTO cs_seat VALUES ('lee', 2);
INSERT INTO cs_seat_now VALUES ('kim', 1);
INSERT INTO cs_seat_now VALUES ('lee', 2);
COMMIT;
SELECT constraint_name, deferrable, deferred, index_name FROM user_constraints
WHERE constraint_name IN ('CS_SEAT_NO_UK', 'CS_SEAT_NOW_UK');
SELECT index_name, uniqueness FROM user_indexes
WHERE table_name IN ('CS_SEAT', 'CS_SEAT_NOW') ORDER BY index_name;

PROMPT ---- 7-A. 즉시 검사 표에서 한 행씩 맞바꾸면 ----
UPDATE cs_seat_now SET seat_no = 2 WHERE guest = 'kim';
ROLLBACK;

PROMPT ---- 7-B. 지연 검사 표에서 한 행씩 맞바꾸면 ----
UPDATE cs_seat SET seat_no = 2 WHERE guest = 'kim';
UPDATE cs_seat SET seat_no = 1 WHERE guest = 'lee';
COMMIT;
SELECT * FROM cs_seat ORDER BY guest;

PROMPT ---- 7-C. 위반을 남긴 채 COMMIT — 마지막 COMMIT 이후 변경이 모두 취소되는가 ----
INSERT INTO cs_seat VALUES ('park', 3);
UPDATE cs_seat SET seat_no = 3 WHERE guest = 'kim';
COMMIT;
SELECT * FROM cs_seat ORDER BY guest;

PROMPT ==== 8. FOREIGN KEY 에 DEFERRABLE — 매뉴얼은 쓸 수 없다고 적는다 ====
CREATE TABLE cs_child (
    id      NUMBER PRIMARY KEY,
    dept_no NUMBER CONSTRAINT cs_child_fk REFERENCES cs_dept (dept_no)
                   DEFERRABLE INITIALLY DEFERRED
);

PROMPT ==== 9. 정리 ====
DROP TABLE cs_child;
DROP TABLE cs_seat_now;
DROP TABLE cs_seat;
DROP TABLE cs_emp;
DROP TABLE cs_dept;
SELECT COUNT(*) AS remaining_objects FROM user_objects;

EXIT
