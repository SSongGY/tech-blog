-- Tibero 7 시퀀스 예제 모음
--
-- 이 파일은 실행 검증을 거치지 않았다. 문법은 Tibero 7.2.6 SQL 참조 안내서의
-- CREATE SEQUENCE / ALTER SEQUENCE / DROP SEQUENCE 항목을 근거로 작성했다.
-- tbsql로 접속해 직접 돌려 확인할 것.
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
CREATE SEQUENCE slot_seq
    START WITH 1
    MINVALUE 1
    MAXVALUE 12
    INCREMENT BY 1
    CYCLE
    CACHE 4;

-- 5. 값 발급. CURRVAL을 쓰기 전에 NEXTVAL을 최소 한 번 호출해야 한다.
SELECT order_seq.NEXTVAL FROM dual;
SELECT order_seq.CURRVAL FROM dual;

-- 6. INSERT에서 쓰는 형태. VALUES 절과 INSERT ... SELECT 모두 사용 가능하다.
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
ALTER SEQUENCE invoice_seq INCREMENT BY 10;
ALTER SEQUENCE invoice_seq NOCACHE;

-- 9. 시작값으로 되돌리기
ALTER SEQUENCE invoice_seq RESTART;
ALTER SEQUENCE invoice_seq RESTART START WITH 5000;

-- 10. 정의 확인. 캐시 개수와 마지막 발급 값을 여기서 본다.
SELECT * FROM user_sequences;

-- 11. 정리
DROP TABLE order_item;
DROP SEQUENCE order_seq;
DROP SEQUENCE invoice_seq;
DROP SEQUENCE countdown_seq;
DROP SEQUENCE slot_seq;
