SET ECHO ON
SET FEEDBACK ON

PROMPT ===== 0. 예제 표 =====
CREATE TABLE iso_account (
    account_id  NUMBER PRIMARY KEY,
    balance     NUMBER NOT NULL
);
INSERT INTO iso_account VALUES (1, 1000);
INSERT INTO iso_account VALUES (2, 500);
COMMIT;
DESC iso_account
SELECT * FROM iso_account ORDER BY account_id;

PROMPT ===== 1. SET TRANSACTION 은 트랜잭션의 첫 문장이어야 한다 =====
PROMPT 1-A 첫 문장으로 쓰면 성공해야 한다
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT balance FROM iso_account WHERE account_id = 1;
COMMIT;

PROMPT 1-B 다른 문장 뒤에 쓰면 TBR-7191 이 나와야 한다
UPDATE iso_account SET balance = balance WHERE account_id = 1;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
ROLLBACK;

PROMPT 1-C SELECT 뒤에 써도 트랜잭션이 시작된 것으로 치는가
SELECT balance FROM iso_account WHERE account_id = 1;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
ROLLBACK;

PROMPT ===== 2. READ ONLY 에서 데이터를 바꾸면 에러 =====
SET TRANSACTION ISOLATION LEVEL READ ONLY;
SELECT balance FROM iso_account WHERE account_id = 1;
UPDATE iso_account SET balance = 0 WHERE account_id = 1;
ROLLBACK;

PROMPT ===== 3. 매뉴얼 목록에 없는 수준 이름을 넘기면 =====
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
ROLLBACK;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
ROLLBACK;

PROMPT ===== 4. 이름 붙이기 =====
SET TRANSACTION NAME 'iso_demo_tx';
UPDATE iso_account SET balance = balance + 1 WHERE account_id = 2;
ROLLBACK;

PROMPT ===== 5. 세션 단위 설정 =====
ALTER SESSION SET ISOLATION_LEVEL = SERIALIZABLE;
SELECT balance FROM iso_account WHERE account_id = 1;
COMMIT;
ALTER SESSION SET ISOLATION_LEVEL = READ COMMITTED;

PROMPT ===== 6. 정리 =====
DROP TABLE iso_account;
SELECT COUNT(*) AS obj_count FROM user_objects;
EXIT
