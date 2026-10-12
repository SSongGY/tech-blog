# 예제 코드 — 중복 행 찾아 지우기

메모리 SQLite에 회원 표(`member`)를 만들고, 같은 이메일이 여러 번 들어간 행을
`GROUP BY … HAVING COUNT(*) > 1`로 찾는다. 묶음마다 `MIN(rowid)` 행만 남기고 지운 뒤
`UNIQUE` 인덱스로 재발을 막는다. 이메일이 NULL인 회원 둘과 대소문자만 다른 이메일을
일부러 넣어 두었다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python dedupe_member_email.py
```

## 바꿔볼 값

- 10번 `DELETE`에서 `email IS NOT NULL` 조건을 빼고 돌려 NULL 회원이 몇 명 남는지 본다.
- 5번의 `MIN(rowid)`를 `MAX(rowid)`로 바꾸면 남는 행이 어떻게 달라지는지 본다.
- `member`에 `member_id INTEGER PRIMARY KEY`를 추가하고 22번의 rowid가 VACUUM 뒤에도 그대로인지 본다.
