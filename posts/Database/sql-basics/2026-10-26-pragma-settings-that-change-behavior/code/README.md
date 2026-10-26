# PRAGMA — 동작을 바꾸는 설정들

SQLite 의 `PRAGMA` 가 무엇을 바꾸고 어디까지 남는지를 직접 확인한다.
파이썬 표준 라이브러리 `sqlite3` 만 쓰므로 따로 설치할 것이 없다.

## 실행

```bash
python pragma_settings.py
```

## 무엇을 보여주는가

| 절 | 확인하는 것 |
|---|---|
| 1 | `PRAGMA` 의 묻는 꼴과 바꾸는 꼴 |
| 2 | `foreign_keys` 를 끄면 없는 부모를 가리키는 행이 들어간다 |
| 3 | 연결을 끊었다 붙여 다섯 가지가 남는지 가른다 |
| 4 | `cache_size` 의 부호가 단위를 바꾼다 |
| 5 | 트랜잭션 안에서 `journal_mode`·`foreign_keys` 가 안 먹는다 |
| 6 | 이름을 틀려도 에러가 나지 않는다 |
| 7 | 조회용 `PRAGMA` 와 `pragma_` 접두 함수 |

## 바꿔볼 값

- 3절의 `cache_size = -8000` 을 양수로 바꿔 보면 다시 붙었을 때 돌아가는 값이 기본값
  `-2000` 임을 볼 수 있다.
- 5절에서 `conn.execute("BEGIN")` 을 지우면 `journal_mode = WAL` 이 그대로 먹는다.
- `sqlite3.connect(db_path, isolation_level=None)` 으로 열면 파이썬이 몰래 거는
  트랜잭션이 없어져 5절의 결과가 달라진다.
