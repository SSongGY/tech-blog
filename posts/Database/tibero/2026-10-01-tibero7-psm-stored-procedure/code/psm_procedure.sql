SET SERVEROUTPUT ON

PROMPT == 0. version and empty schema
SELECT product_major, product_minor FROM v$version;
SELECT COUNT(*) AS obj_count FROM user_objects;

PROMPT == 1. table and rows
CREATE TABLE psm_account (
  account_id NUMBER PRIMARY KEY,
  owner      VARCHAR2(30),
  balance    NUMBER NOT NULL
);
INSERT INTO psm_account VALUES (1, 'kim', 1000);
INSERT INTO psm_account VALUES (2, 'lee', 200);
COMMIT;
SELECT * FROM psm_account ORDER BY account_id;

PROMPT == 2. procedure with IN / OUT / IN OUT / DEFAULT
CREATE OR REPLACE PROCEDURE psm_withdraw (
  p_account_id  IN     NUMBER,
  p_amount      IN     NUMBER,
  p_new_balance OUT    NUMBER,
  p_call_count  IN OUT NUMBER,
  p_memo        IN     VARCHAR2 DEFAULT 'withdraw'
)
IS
  v_balance      psm_account.balance%TYPE;
  e_insufficient EXCEPTION;
BEGIN
  p_call_count := p_call_count + 1;
  SELECT balance INTO v_balance FROM psm_account WHERE account_id = p_account_id;
  IF v_balance < p_amount THEN
    RAISE e_insufficient;
  END IF;
  UPDATE psm_account SET balance = balance - p_amount WHERE account_id = p_account_id;
  p_new_balance := v_balance - p_amount;
  DBMS_OUTPUT.PUT_LINE(p_memo || ' ' || p_amount || ' -> ' || p_new_balance);
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RAISE_APPLICATION_ERROR(-20001, 'no account ' || p_account_id);
  WHEN e_insufficient THEN
    RAISE_APPLICATION_ERROR(-20002, 'insufficient balance ' || v_balance);
END;
/
SELECT object_name, object_type, status FROM user_objects WHERE object_name = 'PSM_WITHDRAW';
SELECT argument_name, position, in_out FROM user_arguments WHERE object_name = 'PSM_WITHDRAW' ORDER BY position;

PROMPT == 3. anonymous block: positional and named notation
DECLARE
  v_new NUMBER;
  v_cnt NUMBER := 0;
BEGIN
  DBMS_OUTPUT.PUT_LINE('before: new=' || NVL(TO_CHAR(v_new), 'NULL') || ' cnt=' || v_cnt);
  psm_withdraw(1, 300, v_new, v_cnt);
  psm_withdraw(p_account_id => 1, p_amount => 100, p_new_balance => v_new,
               p_call_count => v_cnt, p_memo => 'atm');
  DBMS_OUTPUT.PUT_LINE('after: new=' || v_new || ' cnt=' || v_cnt);
END;
/

PROMPT == 4. CALL with bind variables
VAR v_new NUMBER
VAR v_cnt NUMBER
EXEC :v_cnt := 0
CALL psm_withdraw(1, 50, :v_new, :v_cnt);
PRINT v_new v_cnt
EXEC CALL psm_withdraw(1, 50, :v_new, :v_cnt);
PRINT v_new v_cnt
PROMPT == 4-B. EXEC with bare procedure name (not in the manual examples)
EXEC psm_withdraw(1, 50, :v_new, :v_cnt)
PRINT v_new v_cnt

PROMPT == 5. handled exceptions turned into application errors
CALL psm_withdraw(9, 10, :v_new, :v_cnt);
CALL psm_withdraw(2, 999, :v_new, :v_cnt);
PRINT v_cnt

PROMPT == 6. literal passed to OUT parameter
CALL psm_withdraw(1, 10, 0, :v_cnt);

PROMPT == 7. compile error: assignment to IN parameter
CREATE OR REPLACE PROCEDURE psm_bad_in (p_x IN NUMBER)
IS
BEGIN
  p_x := 1;
END;
/
SHOW ERRORS
SELECT object_name, status FROM user_objects WHERE object_name = 'PSM_BAD_IN';
SELECT line, position, text FROM user_errors WHERE name = 'PSM_BAD_IN' ORDER BY sequence;

PROMPT == 8. compile error: DEFAULT on OUT parameter
CREATE OR REPLACE PROCEDURE psm_bad_default (p_x OUT NUMBER DEFAULT 1)
IS
BEGIN
  p_x := 2;
END;
/
SHOW ERRORS

PROMPT == 9. compile error: length on parameter type
CREATE OR REPLACE PROCEDURE psm_bad_length (p_x IN VARCHAR2(10))
IS
BEGIN
  NULL;
END;
/
SHOW ERRORS

PROMPT == 10. unhandled exception
CREATE OR REPLACE PROCEDURE psm_unhandled (p_x IN NUMBER)
IS
  v_y NUMBER;
BEGIN
  v_y := 10 / p_x;
END;
/
EXEC CALL psm_unhandled(0);

PROMPT == 11. cleanup
ROLLBACK;
SELECT * FROM psm_account ORDER BY account_id;
DROP PROCEDURE psm_withdraw;
DROP PROCEDURE IF EXISTS psm_bad_in;
DROP PROCEDURE IF EXISTS psm_bad_default;
DROP PROCEDURE IF EXISTS psm_bad_length;
DROP PROCEDURE psm_unhandled;
DROP TABLE psm_account;
SELECT COUNT(*) AS obj_count FROM user_objects;
EXIT
