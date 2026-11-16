# Roaring 비트맵 — 컨테이너 전환과 크기

Chambi 외(2016) 논문의 2~4장을 파이썬 표준 라이브러리로 구현하고 크기·연산 횟수를 센다.
`roaring.py` 가 자료구조, `experiment.py` 가 측정이다. 난수 시드는 고정돼 있다.

## 실행

```bash
python experiment.py
```

## 바꿔 볼 값

- `roaring.py` 의 `ARRAY_LIMIT` 를 2048·8192 로 바꾸면 [2]·[3] 에서 원소당 비트가 어떻게 달라지는지 본다
- `experiment.py` 의 `UNIVERSE` 를 키우면 청크 수가 늘어 1단계 색인 비중이 커진다
- [4] 는 넣고 빼는 경계를 같은 값(4096)으로 둔 논문 3장 규칙의 비용이다. `RoaringBitmap.remove` 의 기준을 2048 처럼 낮춰 다시 돌려 보면 변환 횟수가 어떻게 바뀌는지 볼 수 있다
