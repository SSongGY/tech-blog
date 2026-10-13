# 예제 코드 — Tibero 7 물리화 뷰의 갱신 방식

**아직 실행하지 않았다.** 글을 쓴 환경에 `tbsql`이 없어 Tibero에 붙을 수 없었다.
클라이언트가 있는 환경에서 이 스크립트를 돌려 출력을 채우고 글을 `executed`로 올린다.

빈 스키마에 부서(`mv_dept`)·사원(`mv_emp`) 표를 만들고, 물리화 뷰 로그 없이 `REFRESH FAST`를
요구했을 때부터 시작한다. `REFRESH FORCE`로 바꿔 보고, 로그를 건 뒤 다시 `FAST`를 만들고,
`ON DEMAND`와 `ON COMMIT`이 커밋에 어떻게 반응하는지 비교한다. 마지막에 `ON COMMIT`+`START WITH`,
분석 함수를 쓴 정의 질의, `NEVER REFRESH` 새로고침처럼 매뉴얼이 막는다고 적어 둔 경우를 차례로 친다.
끝에서 만든 객체를 전부 지우고 `user_objects`가 0개인지 확인한다.

## 실행

```bash
tbsql -s <사용자>/<암호> @mview_refresh_modes.sql
```

## 확인할 것

매뉴얼에 적혀 있지 않거나 번호만 있고 실제 문구를 모르는 항목이다. 돌린 뒤 글에 반영한다.

- 2번 — 로그 없이 `REFRESH FAST`를 만들 때 나오는 코드가 `TBR-7315`인지, 아니면 생성 단계에서
  다른 코드가 먼저 걸리는지.
- 3번 — `REFRESH FORCE`로 만든 뷰의 `USER_MVIEWS.FAST_REFRESHABLE`과 `LAST_REFRESH_TYPE` 값.
  매뉴얼이 `FAST_REFRESHABLE`의 가능한 값을 적어 두지 않았다.
- 6번 — `ON DEMAND` 뷰에서 마스터가 바뀐 뒤 `STALENESS`에 무엇이 찍히는지. 매뉴얼은 이 컬럼의
  값 목록을 적어 두지 않았다.
- 9번 — `ON COMMIT`과 `START WITH`를 함께 썼을 때의 에러 코드. 매뉴얼은 금지한다고만 적는다.
- 10번 — 분석 함수를 쓴 정의 질의가 `TBR-7318`로 막히는지.
- 12번 — `BUILD DEFERRED` 직후의 행 수가 0인지, 첫 새로고침의 `LAST_REFRESH_TYPE`이 COMPLETE인지.

## 바꿔볼 값

- 4번의 로그에서 `INCLUDING NEW VALUES`를 빼고 5번을 다시 돌려 `TBR-7319`가 나오는지 본다.
- 4번의 `SEQUENCE (dept_no, salary)`에서 필터 컬럼 목록을 비우고 돌려 `TBR-7320`이 나오는지 본다.
- 5번의 정의 질의에서 `GROUP BY`를 빼고 `WHERE dept_no = 10`으로 바꿔, 집계 없는 뷰에서는
  `INCLUDING NEW VALUES` 없이도 `FAST`가 만들어지는지 본다.
