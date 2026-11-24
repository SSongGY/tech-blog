# 예제 코드 — FODA 피처 모델의 유효 구성 세기

파이썬 표준 라이브러리만 쓴다. Python 3.13.5 에서 돌렸다.

## 실행

```bash
python feature_configs.py
```

## 바꿔 볼 값

- `CAR_REQUIRES` 를 비우면 [1] 의 유효 구성이 8개로 돌아간다
- `CAR_MUTEX` 에 `("automatic", "air_conditioning")` 을 넣으면 자동 변속기와 에어컨을 함께 고를 수 없는 계열이 된다
- [3] 의 피처 수를 10 에서 늘리면 원시 조합이 2 의 거듭제곱으로 늘어나 열거가 금방 느려진다
- Horsepower 를 두 구간으로 나눈 것은 설명용이다. 원 보고서의 그림 5-1 에는 값 피처로만 있다
