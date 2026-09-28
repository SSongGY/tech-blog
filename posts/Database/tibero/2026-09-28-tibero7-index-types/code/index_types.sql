SET LINESIZE 200
SET PAGESIZE 200
SET ECHO ON
PROMPT ===== 0. 버전과 시작 시점 객체 수 =====
SELECT * FROM v$version;
SELECT COUNT(*) AS obj_before FROM user_objects;
PROMPT ===== 1. 예제 테이블 =====
CREATE TABLE member_account (
  member_id  NUMBER       NOT NULL,
  email      VARCHAR(100) NOT NULL,
  grade      VARCHAR(10)  NOT NULL,
  joined_at  DATE         NOT NULL
);
PROMPT ===== 2. UNIQUE — 중복 키를 넣으면 TBR-10007 이 나와야 한다 =====
CREATE UNIQUE INDEX ux_member_account_member_id ON member_account (member_id);
INSERT INTO member_account VALUES (1, 'a@example.com', 'GOLD', SYSDATE);
INSERT INTO member_account VALUES (1, 'b@example.com', 'GOLD', SYSDATE);
PROMPT ===== 3. 같은 키로 또 만들면 TBR-7124 가 나와야 한다 =====
CREATE UNIQUE INDEX ux_member_account_dup ON member_account (member_id);
PROMPT ===== 4. 함수 기반 — UPPER 는 된다, SYSDATE 는 TBR-8082 =====
CREATE INDEX ix_member_account_upper_email ON member_account (UPPER(email));
CREATE INDEX ix_member_account_sysdate ON member_account (SYSDATE);
PROMPT ===== 5. BITMAP — COMPRESS 를 붙이면 TBR-7013 =====
CREATE BITMAP INDEX ix_member_account_grade ON member_account (grade);
CREATE BITMAP INDEX ix_member_account_joined_c ON member_account (joined_at) COMPRESS;
PROMPT ===== 6. REVERSE 와 DESC =====
CREATE INDEX ix_member_account_joined_rev ON member_account (joined_at, member_id) REVERSE;
CREATE INDEX ix_member_account_grade_desc ON member_account (grade, joined_at DESC);
PROMPT ===== 7. 사전에서 어떻게 보이는가 =====
SELECT index_name, index_type, uniqueness, status, visibility
  FROM user_indexes
 WHERE table_name = 'MEMBER_ACCOUNT'
 ORDER BY index_name;
SELECT index_name, column_position, column_name, descend
  FROM user_idx_columns
 WHERE table_name = 'MEMBER_ACCOUNT'
 ORDER BY index_name, column_position;
SELECT index_name, column_position, column_expression
  FROM user_idx_expressions
 WHERE table_name = 'MEMBER_ACCOUNT';
PROMPT ===== 8. 정리 =====
ROLLBACK;
DROP TABLE member_account;
SELECT COUNT(*) AS obj_left FROM user_objects;
EXIT
