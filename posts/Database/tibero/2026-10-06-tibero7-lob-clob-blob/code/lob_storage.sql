SET LINESIZE 200
SET PAGESIZE 100
SET SERVEROUTPUT ON

PROMPT == 0. start: object count in this schema ==
SELECT COUNT(*) AS obj_before FROM user_objects;

PROMPT == 1. table: in-row CLOB (default), out-of-row CLOB, BLOB ==
CREATE TABLE lb_doc (
    doc_id    NUMBER PRIMARY KEY,
    body_in   CLOB,
    body_out  CLOB,
    image     BLOB
)
LOB (body_out) STORE AS lb_doc_body_out (DISABLE STORAGE IN ROW);

PROMPT == 2. dictionary right after CREATE: which LOB segments exist ==
DESC user_lobs
SELECT * FROM user_lobs WHERE table_name = 'LB_DOC';
SELECT segment_name, segment_type FROM user_segments ORDER BY segment_name;

PROMPT == 3. insert small (100 chars) and large (5000 chars) values ==
INSERT INTO lb_doc VALUES (1, RPAD('a', 100, 'a'), RPAD('a', 100, 'a'), HEXTORAW('CAFE'));
INSERT INTO lb_doc VALUES (2, TO_CLOB(RPAD('b', 4000, 'b')) || RPAD('c', 1000, 'c'), TO_CLOB(RPAD('b', 4000, 'b')) || RPAD('c', 1000, 'c'), NULL);
COMMIT;

PROMPT == 4. segments after insert ==
SELECT segment_name, segment_type, bytes FROM user_segments ORDER BY segment_name;

PROMPT == 5. length: LENGTH vs DBMS_LOB.GETLENGTH, BLOB in bytes ==
SELECT doc_id, LENGTH(body_in) AS len_sql, DBMS_LOB.GETLENGTH(body_in) AS len_lob, DBMS_LOB.GETLENGTH(image) AS img_bytes FROM lb_doc ORDER BY doc_id;

PROMPT == 6. argument order: SUBSTR(str, pos, len) vs DBMS_LOB.SUBSTR(lob, amount, offset) ==
SELECT SUBSTR(body_in, 4001, 3) AS sql_substr, DBMS_LOB.SUBSTR(body_in, 3, 4001) AS lob_substr, DBMS_LOB.SUBSTR(body_in, 4001, 3) AS swapped FROM lb_doc WHERE doc_id = 2;

PROMPT == 7. EMPTY_CLOB vs NULL ==
INSERT INTO lb_doc (doc_id, body_in, body_out) VALUES (3, EMPTY_CLOB(), NULL);
SELECT doc_id, CASE WHEN body_in IS NULL THEN 'NULL' ELSE 'NOT NULL' END AS body_in_state, DBMS_LOB.GETLENGTH(body_in) AS len_in, CASE WHEN body_out IS NULL THEN 'NULL' ELSE 'NOT NULL' END AS body_out_state FROM lb_doc WHERE doc_id = 3;
ROLLBACK;

PROMPT == 8. what LOB columns refuse: equality, ORDER BY, GROUP BY, index ==
SELECT doc_id FROM lb_doc WHERE body_in = RPAD('a', 100, 'a');
SELECT doc_id FROM lb_doc ORDER BY body_in;
SELECT body_in, COUNT(*) FROM lb_doc GROUP BY body_in;
CREATE INDEX ix_lb_doc_body ON lb_doc (body_in);
SELECT doc_id FROM lb_doc WHERE DBMS_LOB.COMPARE(body_in, TO_CLOB(RPAD('a', 100, 'a'))) = 0;

PROMPT == 9. WRITEAPPEND after SELECT ... FOR UPDATE ==
DECLARE
    v_body CLOB;
BEGIN
    SELECT body_in INTO v_body FROM lb_doc WHERE doc_id = 1 FOR UPDATE;
    DBMS_LOB.WRITEAPPEND(v_body, 3, 'xyz');
    DBMS_OUTPUT.PUT_LINE('len after append = ' || DBMS_LOB.GETLENGTH(v_body));
END;
/
SELECT doc_id, DBMS_LOB.GETLENGTH(body_in) AS len_in FROM lb_doc WHERE doc_id = 1;
ROLLBACK;

PROMPT == 10. WRITEAPPEND without FOR UPDATE ==
DECLARE
    v_body CLOB;
BEGIN
    SELECT body_in INTO v_body FROM lb_doc WHERE doc_id = 1;
    DBMS_LOB.WRITEAPPEND(v_body, 3, 'xyz');
    DBMS_OUTPUT.PUT_LINE('len after append = ' || DBMS_LOB.GETLENGTH(v_body));
END;
/
ROLLBACK;

PROMPT == 11. amount out of range (65533) ==
DECLARE
    v_text VARCHAR2(100);
BEGIN
    v_text := DBMS_LOB.SUBSTR(TO_CLOB('abc'), 65533, 1);
    DBMS_OUTPUT.PUT_LINE('result = ' || v_text);
END;
/

PROMPT == 12. cleanup ==
DROP TABLE lb_doc PURGE;
SELECT COUNT(*) AS obj_after FROM user_objects;

EXIT
