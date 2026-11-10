# 예제 코드 — Misra-Gries와 Space-Saving

파이썬 표준 라이브러리만 쓴다. 난수 시드는 42로 고정했다.

## 실행

```bash
python heavy_hitters.py
```

## 바꿔 볼 값

- `ZIPF_EXPONENT` 를 0.8 로 낮추면 쏠림이 약해져 두 알고리즘의 오차가 상한에 가까워진다
- `compare()` 의 칸 수(9, 49)를 바꾸면 상한 n/(m+1), n/m 이 같이 바뀐다
- `burst_at_end()` 의 끝 항목 수를 늘리면 Space-Saving 상위 목록에서 늦게 온 항목이 차지하는 칸이 늘어난다
