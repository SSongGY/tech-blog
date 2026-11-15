# 예제 코드 — 값을 구간으로 묶어 세기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
출력은 SQLite 3.49.1 에서 돌린 것이다. 파이썬에 들어 있는 SQLite 판은 `python -c "import sqlite3; print(sqlite3.sqlite_version)"` 으로 확인한다.

## 실행

```bash
python bucket_histogram.py
```

## 바꿔 볼 값

- `BUCKET_WIDTH` 를 `10` 으로 바꾸면 [2]에서 0 구간에 들어가는 음수가 -9 까지 늘어난다
- `reading` 에 `(-10, -10.0)` 을 넣으면 나머지가 0 인 음수는 [2]와 [4-B]가 같은 구간에 넣는 것을 볼 수 있다
