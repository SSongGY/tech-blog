# LIMIT과 OFFSET — 결과를 잘라내는 문법

`limit_offset.py` 하나로 문법 다섯 가지와, OFFSET이 커질 때 무엇이 늘어나는지를 한 번에 본다.

## 실행

```bash
python limit_offset.py
```

의존성 없음. 표준 라이브러리 `sqlite3`만 쓴다. 메모리 DB에 20만 행을 넣고 지우므로
파일이 남지 않는다.

- 확인 환경: Python 3.13.5 / SQLite 3.49.1 (`sqlite3.sqlite_version`)
- `LIMIT`의 쉼표 문법(`LIMIT 3, 3`)은 SQLite와 MySQL에만 있다.
  PostgreSQL 16·Oracle 19c에는 없다.

## 무엇을 재는가

시간이 아니라 **SQLite 가상 머신이 실행한 명령 개수**를 센다.
`sqlite3.Connection.set_progress_handler(tick, 1)`로 명령 하나마다 호출되는 콜백을 걸어
세는 방식이다. 시간은 같은 기계에서도 돌릴 때마다 흔들리지만, 명령 개수는 같은
데이터·같은 질의면 몇 번을 돌려도 같은 값이 나온다. 그래서 "OFFSET이 왜 비싼가"를
흔들리지 않는 숫자로 보여 줄 수 있다.

## 바꿔 볼 값

- `ROW_COUNT` — 20만을 100만으로 올리면 6번 표의 명령 개수도 그대로 따라 는다.
  건너뛴 행 수에 비례한다는 것을 다른 규모에서 확인할 수 있다.
- `PAGE_SIZE` — 10을 100으로 바꿔도 6번 표의 증가 폭은 거의 그대로다.
  비싼 쪽은 가져오는 행이 아니라 **버리는 행**이다.
- 7번의 `keyset_sql`에서 `WHERE id > ?`를 떼면 다시 앞에서부터 세므로
  6번과 같은 모양으로 돌아간다.
- 9번에서 만드는 `ix_article_view_count`를 `(id DESC)` 같은 다른 컬럼으로 바꾸면
  `ORDER BY` 없는 `LIMIT 3`이 또 다른 세 행을 돌려준다.
