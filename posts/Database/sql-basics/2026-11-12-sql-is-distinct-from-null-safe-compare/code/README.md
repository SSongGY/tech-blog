# 예제 코드 — NULL끼리도 같다고 비교하기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
출력은 SQLite 3.49.1 에서 돌린 것이다. 파이썬에 들어 있는 SQLite 판은 `python -c "import sqlite3; print(sqlite3.sqlite_version)"` 으로 확인한다.

## 실행

```bash
python null_safe_compare.py
```

## 바꿔 볼 값

- `customer_yesterday` 7번 고객의 전화를 `''` 대신 `'-'` 로 바꾸고 [3]을 다시 본다 — COALESCE 에 넣은 대체값과 실제 데이터가 겹칠 때만 행이 빠진다는 것을 확인할 수 있다
- [5]에서 두 표에 전화번호가 NULL 인 고객을 하나씩 더 넣으면 `IS` 조인의 행 수가 곱으로 늘어나는 것을 본다
