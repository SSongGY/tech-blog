SET LINESIZE 200
SET PAGESIZE 100

PROMPT ===== 0. 준비: 예제 사용자 4명과 롤 1개 =====
CREATE USER pv_owner IDENTIFIED BY pv_owner_pw;
CREATE USER pv_mid IDENTIFIED BY pv_mid_pw;
CREATE USER pv_end IDENTIFIED BY pv_end_pw;
CREATE USER pv_app IDENTIFIED BY pv_app_pw;
GRANT CONNECT, RESOURCE TO pv_owner;
GRANT CONNECT TO pv_mid, pv_end, pv_app;
CREATE TABLE pv_owner.orders (id NUMBER PRIMARY KEY, amount NUMBER, memo VARCHAR(100));

PROMPT ===== 1. 시스템 권한 WITH ADMIN OPTION: 중간 사용자를 회수해도 다음 사용자는 남는다 =====
GRANT CREATE VIEW TO pv_mid WITH ADMIN OPTION;
CONN pv_mid/pv_mid_pw
GRANT CREATE VIEW TO pv_end;
CONN tibero/tmax
REVOKE CREATE VIEW FROM pv_mid;
SELECT grantee, privilege, admin_option FROM dba_sys_privs
 WHERE grantee IN ('PV_MID', 'PV_END') AND privilege = 'CREATE VIEW';

PROMPT ===== 2. 객체 권한 WITH GRANT OPTION: 중간 사용자를 회수하면 다음 사용자도 잃는다 =====
CONN pv_owner/pv_owner_pw
GRANT SELECT ON orders TO pv_mid WITH GRANT OPTION;
CONN pv_mid/pv_mid_pw
GRANT SELECT ON pv_owner.orders TO pv_end;
CONN pv_owner/pv_owner_pw
SELECT grantee, grantor, privilege, grantable FROM user_tbl_privs WHERE table_name = 'ORDERS';
REVOKE SELECT ON orders FROM pv_mid;
SELECT grantee, grantor, privilege, grantable FROM user_tbl_privs WHERE table_name = 'ORDERS';

PROMPT ===== 3. 롤에는 WITH GRANT OPTION 을 줄 수 없다 =====
CONN tibero/tmax
CREATE ROLE pv_reader;
CONN pv_owner/pv_owner_pw
GRANT SELECT ON orders TO pv_reader WITH GRANT OPTION;
GRANT SELECT, UPDATE (amount) ON orders TO pv_reader;

PROMPT ===== 4. 롤을 사용자에게 주고 기본 롤·SET ROLE 로 켜고 끄기 =====
CONN tibero/tmax
GRANT pv_reader TO pv_app;
SELECT grantee, granted_role, admin_option, default_role FROM dba_role_privs
 WHERE grantee = 'PV_APP';
CONN pv_app/pv_app_pw
SELECT role FROM session_roles;
SET ROLE NONE;
SELECT COUNT(*) FROM pv_owner.orders;
SET ROLE pv_reader;
SELECT COUNT(*) FROM pv_owner.orders;

PROMPT ===== 5. REFERENCES 회수와 CASCADE CONSTRAINTS =====
CONN pv_owner/pv_owner_pw
GRANT REFERENCES ON orders TO pv_mid;
CONN pv_mid/pv_mid_pw
CREATE TABLE order_note (order_id NUMBER REFERENCES pv_owner.orders(id), note VARCHAR(100));
CONN pv_owner/pv_owner_pw
REVOKE REFERENCES ON orders FROM pv_mid;
REVOKE REFERENCES ON orders FROM pv_mid CASCADE CONSTRAINTS;

PROMPT ===== 9. 정리: 만든 것을 전부 지운다 =====
CONN tibero/tmax
DROP USER pv_app CASCADE;
DROP USER pv_end CASCADE;
DROP USER pv_mid CASCADE;
DROP USER pv_owner CASCADE;
DROP ROLE pv_reader;
SELECT COUNT(*) FROM dba_users WHERE username LIKE 'PV\_%' ESCAPE '\';
EXIT
