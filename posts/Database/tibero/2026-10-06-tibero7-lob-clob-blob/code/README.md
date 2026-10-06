# 예제 코드 — Tibero 7 LOB

**아직 실행하지 않았다.** 글을 쓴 시점에 검증용 인스턴스에 접속할 수 없었다(`TBR-2131`).
인스턴스가 살아나면 이 스크립트를 돌려 출력을 채우고 글을 `executed`로 올린다.

빈 스키마에 표 하나(`lb_doc`)만 만든다. CLOB 컬럼 두 개를 하나는 기본값(`ENABLE STORAGE IN ROW`),
하나는 `DISABLE STORAGE IN ROW`로 두고, 짧은 값(100자)과 긴 값(5000자)을 넣어 LOB 세그먼트가 언제
보이는지 본다. 끝나면 표를 지우고 `user_objects`가 0개인지 찍는다. 다른 객체는 조회하지 않는다.

## 실행

```bash
tbsql -s <사용자>/<암호> @lob_storage.sql
```

tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 `--` 주석을 달면 다음 문장이 깨지므로 설명은 `PROMPT`로 적었다.
파일 끝의 `EXIT`가 없으면 프롬프트에서 대기한다.

## 확인할 것

- 2번 — `CREATE TABLE` 직후 `USER_LOBS`의 컬럼 이름과, `USER_SEGMENTS`에 LOB 세그먼트가 이미 보이는지.
  매뉴얼에는 세그먼트가 만들어지는 시점이 적혀 있지 않다.
- 4번 — 값을 넣은 뒤 세그먼트 목록이 바뀌는지. 짧은 값만 든 `body_in`의 세그먼트 크기와
  `DISABLE STORAGE IN ROW`인 `body_out`의 세그먼트 크기를 비교한다.
- 6번 — `DBMS_LOB.SUBSTR`의 인자 순서(크기, 위치)를 `SUBSTR`(위치, 길이)처럼 바꿔 쓰면 무엇이 나오는지.
- 7번 — `EMPTY_CLOB()`으로 넣은 값이 `IS NULL`에 걸리는지, 길이가 0인지.
- 8번 — LOB 컬럼에 `=`·`ORDER BY`·`GROUP BY`·`CREATE INDEX`를 쓰면 각각 어떤 에러 코드가 나는지.
- 10번 — `FOR UPDATE` 없이 가져온 로케이터에 `WRITEAPPEND`를 하면 어떻게 되는지.
  매뉴얼은 "프러시저나 함수는 자동으로 잠금을 설정해 주지 않는다"고만 적는다.
- 11번 — amount 65533이 `TBR-14052`를 내는지.
