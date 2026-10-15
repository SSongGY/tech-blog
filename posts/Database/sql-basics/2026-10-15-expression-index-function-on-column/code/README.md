# 예제 코드 — 표현식 인덱스 — 함수를 씌운 컬럼도 인덱스를 타게

메모리 SQLite에 회원 240행을 만들고, 같은 질의를 인덱스 없이 / 일반 인덱스로 /
표현식 인덱스로 각각 돌려 실행계획과 함수 호출 횟수를 비교한다.

인덱스에 쓰는 함수(`norm`)를 파이썬 쪽에 직접 등록해 호출 횟수를 세므로,
"실제로 표의 행을 몇 번 건드렸는가"가 숫자로 나온다.

## 실행

```bash
python expression_index.py
```

의존성은 없다. 표준 라이브러리의 `sqlite3`만 쓴다.

## 바꿔볼 값

- `ROW_COUNT` — 행 수. 인덱스 없이 돌 때의 `norm()` 호출 횟수가 이 값을 따라간다
- `target` — 찾는 이메일. `User120@example.com`처럼 대소문자를 바꿔도 결과가
  같은지 확인한다
- 4절의 `CREATE INDEX idx_score_xy ON score(x + y)` 를 `score(y + x)` 로 바꾸면
  어느 질의가 인덱스를 타는지가 뒤집힌다

## 파일

- `expression_index.py` — 본체
- `dbshow.py` — 표 정의와 데이터를 출력 앞머리에 찍는 도우미 (`references/dbshow.py` 사본)
- `output.txt` — `python scripts/blog.py run-example` 이 남긴 실행 기록
