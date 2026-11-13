# 예제 코드 — 한 질의로 쪽 데이터와 전체 건수 받기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
출력은 SQLite 3.49.1 에서 돌린 것이다. 파이썬에 들어 있는 SQLite 판은 `python -c "import sqlite3; print(sqlite3.sqlite_version)"` 으로 확인한다.

## 실행

```bash
python count_over_paging.py
```

## 바꿔 볼 값

- `build_large_database(200_000)` 의 행 수를 2만·200만으로 바꿔 [5]를 다시 본다 — 쪽 질의만의 일량은 그대로이고 한 질의 방식은 행 수에 비례해 는다
- [5]의 `OFFSET` 을 0 대신 3,000 으로 바꿔 쪽 질의만의 일량이 얼마나 느는지 본다 — 이때 두 방식의 차이가 줄어든다
- `WHERE category = 'db'` 를 `'ai'` 처럼 다른 값으로 바꿔도 [3]처럼 범위 밖 쪽에서는 `total` 이 사라진다
