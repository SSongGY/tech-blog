# 예제 코드 — N+1 쿼리는 왜 반복해서 생기고 어떻게 잡아내는가

메모리 SQLite에 저자와 글(저자당 3편)을 넣고, 글 목록 화면을 세 방식으로 그린다.

- `render_lazy` — ORM 지연 로딩을 흉내 낸 모델 계층. 글마다 저자를 따로 읽는다
- `render_join` — JOIN 한 번
- `render_in_batch` — 글 목록 한 번 + 저자 `IN (...)` 한 번

`sqlite3.Connection.set_trace_callback`으로 실제 실행된 문장을 모으고, 값만 다른 문장을 지문으로 묶어 반복을 찾는다.
`test_n_plus_one.py`는 그 탐지기를 테스트에 건 예다. 5절에서 함께 돈다. 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python n_plus_one.py
```

테스트만 따로 돌리려면:

```bash
python -m unittest -v test_n_plus_one
```

## 바꿔볼 값

- `assert_no_repeated_query`의 `max_repeat`를 `20`으로 올리고 `test_n_plus_one.py`의 저자 수를 10으로 낮추면 지연 로딩도 통과한다. 허용치를 데이터 크기와 엮으면 탐지기가 무뎌진다.
- `render_lazy`의 `Post`에 같은 `author_id`끼리 결과를 나눠 갖는 캐시를 붙이면 문장 수가 저자 수만큼으로 준다. 그래도 N+1인지 본다.
- 4절의 `(10, 100, 1000)`에 `5000`을 더해 `IN (...)` 자리표시자 수가 늘 때 어떻게 되는지 본다.
