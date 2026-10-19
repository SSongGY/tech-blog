# ON CONFLICT 다섯 가지 — 실행 예제

제약을 어겼을 때 어디까지 되돌아가는지를 다섯 가지 해결 방식으로 확인한다.
표준 라이브러리만 쓴다. 설치할 것이 없다.

## 실행

```bash
python conflict_resolution.py
```

## 무엇을 찍는가

| 절 | 확인하는 것 |
|---|---|
| 1 | 같은 4행 배치를 여섯 가지 문장으로 넣어 선행 행·앞선 행·뒤따른 행의 생존을 대조 |
| 2 | `REPLACE` 뒤 rowid 와 `note` 컬럼이 어떻게 되는지 |
| 3 | `REPLACE` 가 `NOT NULL` 을 만났을 때 DEFAULT 유무로 갈리는 결과 |
| 4 | 표 정의의 `ON CONFLICT` 와 문장의 `OR` 중 무엇이 적용되는지 |
| 5 | `IGNORE` 가 UNIQUE 외에 `NOT NULL`·`CHECK` 위반도 건너뛰는지 |

## 바꿔 볼 값

- `BATCH` 안에서 충돌 행(`A-100`)의 위치를 첫 줄이나 마지막 줄로 옮겨 본다.
  `OR FAIL` 과 `OR ABORT` 의 차이가 충돌 행 앞에 몇 행이 있느냐로 정해진다.
- `run_batch` 의 `conn.execute("BEGIN")` 을 지워 본다. 문장 하나가 곧 트랜잭션이
  되어 `OR ROLLBACK` 과 `OR ABORT` 의 결과가 같아진다.
- `show_clause_precedence` 의 표 정의에서 `ON CONFLICT IGNORE` 를
  `ON CONFLICT REPLACE` 로 바꿔 본다.
