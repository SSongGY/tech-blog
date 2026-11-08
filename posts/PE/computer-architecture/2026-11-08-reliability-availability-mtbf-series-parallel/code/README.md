# 예제 코드 — 신뢰도와 가용성 계산

파이썬 표준 라이브러리만 쓴다. 난수 시드는 고정(`20261108`)이라 몇 번을 돌려도 같은 값이 나온다.

## 실행

```bash
python reliability.py
```

## 바꿔볼 값

- `section_structures` 의 임무 시간 `t` 를 1,000 시간으로 줄여 병렬 구성의 이득이 얼마나 작아지는지 본다
- `section_availability` 에서 MTBF 와 MTTR 을 같은 비율로 키워도 A 가 그대로인 것을 확인한다
- `section_service` 의 DB 가용도를 0.99 로 낮춰 이중화한 웹·WAS 의 효과가 어디까지 가려지는지 본다
