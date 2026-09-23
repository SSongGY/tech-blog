-- 시퀀스 캐시가 세션 단위인가 인스턴스 단위인가
--
-- 이 파일은 한 번에 돌리는 것이 아니라 tbsql 을 세 번 따로 띄워서 돌린다.
-- 세션이 끊길 때 캐시에 남아 있던 값이 유실되는지를 보려면 세션을 실제로
-- 끝내야 하기 때문이다. 아래 세 덩어리를 각각 별도 파일로 잘라 쓴다.
--
-- 실행:
--   tbsql <사용자>/<비밀번호> @s1.sql
--   tbsql <사용자>/<비밀번호> @s2.sql
--   tbsql <사용자>/<비밀번호> @s3.sql
--
-- 캐시가 세션 단위라면 세션 1이 끝나는 순간 2~20이 사라져
-- 세션 2의 NEXTVAL 은 21이 되어야 한다.

-- ================================================================
-- [s1.sql] 세션 1 — 시퀀스를 만들고 한 개만 뽑은 뒤 종료한다.
--          캐시에는 2~20이 남은 채로 세션이 끊긴다.
-- ================================================================
CREATE SEQUENCE xs_seq START WITH 1 INCREMENT BY 1 CACHE 20;
SELECT xs_seq.NEXTVAL AS sess1_val FROM dual;
SELECT cache_size, last_number FROM user_sequences WHERE sequence_name = 'XS_SEQ';
EXIT

-- ================================================================
-- [s2.sql] 세션 2 — 새 세션에서 뽑는다.
--          2가 나오면 캐시가 인스턴스 단위로 살아남은 것이다.
-- ================================================================
SELECT xs_seq.NEXTVAL AS sess2_val FROM dual;
SELECT cache_size, last_number FROM user_sequences WHERE sequence_name = 'XS_SEQ';
EXIT

-- ================================================================
-- [s3.sql] 세션 3 — 캐시를 채운 세션이 아닌 다른 세션에서 ALTER 를 건다.
--          그래도 3이 나오면 ALTER 는 번호를 건너뛰게 하지 않는다.
-- ================================================================
ALTER SEQUENCE xs_seq CACHE 20;
SELECT cache_size, last_number FROM user_sequences WHERE sequence_name = 'XS_SEQ';
SELECT xs_seq.NEXTVAL AS sess3_val FROM dual;
SELECT cache_size, last_number FROM user_sequences WHERE sequence_name = 'XS_SEQ';
DROP SEQUENCE xs_seq;
SELECT COUNT(*) AS seq_left FROM user_sequences;
EXIT
