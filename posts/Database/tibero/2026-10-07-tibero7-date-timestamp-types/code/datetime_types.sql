SET LINESIZE 200
SET PAGESIZE 100

PROMPT ==== 0. 버전과 세션 시간대 ====
SELECT product_major, product_minor FROM v$version;
SELECT SESSIONTIMEZONE FROM dual;

PROMPT ==== 1. 표 만들기 - 일곱 가지 날짜형과 간격형 ====
CREATE TABLE dt_sample (
    id        NUMBER PRIMARY KEY,
    c_date    DATE,
    c_ts0     TIMESTAMP(0),
    c_ts      TIMESTAMP,
    c_ts9     TIMESTAMP(9),
    c_tstz    TIMESTAMP WITH TIME ZONE,
    c_tsltz   TIMESTAMP WITH LOCAL TIME ZONE,
    c_ym      INTERVAL YEAR TO MONTH,
    c_ds      INTERVAL DAY TO SECOND
);
DESC dt_sample

PROMPT ==== 2. 같은 리터럴을 각 컬럼에 넣으면 소수 초가 어떻게 남는가 ====
INSERT INTO dt_sample (id, c_date, c_ts0, c_ts, c_ts9)
VALUES (1,
        TIMESTAMP '2026-10-07 09:30:15.123456789',
        TIMESTAMP '2026-10-07 09:30:15.123456789',
        TIMESTAMP '2026-10-07 09:30:15.123456789',
        TIMESTAMP '2026-10-07 09:30:15.123456789');
SELECT TO_CHAR(c_date, 'YYYY-MM-DD HH24:MI:SS') AS c_date, c_ts0, c_ts, c_ts9 FROM dt_sample WHERE id = 1;

PROMPT ==== 3. 소수 초는 버리는가 반올림하는가 - .5 를 넣어 본다 ====
INSERT INTO dt_sample (id, c_date, c_ts0)
VALUES (2, TIMESTAMP '2026-10-07 23:59:59.5', TIMESTAMP '2026-10-07 23:59:59.5');
SELECT TO_CHAR(c_date, 'YYYY-MM-DD HH24:MI:SS') AS c_date, c_ts0 FROM dt_sample WHERE id = 2;

PROMPT ==== 4. WITH TIME ZONE 과 WITH LOCAL TIME ZONE 에 같은 순간을 넣는다 ====
INSERT INTO dt_sample (id, c_tstz, c_tsltz)
VALUES (3,
        TIMESTAMP '2026-10-07 09:00:00 Asia/Seoul',
        TIMESTAMP '2026-10-07 09:00:00 Asia/Seoul');
SELECT c_tstz, c_tsltz, SYS_EXTRACT_UTC(c_tstz) AS tstz_utc FROM dt_sample WHERE id = 3;

PROMPT ==== 5. 세션 시간대를 바꾸고 다시 조회한다 ====
ALTER SESSION SET TIME_ZONE = '+00:00';
SELECT SESSIONTIMEZONE FROM dual;
SELECT c_tstz, c_tsltz FROM dt_sample WHERE id = 3;
ALTER SESSION SET TIME_ZONE = 'Asia/Seoul';

PROMPT ==== 6. 같은 순간을 다른 시간대로 적은 두 값은 같은가 ====
SELECT CASE WHEN TIMESTAMP '2026-10-07 09:00:00 Asia/Seoul'
               = TIMESTAMP '2026-10-07 00:00:00 +00:00'
            THEN 'SAME' ELSE 'DIFFERENT' END AS same_instant
FROM dual;

PROMPT ==== 7. 연산 결과 타입 - DATE + 숫자, DATE - DATE, TIMESTAMP - TIMESTAMP ====
SELECT DATE '2026-10-07' + 1 AS date_plus_1,
       DATE '2026-10-07' + 1/24 AS date_plus_1h,
       DATE '2026-10-08' - DATE '2026-10-07' AS date_minus_date,
       TIMESTAMP '2026-10-08 00:00:00' - TIMESTAMP '2026-10-07 12:00:00' AS ts_minus_ts
FROM dual;

PROMPT ==== 8. TIMESTAMP 에 숫자를 더하면 소수 초가 남는가 ====
SELECT TIMESTAMP '2026-10-07 09:30:15.123456' + 1 AS ts_plus_1,
       TIMESTAMP '2026-10-07 09:30:15.123456' + NUMTODSINTERVAL(1, 'DAY') AS ts_plus_interval
FROM dual;

PROMPT ==== 9. 간격형 리터럴과 정밀도 초과 ====
INSERT INTO dt_sample (id, c_ym, c_ds)
VALUES (4, INTERVAL '1-2' YEAR TO MONTH, INTERVAL '3 04:05:06.789' DAY TO SECOND);
SELECT c_ym, c_ds FROM dt_sample WHERE id = 4;
INSERT INTO dt_sample (id, c_ds) VALUES (5, INTERVAL '123 00:00:00' DAY(3) TO SECOND);

PROMPT ==== 10. 월말에 한 달 더하기 - ADD_MONTHS 와 INTERVAL ====
SELECT ADD_MONTHS(DATE '2026-01-31', 1) AS add_months_jan31 FROM dual;
SELECT DATE '2026-01-31' + INTERVAL '1' MONTH AS interval_jan31 FROM dual;

PROMPT ==== 11. 현재 시각 함수 다섯 가지의 반환 타입 ====
SELECT SYSDATE, SYSTIMESTAMP, CURRENT_TIMESTAMP, LOCALTIMESTAMP, SESSIONTIMEZONE FROM dual;

PROMPT ==== 12. DATE 컬럼 조건에 날짜만 쓰면 ====
INSERT INTO dt_sample (id, c_date) VALUES (6, TO_DATE('2026-10-07 18:00:00', 'YYYY-MM-DD HH24:MI:SS'));
SELECT COUNT(*) AS eq_date_only FROM dt_sample WHERE c_date = DATE '2026-10-07';
SELECT COUNT(*) AS half_open FROM dt_sample
 WHERE c_date >= DATE '2026-10-07' AND c_date < DATE '2026-10-08';

ROLLBACK;
DROP TABLE dt_sample;
SELECT COUNT(*) AS remaining_objects FROM user_objects;
EXIT
