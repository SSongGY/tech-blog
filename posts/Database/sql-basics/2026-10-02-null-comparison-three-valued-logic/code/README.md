# 예제 코드 — NULL 비교와 삼값 논리

메모리 SQLite에 회원 5명을 넣는다. 추천인과 등급이 비어 있는(NULL) 회원이 섞여 있다.
진리표를 SQLite가 직접 계산하게 한 뒤 `WHERE`·`CHECK`·`UNIQUE`·`CASE`가 NULL을 어떻게 다루는지 찍는다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python null_comparison.py
```

## 바꿔볼 값

- 2-G의 반복에 `referrer` 값 `3`을 더하면 `=`과 `IS`가 같은 `[5]`를 돌려준다.
- 2-C의 `referrer_id <> 1`에 `OR referrer_id IS NULL`을 덧붙이면 2-E와 같은 세 행이 나온다.
- `CHECK` 조건을 `CHECK (rate IS NOT NULL AND rate BETWEEN 1 AND 50)`로 바꾸면 `(None, None)` 삽입이 거부된다.
- 3번 회원의 등급 `None`을 `"silver"`로 바꾸면 4-A의 두 칸이 모든 행에서 같아진다.
