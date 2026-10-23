# rowid 와 AUTOINCREMENT 가 다음 번호를 고르는 방식

표 둘(`plain`, `strict_seq`)을 같은 데이터로 채우고 똑같은 조작을 가한 뒤,
다음 번호가 무엇이 되는지와 `sqlite_sequence` 가 어떻게 바뀌는지를 찍는다.

의존성은 없다. 파이썬 표준 라이브러리의 `sqlite3` 만 쓴다.

## 실행

```bash
python autoincrement_rowid.py
```

## 바꿔 볼 값

- `SEED` — 처음 채우는 행 수. 삭제·재삽입 실험의 번호가 따라 움직인다
- 5번 절의 `limit` — 상한을 조금 낮춰 두면(예: `100`) 일반 rowid 표가
  빈 번호를 어떻게 고르는지 여러 번 돌려 볼 수 있다
- `build_database()` 의 `":memory:"` 를 파일 경로로 바꾸면 `sqlite_sequence` 가
  재접속 뒤에도 남아 있는 것을 확인할 수 있다
