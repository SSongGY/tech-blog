SET LINESIZE 200
SET PAGESIZE 100
SET FEEDBACK ON

PROMPT == 0. version ==
SELECT product_major, product_minor FROM v$version;

PROMPT == 1. CREATE DIRECTORY - path that does not exist ==
CREATE DIRECTORY blog_missing_dir AS '/tmp/blog_ext_no_such_dir';
DESC all_directories
SELECT * FROM all_directories;

PROMPT == 2. CREATE DIRECTORY - real path ==
CREATE DIRECTORY blog_ext_dir AS '/tmp/blog_ext';

PROMPT == 3. external table - manual example shape ==
CREATE TABLE ext_member (
    member_id NUMBER,
    name      VARCHAR2(30),
    city      VARCHAR2(30) )
ORGANIZATION EXTERNAL
(
    DEFAULT DIRECTORY blog_ext_dir
    ACCESS PARAMETERS
    (
        LOAD DATA INTO TABLE ext_member FIELDS
            TERMINATED BY ','
            ESCAPED BY '\\'
            LINES TERMINATED BY '\n'
            IGNORE 1 LINES (member_id, name, city)
    )
    LOCATION('members.csv')
);
SELECT * FROM ext_member ORDER BY member_id;

PROMPT == 4. same file without IGNORE 1 LINES ==
CREATE TABLE ext_member_hdr (
    member_id NUMBER,
    name      VARCHAR2(30),
    city      VARCHAR2(30) )
ORGANIZATION EXTERNAL
(
    DEFAULT DIRECTORY blog_ext_dir
    ACCESS PARAMETERS
    (
        LOAD DATA INTO TABLE ext_member_hdr FIELDS
            TERMINATED BY ','
            ESCAPED BY '\\'
            LINES TERMINATED BY '\n'
            (member_id, name, city)
    )
    LOCATION('members.csv')
);
SELECT * FROM ext_member_hdr;

PROMPT == 5. read-only - DML ==
INSERT INTO ext_member VALUES (5, 'test', 'test');
UPDATE ext_member SET city = 'x';
DELETE FROM ext_member;

PROMPT == 6. index on external table ==
CREATE INDEX ext_member_ix ON ext_member (member_id);

PROMPT == 7. column attributes other than definition ==
CREATE TABLE ext_member_pk (
    member_id NUMBER PRIMARY KEY,
    name      VARCHAR2(30) )
ORGANIZATION EXTERNAL
(
    DEFAULT DIRECTORY blog_ext_dir
    ACCESS PARAMETERS
    (
        LOAD DATA INTO TABLE ext_member_pk FIELDS
            TERMINATED BY ','
            IGNORE 1 LINES (member_id, name)
    )
    LOCATION('members.csv')
);

PROMPT == 8. missing file / missing directory - error appears at SELECT ==
CREATE TABLE ext_nofile (
    member_id NUMBER )
ORGANIZATION EXTERNAL
(
    DEFAULT DIRECTORY blog_ext_dir
    ACCESS PARAMETERS
    (
        LOAD DATA INTO TABLE ext_nofile FIELDS
            TERMINATED BY ','
            (member_id)
    )
    LOCATION('no_such_file.csv')
);
SELECT * FROM ext_nofile;
CREATE TABLE ext_nodir (
    member_id NUMBER )
ORGANIZATION EXTERNAL
(
    DEFAULT DIRECTORY blog_missing_dir
    ACCESS PARAMETERS
    (
        LOAD DATA INTO TABLE ext_nodir FIELDS
            TERMINATED BY ','
            (member_id)
    )
    LOCATION('members.csv')
);
SELECT * FROM ext_nodir;

PROMPT == 9. dictionary ==
SELECT * FROM user_external_tables;
SELECT * FROM user_external_locations;

PROMPT == 10. the file changes, the table follows ==
PROMPT (README step: append a line to members.csv on the host, then rerun section 3 SELECT)

PROMPT == 11. cleanup ==
DROP TABLE ext_member;
DROP TABLE ext_member_hdr;
DROP TABLE ext_member_pk;
DROP TABLE ext_nofile;
DROP TABLE ext_nodir;
DROP DIRECTORY blog_ext_dir;
DROP DIRECTORY blog_missing_dir;
SELECT COUNT(*) AS obj_count FROM user_objects;
SELECT * FROM all_directories;
EXIT
