# 예제 코드 — Tibero 7 PSM 저장 프로시저 기본 문법

**아직 실행하지 않았다.** 글을 쓴 시점(2026-10-01)에 검증용 Tibero 인스턴스에 접속할 수 없었다(`TBR-2131`).
인스턴스가 살아나면 아래로 돌려 `output.txt`를 채우고 글을 `executed`로 올린다.

`psm_procedure.sql`이 확인하는 것:

1. `IN`·`OUT`·`IN OUT`·`DEFAULT`를 모두 쓴 프로시저가 `VALID`로 만들어지는가, `USER_ARGUMENTS.IN_OUT`에 무엇이 찍히는가
2. 익명 블록에서 위치 표기·이름 표기로 부를 때 `OUT`이 NULL로 시작하고 `IN OUT`이 누적되는가
3. `VAR`·`EXEC`·`CALL`·`PRINT`로 바인드 변수에 받을 때. 4-B는 매뉴얼 예제에 없는 `EXEC 프로시저이름(...)` 형태가 되는지 본다
4. 처리한 예외를 `RAISE_APPLICATION_ERROR`로 바꿨을 때 클라이언트가 받는 에러, 실패한 호출에서 `IN OUT` 값
5. `OUT` 자리에 리터럴 (매뉴얼은 TBR-15055)
6. 컴파일 에러 세 가지 — `IN`에 대입(TBR-15055), `OUT`에 기본값(TBR-15023), 타입에 길이(TBR-15067).
   객체가 `INVALID`로 남는지와 `SHOW ERRORS`·`USER_ERRORS` 출력
7. 처리하지 않은 0 나누기 (매뉴얼은 TBR-5070 + TBR-15163)

빈 스키마에 `psm_account` 표와 프로시저만 만들고, 끝에서 전부 지운 뒤 `user_objects`가 0개인지 찍는다.

## 실행

```bash
tbsql -s <사용자>/<암호> @psm_procedure.sql
```

tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 `--` 주석을 달지 않는다. 설명은 `PROMPT` 줄로 둔다.
PSM 블록은 `END;` 다음 줄의 `/`로 실행한다.

## 바꿔 볼 값

- 3번의 `v_cnt NUMBER := 0`에서 `:= 0`을 지운다. `IN OUT`에 NULL이 들어가면 `p_call_count + 1`이 무엇이 되는지 본다.
- 2번의 `WHEN NO_DATA_FOUND` 처리부를 지운다. 5번 첫 호출의 에러가 `-20001`에서 무엇으로 바뀌는지 본다.
