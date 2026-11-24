# 예제 코드 — ARC 와 LRU 의 적중률

파이썬 표준 라이브러리만 쓴다. Python 3.13.5 에서 돌렸다. 난수는 `SEED` 로 고정했다.

## 실행

```bash
python arc_vs_lru.py
```

## 바꿔 볼 값

- `hot_with_scans` 의 `scan_len` 을 200 에서 40 으로 줄이면 스캔이 캐시를 다 밀어내지 못해 LRU 도 뜨거운 키를 지킨다
- `capacity` 를 120 으로 올리면 `loop_120` 에서 LRU 의 적중률이 0 에서 거의 100 으로 뛴다
- `ArcCache.access` 의 Case II·III 에서 `self.p` 를 고치는 줄을 지우면 p 가 0 에 고정된 FRC 가 된다. 적중률이 어떻게 바뀌는지 본다
- `opt_hits` 는 미래 접근을 아는 벨러디 최적이라 실제 캐시가 아니라 상한선이다
