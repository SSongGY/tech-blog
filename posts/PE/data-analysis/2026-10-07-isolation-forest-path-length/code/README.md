# 예제 코드 — Isolation Forest 의 경로 길이와 이상 점수

Liu·Ting·Zhou(ICDM 2008)의 알고리즘 1~3(iForest·iTree·PathLength)과 식 1·2를 그대로
구현해 네 가지를 확인한다. 파이썬 표준 라이브러리만 쓴다.

1. 정규화 상수 c(n) 과 높이 제한 ceil(log2 n)
2. 중심점·가장자리·고립점의 평균 경로 길이와 점수
3. 이상치가 빽빽한 군집일 때 부분표본 크기 ψ 가 점수에 주는 영향 (swamping·masking)
4. 값 범위 안의 형상 이상을 값 하나로 볼 때와 슬라이딩 창으로 볼 때

## 실행

```bash
python iforest_demo.py
```

## 바꿔볼 값

- `experiment_subsampling` 의 이상 군집 표준편차 `0.15` 를 키우면 군집이 흩어져 ψ 에 따른 차이가 줄어든다.
- `experiment_time_series` 의 창 길이 목록에 `50`(한 주기)을 넣어 본다.
