# PERCENT_RANK·CUME_DIST 예제

메모리 SQLite에 10명짜리 점수 표를 만들고, `PERCENT_RANK()`와 `CUME_DIST()`가
동점·NULL·한 행짜리 파티션에서 어떤 값을 내는지 공식과 맞춰 본다. 외부 의존성은 없다.

## 실행

```bash
python percentile_demo.py
```

## 바꿔 볼 값

- `build_database()`의 88점 세 명 — 동점 수를 늘리면 `PERCENT_RANK`는 동점 묶음 안에서
  그대로이고, 다음 학생의 값만 크게 뛴다. `CUME_DIST`는 동점 전원이 묶음 끝 값을 받는다.
- 3번 질의의 `PARTITION BY class` — C반처럼 한 명뿐인 파티션은 `PERCENT_RANK`가 0,
  `CUME_DIST`가 1이 된다.
- 6번에서 넣는 NULL 점수 — `ORDER BY score`에서 NULL이 맨 앞에 서므로
  다른 학생 전원의 값이 바뀐다. `ORDER BY score NULLS LAST`로 바꿔 보면 뒤로 간다.
