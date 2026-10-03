# 예제 코드 — NOT NULL과 DEFAULT — 값이 없을 때

메모리 SQLite에 회원 표를 만들고, 컬럼을 빼먹었을 때·NULL을 직접 넣었을 때·빈 문자열을
넣었을 때 각각 무엇이 저장되는지 찍는다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python not_null_default.py
```

## 바꿔볼 값

- 1번의 `nickname` 에 `None` 대신 `""` 를 넘기면 에러 없이 빈 닉네임이 저장된다.
- `member_strict` 의 CHECK 를 `email <> ''` 로 바꾸면 공백 세 칸(`'   '`)짜리 줄이 통과한다.
- 5번의 `DEFAULT 'basic'` 을 `DEFAULT NULL` 로 바꾸면 `NOT NULL` 과 함께 쓸 수 없다는 에러가 난다.
