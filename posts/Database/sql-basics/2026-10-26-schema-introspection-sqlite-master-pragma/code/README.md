# 스키마 조회 예제

표·인덱스·뷰·트리거가 섞인 스키마를 메모리 DB에 만들고, 그 정의를
`sqlite_master` 와 `PRAGMA` 두 경로로 꺼내 대조한다. 외부 의존성은 없다.

## 실행

```bash
python schema_introspection.py
```

## 바꿔볼 값

- `SCHEMA` 의 `title_fold` 를 `VIRTUAL` 대신 `STORED` 로 바꾸면
  `PRAGMA table_xinfo` 의 `hidden` 값이 2에서 3으로 바뀐다.
- `ix_book_cheap` 의 `WHERE price < 20000` 을 지우면
  `PRAGMA index_list` 의 `partial` 이 1에서 0이 된다.
- `author.name` 의 `UNIQUE` 를 지우면 `sqlite_autoindex_author_1` 이
  `sqlite_master` 에서 사라진다.
