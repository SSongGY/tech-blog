# 예제 코드 — t-digest 척도 함수와 꼬리 분위수 오차

파이썬 표준 라이브러리만 쓴다. 설치할 것이 없다. Python 3.13.5 에서 돌렸다.
난수 시드는 `SEED = 20261122` 로 고정했다. 표본 100만 개를 네 번 넣으므로 수십 초 걸린다.

- `tdigest.py` — Dunning·Ertl(2019) Algorithm 1 의 병합 t-digest, 척도 함수 k0·k1
- `measure.py` — 정확한 분위수와 비교해 순위 오차를 찍는다

## 실행

```bash
python measure.py
```

## 바꿔 볼 값

- `DELTA` 를 50·200 으로 바꾸면 클러스터 수 상한(⌈δ⌉)과 오차가 함께 움직인다
- `TDigest(..., buffer_factor=10)` 을 1 로 줄이면 병합이 더 자주 일어난다. 오차가 얼마나 변하는지 본다
- `make_samples` 를 `rng.random()`(균등분포)로 바꾸면 분포 모양이 오차에 주는 영향을 볼 수 있다
