# 예제 코드 — 의존성 방향 확인

같은 주문 기능을 두 가지로 짰다.

- `before/order_service.py` — 계층형. 업무 규칙이 `sqlite3`를 직접 import 한다
- `after/` — 포트와 어댑터. `domain.py`(업무 규칙·포트) ← `adapters.py`(구현) ← `main.py`(조립)

`check_dependencies.py`가 두 설계의 import 문을 `ast`로 뽑아 의존 방향을 찍고,
실행 중 호출 방향을 기록하고, 유스케이스를 고치지 않은 채 어댑터만 바꿔 실행한다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python check_dependencies.py
```

## 바꿔볼 값

- `after/domain.py` 맨 위에 `import sqlite3`를 넣으면 1-B에 "바깥으로 (규칙 위반)" 줄이 생긴다.
- `after/adapters.py`에 `class FailingRepository`를 만들어 `save`에서 예외를 던지게 하고 `main.py`에서 꽂으면,
  `domain.py`를 고치지 않고 저장 실패 상황을 시험할 수 있다.
