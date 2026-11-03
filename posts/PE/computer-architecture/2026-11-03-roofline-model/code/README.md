# 예제 코드 — 루프라인 모델 검산

Williams · Waterman · Patterson 의 루프라인 논문(UCB/EECS-2008-134)에 적힌 수치
(Opteron X2 의 최대 연산 성능·대역폭, 천장 값, 커널별 연산강도)를 그대로 넣고
능선점과 커널별 상한을 계산한다. 표준 라이브러리만 쓴다.

## 실행

```bash
python roofline_calc.py
```

## 바꿔볼 값

- `PEAK_GFLOPS`, `PEAK_GBPS` — 자기 장비의 값으로 바꾸면 능선점이 그 장비 것이 된다.
  최대 연산 성능은 사양표에서, 대역폭은 STREAM 같은 벤치마크로 잰 값을 쓴다
- `KERNELS` — 연산강도를 바꿔 넣으면 어느 바운드인지와 상한이 따라 바뀐다
- `MEMORY_CEILINGS`, `COMPUTE_CEILINGS` — 천장은 장비마다 다르다. 논문 §4 가
  설명하듯 마이크로벤치마크로 한 번 재 두면 그 장비의 모든 커널에 다시 쓴다
