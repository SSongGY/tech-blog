# 예제 코드 — 캐시 쓰기 정책 시뮬레이터

파이썬 표준 라이브러리만 쓴다. 난수를 쓰지 않으므로 결과는 매번 같다.

## 실행

```bash
python write_policy_sim.py
```

## 바꿔 볼 값

- `LINE_WORDS` 를 1 로 줄이면 줄 크기가 쓰기 단위와 같아져 fetch-on-write 가 읽어 온 줄이 전부 버려진다 (Jouppi §4 의 지적)
- `LINE_WORDS` 를 8 이상으로 늘리면 write-validate 가 남기는 무효 워드가 늘어 이점이 줄어든다
- 패턴 함수를 새로 만들어 `PATTERNS` 에 넣으면 같은 표가 하나 더 찍힌다
