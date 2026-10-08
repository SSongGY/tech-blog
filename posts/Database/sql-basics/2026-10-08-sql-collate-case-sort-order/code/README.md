# 예제 코드 — COLLATE

메모리 SQLite에 회원 이름 12행을 넣고 정렬 규칙(BINARY·NOCASE·RTRIM)에 따라 정렬 순서와 `=` 비교 결과가
어떻게 갈리는지, 컬럼 규칙과 `COLLATE` 연산자 중 무엇이 이기는지, 인덱스·UNIQUE·GROUP BY가 규칙을 따르는지,
파이썬으로 등록한 규칙이 다른 연결에서는 어떻게 되는지를 차례로 찍는다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python collate_basics.py
```

## 바꿔볼 값

- 12번과 13번은 `ON` 절 양쪽을 바꾼 것뿐이다. 한쪽에 `COLLATE NOCASE`를 붙이면 순서와 상관없이 그 규칙이 쓰인다.
- 19번 앞의 `CREATE INDEX ix_member_name_nc`를 지우면 18번과 같은 계획으로 돌아간다.
- `natural_key`에서 `part.lower()`를 `part`로 바꾸면 대소문자를 가리는 자연 정렬이 된다.
