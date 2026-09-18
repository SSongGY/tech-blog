-- Tibero 7 시퀀스 예제 모음
--
-- 이 파일은 Tibero 7.2 인스턴스에서 실제로 실행해 확인했다. 주석의 에러 번호도
-- 직접 재현해 대조했다. 문법 근거는 Tibero 7.2.6판 SQL 참조 안내서의
-- CREATE SEQUENCE / ALTER SEQUENCE / DROP SEQUENCE / CREATE TABLE 항목,
-- 에러 번호는 같은 판 에러 참조 안내서(6000.dd / 7000.ddl)다.
-- (인스턴스 버전 7.2와 매뉴얼 판 번호 7.2.6은 다른 값이다.)
--
-- 실행: tbsql <사용자>/<비밀번호> @sequence_examples.sql

-- 1. 기본형. 생략한 속성은 매뉴얼의 기본값을 따른다.
--    INCREMENT BY 1, NOCYCLE, NOORDER, MINVALUE 1, MAXVALUE INT64_MAX
CREATE SEQUENCE order_seq;

-- 2. 속성을 모두 지정한 형태
CREATE SEQUENCE invoice_seq
    START WITH 1000
    INCREMENT BY 1
    MINVALUE 1000
    MAXVALUE 9999999999
    NOCYCLE
    CACHE 100
    NOORDER;

-- 3. 감소하는 시퀀스. INCREMENT BY가 음수면 START WITH 기본값은 MAXVALUE다.
CREATE SEQUENCE countdown_seq
    INCREMENT BY -1
    MAXVALUE 1000
    MINVALUE 1
    NOCYCLE;

-- 4. 순환 시퀀스. MAXVALUE에 닿으면 MINVALUE로 돌아간다.
--    오름차순에서 CYCLE은 MAXVALUE와 함께 지정해야 한다(에러 7136).
--    내림차순이면 MINVALUE와 함께다(7135).
--    캐시 크기는 한 사이클보다 작아야 한다(7340). 아래는 사이클 12개에 캐시 4개다.
CREATE SEQUENCE slot_seq
    START WITH 1
    MINVALUE 1
    MAXVALUE 12
    INCREMENT BY 1
    CYCLE
    CACHE 4;

-- 5. 값 발급. CURRVAL을 쓰기 전에 NEXTVAL을 최소 한 번 호출해야 한다.
--    순서를 바꾸면 에러 6003(ERROR_DD_SEQ_NO_CURRVAL)이 난다.
SELECT order_seq.NEXTVAL FROM dual;
SELECT order_seq.CURRVAL FROM dual;

-- 6. INSERT에서 쓰는 형태. VALUES 절과 INSERT ... SELECT 모두 사용 가능하다.
--    created_at의 기본값에는 SYSDATE를 썼다. 컬럼 DEFAULT에 NEXTVAL을 쓸 수 있는지는
--    매뉴얼 두 페이지가 반대로 적고 있어(스키마 객체 = 불가 / CREATE TABLE = 가능)
--    이 스크립트에서는 쓰지 않는다. 자기 버전에서 직접 확인할 항목이다.
CREATE TABLE order_item (
    order_id   NUMBER PRIMARY KEY,
    product_id NUMBER NOT NULL,
    created_at DATE DEFAULT SYSDATE
);

INSERT INTO order_item (order_id, product_id) VALUES (order_seq.NEXTVAL, 10);

-- 7. 한 행에서 NEXTVAL이 여러 번 나와도 값은 한 번만 증가한다.
--    아래 두 컬럼에는 같은 값이 들어간다.
INSERT INTO order_item (order_id, product_id)
     VALUES (order_seq.NEXTVAL, order_seq.NEXTVAL);

-- 8. 정의 변경. 앞으로 발급될 번호에만 적용되고, 캐시에 있던 값은 무효화된다.
--    ALTER에서 START WITH는 쓸 수 없다(7008). CREATE에서 RESTART는 쓸 수 없다(7615).
ALTER SEQUENCE invoice_seq INCREMENT BY 10;
ALTER SEQUENCE invoice_seq NOCACHE;

-- 9. 시작값으로 되돌리기
ALTER SEQUENCE invoice_seq RESTART;
ALTER SEQUENCE invoice_seq RESTART START WITH 5000;

-- 10. 정의 확인. 캐시 개수와 마지막 발급 값을 여기서 본다.
SELECT * FROM user_sequences;

-- 11. identity 컬럼 (Tibero 7 FS02부터 지원)
--     구성요소는 ALWAYS / BY DEFAULT / ON NULL / sequence_attributes 네 가지다.
--     문법 도식이 매뉴얼에서 이미지로만 제공되어 여기에 DDL을 적지 않는다.
--     추정한 문법을 싣지 않기 위한 것이다. CREATE TABLE 문법 도식을 직접 확인할 것.

-- 12. 정리
DROP TABLE order_item;
DROP SEQUENCE order_seq;
DROP SEQUENCE invoice_seq;
DROP SEQUENCE countdown_seq;
DROP SEQUENCE slot_seq;
