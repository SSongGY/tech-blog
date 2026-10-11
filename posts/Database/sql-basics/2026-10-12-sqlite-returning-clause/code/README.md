# 예제 코드 — RETURNING — 넣은 값을 그 자리에서 돌려받기

파이썬 표준 라이브러리만 쓴다. 메모리 DB라 파일이 남지 않는다.

## 실행

```bash
python returning_basics.py
```

## 바꿔볼 값

- 6번의 금액을 `150000`에서 `90000`으로 낮추면 트리거가 돌지 않아 `order_log`가 비고 상태도 `접수`로 남는다.
- 7번에서 `cur.fetchone()` 대신 아무것도 읽지 않고 `COUNT(*)`를 세어 봐도 세 행이 이미 들어가 있다.
- `build_database()`의 `autocommit=True`를 빼면 파이썬이 트랜잭션을 연 채로 진행한다. 결과 행은 같다.
