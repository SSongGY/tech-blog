# 예제 코드 — Tibero 7 실행계획 보기

**아직 실행하지 않았다.** 글을 쓴 시점에 검증용 인스턴스에 접속할 수 없었다(`TBR-2131`).
빈 스키마에서 돌리면 예제 표 `xp_emp`를 만들고, 세 경로로 계획을 뽑은 뒤 전부 지운다.

| 장 | 무엇을 보는가 |
|---|---|
| 2 | `PLAN_TABLE`이 이미 있는지 (없으면 3장부터 실패한다) |
| 3·4 | `EXPLAIN PLAN` + `DISPLAY` 기본 형식과 `ALL` 형식의 차이 |
| 5 | `EXPLAIN PLAN`이 자동 커밋하지 않는지 — `ROLLBACK` 뒤 행 수 |
| 6·7 | `GATHER_SQL_PLAN_STAT`을 켜기 전과 후의 `DISPLAY_CURSOR` Rows 값 |
| 8 | 형식 문자열 가감(`-COST +OUTLINE`)과 틀린 항목 이름의 오류 문구 |
| 9 | `AUTOTRACE TRACEONLY EXPLAIN`과 `PLANSTAT` |

## 실행

```bash
tbsql -s tibero/tmax @explain_plan.sql
```

## 바꿔볼 값

- 6장에서 `'TYPICAL'` 대신 기본값(`'BASIC LAST SQL'`)으로 두고 어떤 열이 빠지는지 본다.
- 9장을 `SET AUTOTRACE ON`으로 바꾸면 결과 행까지 찍힌다.
