# Box-Jenkins 모형화 절차 검산

ARIMA(1,1,1) 표본경로를 만들어 식별-추정-진단 3단계를 그대로 따라간다.
statsmodels·numpy 없이 표준 라이브러리만 쓴다. 난수는 선형합동법으로 만들어
어느 기계에서 돌려도 같은 표본경로가 나온다.

- 정상성 판정 — 구간별 평균·분산, ACF 감쇠 모양, 과대차분 점검
- 식별 — ACF·PACF 와 ±2/√n 유의대역
- 추정 — Hannan-Rissanen 2단계 회귀, AIC·BIC 로 차수 선택
- 진단 — Ljung-Box Q 통계량과 카이제곱 꼬리확률 (직접 구현, 임계값으로 검산)
- 예측 — 차분계열 예측을 누적해 수준으로 되돌리기

## 실행

```bash
python box_jenkins.py
```
