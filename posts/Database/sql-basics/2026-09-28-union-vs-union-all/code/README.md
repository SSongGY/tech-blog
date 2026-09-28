# 예제 코드 — UNION과 UNION ALL

메모리 SQLite에 온라인 회원 5명, 매장 회원 4명을 넣고 두 표를 `UNION`과 `UNION ALL`로 합친다.
행 수, 합칠 때의 규칙(컬럼 이름·컬럼 수·`ORDER BY`), 실행계획을 찍은 뒤 표마다 20만 행으로 늘려
시간을 잰다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python union_vs_union_all.py
```

## 바꿔볼 값

- `STORE_MEMBERS`의 `"김도윤 "`에서 뒤 공백을 지우면 1-C의 `UNION` 결과가 한 행 줄어든다.
- `TIMING_OVERLAP`을 `0.0`으로 바꾸면 겹치는 이메일이 없어져 `UNION`이 지울 행이 없다.
  그래도 중복을 찾는 일은 똑같이 하므로 시간 차이는 남는다.
- `TIMING_ROWS`를 늘리면 두 방식의 시간 차이가 어떻게 벌어지는지 볼 수 있다.
