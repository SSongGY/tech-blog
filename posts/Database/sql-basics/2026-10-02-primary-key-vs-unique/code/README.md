# 예제 코드 — 기본 키와 UNIQUE 제약

메모리 SQLite에 회원 3명을 넣는다. 회원 코드(`member_code`)는 기본 키, 이메일(`email`)은 UNIQUE다.
같은 값과 NULL을 넣어 두 제약이 어디서 같고 어디서 갈리는지 보고, 정수가 아닌 기본 키에 NULL이
들어가는 SQLite의 호환 동작을 NOT NULL·STRICT·WITHOUT ROWID 표와 나란히 확인한다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python pk_vs_unique.py
```

## 바꿔볼 값

- `member` 표 정의에서 `member_code TEXT PRIMARY KEY`를 `member_code TEXT NOT NULL PRIMARY KEY`로 바꾸면 3번의 두 INSERT가 실패한다.
- 5번의 `board` 표를 `post_id INTEGER PRIMARY KEY DESC`로 바꾸면 NULL이 번호로 바뀌지 않는다(행 번호의 별칭이 아니게 된다).
- 6번의 `enrollment`에 `('S2', 'DB101')`을 넣으면 성공한다. 두 컬럼을 묶은 값이 처음 나오기 때문이다.
