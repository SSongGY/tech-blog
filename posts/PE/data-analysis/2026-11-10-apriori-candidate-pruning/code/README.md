# 예제 코드 — Apriori 와 FP-growth 의 빈발 항목집합 비교

파이썬 3.10 이상 표준 라이브러리만 쓴다. 설치할 것이 없다.

## 실행

```bash
python apriori.py
```

## 바꿔볼 값

- `MIN_SUPPORT` 를 `2` 로 낮추면 후보와 빈발 항목집합이 얼마나 늘어나는지 본다
- `TRANSACTIONS` 에 거래를 더해 Apriori 의 DB 스캔 횟수(가장 긴 빈발 항목집합 길이 + 1 이하)가 어떻게 변하는지 본다
