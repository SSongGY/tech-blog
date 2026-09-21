# ORDER BY — 다중 정렬과 NULL이 놓이는 자리

## 실행

```bash
python order_by_nulls.py
```

의존성 없음. 표준 라이브러리 `sqlite3`만 쓴다.

- 확인 환경: Python 3.13.5 / SQLite 3.49.1 (`sqlite3.sqlite_version`)
- `NULLS FIRST` / `NULLS LAST` 구문은 SQLite 3.30.0 이상에서만 동작한다.
  그 이전 버전에서는 3·4·6·7번 예제가 구문 오류로 멈춘다.

## 바꿔 볼 값

- `show()` 호출의 `order_clause` — 키 순서와 방향을 바꿔 가며 결과가 어떻게 갈리는지 본다.
- `build_sample()`의 `bonus` 값 — NULL을 늘리거나 동점 행을 더 넣어 본다.
- `report_tie_order()` 앞뒤로 만드는 인덱스 `idx_bonus_name`의 컬럼 순서와 방향 —
  `(bonus, name DESC)`를 `(bonus, name)`으로 바꾸면 동점 행의 순서가 또 달라진다.
