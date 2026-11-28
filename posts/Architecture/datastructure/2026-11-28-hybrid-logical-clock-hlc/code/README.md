# 하이브리드 논리 시계(HLC) 시뮬레이션

Kulkarni 외(2014)의 HLC 알고리즘(Figure 5)과 단순 알고리즘(Figure 3)을 구현해, 시계가 어긋난
노드 사이에서 물리 시각·HLC가 인과 순서를 지키는지와 l − pt, c 의 최댓값을 잰다.
표준 라이브러리만 쓰고 난수 시드는 고정돼 있다.

## 실행

```bash
python hlc_sim.py
```

## 바꿔 볼 값

- `main()`의 `offsets` 목록 — 노드별 시계 오프셋(ms). ε(가장 빠른 시계와 가장 느린 시계의 차이)이 바뀐다
- `simulate()`의 전송 지연 `rng.randint(1, 20)` — 지연이 짧을수록 물리 시각 위반이 늘어난다
- `burst_loop()`의 `hops_per_ms` — 1ms 안에 일어나는 사건 수
