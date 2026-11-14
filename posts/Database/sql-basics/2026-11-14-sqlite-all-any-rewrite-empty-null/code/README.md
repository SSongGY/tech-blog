# 예제 코드 — ALL·ANY 비교를 SQLite에서 쓰는 법

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
출력은 SQLite 3.49.1 에서 돌린 것이다. 파이썬에 들어 있는 SQLite 판은 `python -c "import sqlite3; print(sqlite3.sqlite_version)"` 으로 확인한다.

## 실행

```bash
python all_any_rewrite.py
```

## 바꿔 볼 값

- `rival_offer` 4번 행의 가격 `NULL` 을 `2000` 으로 바꾸고 [3]을 다시 본다 — note 분류에서 세 형태가 모두 3번 상품을 빼는 것을 볼 수 있다
- `rival_offer` 에 `('ink', 6000)` 을 넣으면 ink 분류가 "빈 집합"에서 벗어나 [3-A]와 [3-B]의 결과가 같아진다
