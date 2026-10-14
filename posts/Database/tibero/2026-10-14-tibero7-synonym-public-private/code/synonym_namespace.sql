-- Tibero 7 시노님 — 공용과 전용이 놓인 네임스페이스를 확인한다.
--
-- 빈 스키마에서 돌린다. 끝에서 만든 객체를 전부 지우고 user_objects 가
-- 비었는지 확인한다. 기존 객체는 조회하지 않는다.
--
-- 돌리는 법:  tbsql -s <사용자>/<암호> @synonym_namespace.sql
--
-- 공용 시노님을 만들고 지우려면 CREATE PUBLIC SYNONYM / DROP PUBLIC SYNONYM
-- 권한이 필요하다. 없으면 6~11번은 건너뛰고 전용 시노님 부분만 본다.

SET ECHO ON
SET SERVEROUTPUT ON

-- 1. 대상 객체 두 개를 만든다
CREATE TABLE syn_src_orders (
    order_id   NUMBER PRIMARY KEY,
    order_memo VARCHAR(100)
);

INSERT INTO syn_src_orders VALUES (1, 'from syn_src_orders');
COMMIT;

CREATE TABLE syn_local_orders (
    order_id   NUMBER PRIMARY KEY,
    order_memo VARCHAR(100)
);

INSERT INTO syn_local_orders VALUES (9, 'from syn_local_orders');
COMMIT;

-- 2. 전용 시노님 — 겹치지 않는 이름이면 만들어진다
CREATE SYNONYM syn_alias_orders FOR syn_src_orders;
SELECT * FROM syn_alias_orders;

-- 3. 전용 시노님은 표와 같은 네임스페이스를 쓴다.
--    같은 스키마에 이미 있는 표 이름으로는 만들 수 없어야 한다.
--    → 어떤 에러 코드가 나오는지 확인한다.
CREATE SYNONYM syn_local_orders FOR syn_src_orders;

-- 4. 대상이 없어도 생성 자체는 된다 (매뉴얼 근거). 쓸 때 에러가 난다.
--    → 생성이 성공하는지, 조회에서 어떤 코드가 나오는지 확인한다.
CREATE SYNONYM syn_missing_target FOR syn_no_such_table;
SELECT * FROM syn_missing_target;

-- 5. ALTER SYNONYM 은 없다. OR REPLACE 로 대상을 바꾼다.
CREATE OR REPLACE SYNONYM syn_alias_orders FOR syn_local_orders;
SELECT * FROM syn_alias_orders;

-- 6. 공용 시노님은 독립된 네임스페이스에 있다.
--    같은 스키마에 syn_local_orders 표가 있는데도 만들어지는지 확인한다.
CREATE PUBLIC SYNONYM syn_local_orders FOR syn_src_orders;

-- 7. 이름 해석 순서 확인 — ① 내 스키마 → ② 공용 시노님.
--    표가 이기면 'from syn_local_orders' 가, 공용 시노님이 이기면
--    'from syn_src_orders' 가 나온다.
SELECT order_id, order_memo FROM syn_local_orders;

-- 8. 스키마를 붙이면 표가 확실히 읽힌다 (대조군)
SELECT order_id, order_memo FROM USER.syn_local_orders;

-- 9. 공용 시노님이 사전 뷰에 어떤 OWNER 로 보이는지 확인한다.
--    매뉴얼은 공용 시노님의 OWNER 값을 적어 두지 않았다.
SELECT owner, synonym_name, org_object_owner, org_object_name
  FROM all_synonyms
 WHERE synonym_name IN ('SYN_ALIAS_ORDERS', 'SYN_LOCAL_ORDERS',
                        'SYN_MISSING_TARGET')
 ORDER BY owner, synonym_name;

-- 10. 시노님이 시노님을 가리킬 수 있다 (매뉴얼이 대상에 시노님을 포함한다)
CREATE SYNONYM syn_chain FOR syn_alias_orders;
SELECT * FROM syn_chain;

-- 11. 뒷정리 — 만든 것만 지운다
DROP SYNONYM syn_chain;
DROP SYNONYM syn_missing_target;
DROP SYNONYM syn_alias_orders;
DROP PUBLIC SYNONYM syn_local_orders;
DROP TABLE syn_local_orders;
DROP TABLE syn_src_orders;

-- 12. 남은 것이 없는지 본다
SELECT object_name, object_type FROM user_objects
 WHERE object_name LIKE 'SYN\_%' ESCAPE '\';

SET ECHO OFF
