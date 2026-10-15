# 인덱스와 NULL — 예제 코드

파이썬 표준 라이브러리의 `sqlite3` 모듈만 쓴다. 따로 설치할 것이 없다.

## 실행

```bash
python main.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `main.py` | 네 가지 확인을 차례로 돌린다 |
| `dbshow.py` | 표 정의와 데이터를 출력 맨 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |

## 바꿔 볼 값

- `build_database()` 의 `None if i % 5 else i // 5` — NULL 비율을 바꾸면
  `IS NULL` 질의가 인덱스를 타는 것이 언제까지 이득인지 보인다.
- `experiment_order()` 의 질의에 `NULLS LAST` 를 붙였다 떼면서 계획이 바뀌는지 본다.
  (`NULLS FIRST`/`NULLS LAST` 는 SQLite 3.30.0 부터다)
