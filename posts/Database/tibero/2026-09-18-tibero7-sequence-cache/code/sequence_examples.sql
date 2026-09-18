-- Tibero 7 시퀀스 예제 모음
--
-- Tibero 7.2.6(PRODUCT_MAJOR 7, PRODUCT_MINOR 2)에서 전부 실행해 확인했다.
-- 주석의 에러 번호와 기대값은 실제로 받은 것이다.
--
-- 실행: tbsql <사용자>/<비밀번호> @sequence_examples.sql
--
-- tbsql 스크립트 모드의 두 가지 제약 때문에 이 파일의 형식이 이렇다.
--   1) 끝에 EXIT가 없으면 프롬프트에서 대기한다. 무인 실행이 멈춘다.
--   2) 문장 뒤에 같은 줄로 `-- 주석`을 달면 다음 문장이 TBR-8004로 깨진다.
--      그래서 모든 주석을 독립된 줄에 둔다. code/README.md에 재현 예가 있다.

SET LINESIZE 220
SET PAGESIZE 60

-- ================================================================
-- 1. 기본형. 생략한 속성의 실측 기본값을 바로 확인한다.
--    INCREMENT BY 1, NOCYCLE(N), NOORDER(N), MINVALUE 1, CACHE 20,
--    MAXVALUE 9999999999999999999999999999 (9가 28개. INT64_MAX가 아니다)
-- ================================================================
CREATE SEQUENCE order_seq;

COL sequence_name FORMAT A14
COL max_value FORMAT 99999999999999999999999999999
SELECT sequence_name, min_value, max_value, increment_by,
       cycle_flag, order_flag, cache_size, last_number
  FROM user_sequences WHERE sequence_name = 'ORDER_SEQ';

-- ================================================================
-- 2. CURRVAL은 같은 세션에서 NEXTVAL을 먼저 불러야 한다.
--    아래 첫 문장은 TBR-6003, 이어지는 두 문장은 각각 1을 반환한다.
-- ================================================================
SELECT order_seq.CURRVAL FROM dual;
SELECT order_seq.NEXTVAL FROM dual;
SELECT order_seq.CURRVAL FROM dual;

-- ================================================================
-- 3. 내림차순. START WITH를 생략하면 MAXVALUE에서 시작해 1000이 나온다.
-- ================================================================
CREATE SEQUENCE countdown_seq INCREMENT BY -1 MAXVALUE 1000 MINVALUE 1 NOCYCLE;
SELECT countdown_seq.NEXTVAL FROM dual;

-- ================================================================
-- 4. 구성요소 표에 없는 제약들. 전부 생성 단계에서 막힌다.
-- ================================================================

-- 오름차순 CYCLE에는 MAXVALUE가 필요하다 → TBR-7136
CREATE SEQUENCE bad_cycle_seq START WITH 1 MINVALUE 1 INCREMENT BY 1 CYCLE;

-- 캐시 크기는 한 사이클보다 작아야 한다 → TBR-7340 (사이클 12개에 캐시 20개)
CREATE SEQUENCE bad_cache_seq START WITH 1 MINVALUE 1 MAXVALUE 12
    INCREMENT BY 1 CYCLE CACHE 20;

-- INCREMENT는 MAXVALUE - MINVALUE보다 작아야 한다 → TBR-7424
CREATE SEQUENCE big_step_seq MINVALUE 1 MAXVALUE 10 INCREMENT BY 100;

-- RESTART는 CREATE에서 쓸 수 없다 → TBR-7615
CREATE SEQUENCE bad_restart_seq RESTART START WITH 5;

-- 사이클보다 작은 캐시는 통과한다
CREATE SEQUENCE slot_seq START WITH 1 MINVALUE 1 MAXVALUE 12
    INCREMENT BY 1 CYCLE CACHE 4;

-- ================================================================
-- 5. 한계에 닿았을 때.
--    NOCYCLE은 1, 2를 내고 세 번째에 TBR-6004로 멈춘다.
-- ================================================================
CREATE SEQUENCE tiny_seq START WITH 1 MINVALUE 1 MAXVALUE 2
    INCREMENT BY 1 NOCYCLE NOCACHE;
SELECT tiny_seq.NEXTVAL FROM dual;
SELECT tiny_seq.NEXTVAL FROM dual;
SELECT tiny_seq.NEXTVAL FROM dual;

-- CYCLE은 1, 2, 3을 낸 뒤 MINVALUE로 돌아가 다시 1을 낸다.
CREATE SEQUENCE ring_seq START WITH 1 MINVALUE 1 MAXVALUE 3
    INCREMENT BY 1 CYCLE NOCACHE;
SELECT ring_seq.NEXTVAL FROM dual;
SELECT ring_seq.NEXTVAL FROM dual;
SELECT ring_seq.NEXTVAL FROM dual;
SELECT ring_seq.NEXTVAL FROM dual;

-- ================================================================
-- 6. 컬럼 DEFAULT에 NEXTVAL. 매뉴얼 두 페이지가 반대로 적는 항목인데
--    7.2.6에서는 동작한다. 다만 운영 코드라면 identity 컬럼 쪽이 안전하다.
-- ================================================================
CREATE TABLE order_item (
    order_id   NUMBER DEFAULT order_seq.NEXTVAL PRIMARY KEY,
    product_id NUMBER NOT NULL,
    created_at DATE DEFAULT SYSDATE
);
INSERT INTO order_item (product_id) VALUES (10);
SELECT order_id, product_id FROM order_item;

-- ================================================================
-- 7. 한 행에서 NEXTVAL이 여러 번 나와도 증가는 한 번이다.
--    아래 SELECT의 두 컬럼에는 같은 값이 들어 있다.
-- ================================================================
DROP TABLE order_item;
CREATE TABLE order_item (
    order_id   NUMBER PRIMARY KEY,
    product_id NUMBER NOT NULL
);
INSERT INTO order_item (order_id, product_id)
     VALUES (order_seq.NEXTVAL, order_seq.NEXTVAL);
SELECT order_id, product_id FROM order_item;

-- ================================================================
-- 8. ALTER.
--    START WITH는 못 바꾼다 → TBR-7008
--    RESTART는 START WITH로 준 1000이 아니라 MINVALUE 기본값 1로 돌아간다.
--    특정 값이 필요하면 RESTART START WITH로 직접 준다.
-- ================================================================
CREATE SEQUENCE invoice_seq START WITH 1000 INCREMENT BY 1 CACHE 100;
SELECT invoice_seq.NEXTVAL FROM dual;

ALTER SEQUENCE invoice_seq START WITH 2000;

ALTER SEQUENCE invoice_seq INCREMENT BY 10;
ALTER SEQUENCE invoice_seq NOCACHE;

ALTER SEQUENCE invoice_seq RESTART;
SELECT invoice_seq.NEXTVAL FROM dual;

ALTER SEQUENCE invoice_seq RESTART START WITH 5000;
SELECT invoice_seq.NEXTVAL FROM dual;

-- ================================================================
-- 9. identity 컬럼 (Tibero 7 FS02부터).
--    문법 도식이 매뉴얼에서 이미지로만 제공되어 실기에서 확인한 형태다.
--    emp_id에 1, 2가 자동으로 들어간다.
-- ================================================================
CREATE TABLE emp_identity (
    emp_id NUMBER GENERATED ALWAYS AS IDENTITY,
    name   VARCHAR(20)
);
INSERT INTO emp_identity (name) VALUES ('kim');
INSERT INTO emp_identity (name) VALUES ('lee');
SELECT emp_id, name FROM emp_identity;

-- ALWAYS 컬럼에 값을 직접 넣으면 막힌다 → TBR-8162
INSERT INTO emp_identity (emp_id, name) VALUES (99, 'park');

-- ================================================================
-- 10. 정의 확인.
--     LAST_NUMBER는 마지막 발급 번호가 아니라 캐시로 미리 확보한 다음 값이다.
--     NEXTVAL을 세 번 부른 ORDER_SEQ가 CACHE 20이라 21로 찍힌다.
--     identity가 만든 ISEQ$$_<객체번호> 시퀀스도 같이 보인다.
-- ================================================================
COL sequence_name FORMAT A24
SELECT sequence_name, cache_size, last_number
  FROM user_sequences ORDER BY sequence_name;

-- ================================================================
-- 11. 정리. 예제 객체만 지운다. 마지막 두 카운트는 0이어야 한다.
-- ================================================================
DROP TABLE order_item;
DROP TABLE emp_identity;
DROP SEQUENCE order_seq;
DROP SEQUENCE invoice_seq;
DROP SEQUENCE countdown_seq;
DROP SEQUENCE slot_seq;
DROP SEQUENCE tiny_seq;
DROP SEQUENCE ring_seq;

SELECT COUNT(*) AS seq_left FROM user_sequences;
SELECT COUNT(*) AS tab_left FROM user_tables;

EXIT
