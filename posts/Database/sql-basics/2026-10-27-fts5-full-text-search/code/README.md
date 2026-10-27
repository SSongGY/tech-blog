# FTS5 전문검색 예제

LIKE 검색과 FTS5 `MATCH` 검색을 같은 데이터로 대조한다. 추가 설치가 필요 없다 —
파이썬에 들어 있는 SQLite 가 FTS5 를 포함해 빌드되어 있으면 그대로 돈다.

## 실행

```bash
python fts5_search.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `fts5_search.py` | 본 예제. 여섯 절로 나뉘어 있다 |
| `dbshow.py` | 표 정의와 데이터를 출력 맨 앞에 찍는 도우미 |
| `output.txt` | 실제 실행 기록 |

## FTS5 가 빌드에 들어 있는지 먼저 본다

```python
import sqlite3
print([r[0] for r in sqlite3.connect(":memory:").execute("PRAGMA compile_options")
       if "FTS5" in r[0]])
```

`['ENABLE_FTS5']` 가 나오면 된다. 비어 있으면 `CREATE VIRTUAL TABLE ... USING fts5`
에서 `no such module: fts5` 가 난다.

## 바꿔 볼 값

- `NOTES` 의 본문에 조사가 붙은 낱말을 더 넣어 보면 4절의 토큰 목록이 길어진다.
  `'백업'` 으로는 안 잡히고 `'백업*'` 으로만 잡히는 행이 늘어난다
- `show_scale()` 의 `50_000` 을 키우면 LIKE 쪽만 선형으로 늘어난다.
  MATCH 쪽은 맞는 행 수에만 비례하므로 거의 그대로다
- `fts5(...)` 선언에서 `content`/`content_rowid` 를 빼면 외부 콘텐츠 테이블이 아니라
  본문을 FTS5 가 직접 들고 있는 형태가 된다. `doc_fts_content` 표가 하나 더 생긴다
- `tokenize = "unicode61 remove_diacritics 2"` 를 붙여 보면 토큰 경계가 어떻게
  달라지는지 볼 수 있다. 한국어 공백 분할 자체는 바뀌지 않는다
