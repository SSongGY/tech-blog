SET LINESIZE 200
SET PAGESIZE 100

PROMPT == 0. start: object count in this schema ==
SELECT COUNT(*) AS obj_before FROM user_objects;

PROMPT == 1. sample objects ==
CREATE TABLE dv_member (
    member_id   NUMBER        CONSTRAINT dv_member_pk PRIMARY KEY,
    email       VARCHAR2(100) NOT NULL,
    joined_on   DATE
);
CREATE INDEX ix_dv_member_email ON dv_member (email);
COMMENT ON TABLE dv_member IS 'dictionary view sample';
COMMENT ON COLUMN dv_member.email IS 'login id';

PROMPT == 2. DICTIONARY: which views exist ==
DESC dictionary
SELECT * FROM dictionary WHERE ROWNUM <= 5;

PROMPT == 3. objects ==
SELECT object_name, object_type, status FROM user_objects ORDER BY object_name;

PROMPT == 4. columns (manual name USER_TBL_COLUMNS) ==
SELECT column_name, data_type, nullable FROM user_tbl_columns WHERE table_name = 'DV_MEMBER';

PROMPT == 5. indexes and index columns ==
SELECT index_name, uniqueness FROM user_indexes WHERE table_name = 'DV_MEMBER';
SELECT index_name, column_name FROM user_idx_columns WHERE table_name = 'DV_MEMBER';

PROMPT == 6. constraints ==
SELECT constraint_name, constraint_type FROM user_constraints WHERE table_name = 'DV_MEMBER';
SELECT constraint_name, column_name FROM user_cons_columns WHERE table_name = 'DV_MEMBER';

PROMPT == 7. comments ==
SELECT comments FROM user_tab_comments WHERE table_name = 'DV_MEMBER';
SELECT column_name, comments FROM user_col_comments WHERE table_name = 'DV_MEMBER' AND comments IS NOT NULL;

PROMPT == 8. lower-case name finds nothing ==
SELECT COUNT(*) AS lower_hits FROM user_tables WHERE table_name = 'dv_member';
SELECT COUNT(*) AS upper_hits FROM user_tables WHERE table_name = 'DV_MEMBER';

PROMPT == 9. Oracle-style names: accepted or not ==
SELECT COUNT(*) AS tab_columns FROM user_tab_columns WHERE table_name = 'DV_MEMBER';
SELECT COUNT(*) AS ind_columns FROM user_ind_columns WHERE table_name = 'DV_MEMBER';

PROMPT == 10. USER_ vs ALL_ vs DBA_ ==
SELECT COUNT(*) AS user_cnt FROM user_tables;
SELECT COUNT(*) AS all_cnt FROM all_tables;
SELECT COUNT(*) AS dba_cnt FROM dba_tables;

PROMPT == 11. dynamic view ==
SELECT COUNT(*) AS session_cnt FROM v$session;

PROMPT == 12. cleanup ==
DROP TABLE dv_member;
SELECT COUNT(*) AS obj_left FROM user_objects;

EXIT
