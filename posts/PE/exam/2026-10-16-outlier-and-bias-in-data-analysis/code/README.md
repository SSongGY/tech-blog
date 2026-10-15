# 이상치와 편향 — 계산 검산

답안의 Ⅲ절과 Ⅳ절에 실은 숫자를 직접 계산한다. 외부 의존성이 없고 파이썬 표준
라이브러리만 쓴다.

- `outlier_bias.py` — 세 가지를 차례로 계산한다
  1. 이상치 한 점이 평균·표준편차를 움직이는 폭, IQR 울타리와 수정 Z 점수로 검출
  2. 표본 구성이 치우쳤을 때 집단별 결론과 전체 결론이 갈리는 모습(심슨의 역설)
  3. 전역 울타리로 이상치를 일괄 제거했을 때 집단별 절삭률이 갈리며 생기는 편향

검출 기준은 NIST/SEMATECH *e-Handbook of Statistical Methods* 를 따른다.

- 사분위 울타리 — 안쪽 1.5×IQ, 바깥쪽 3×IQ (§7.1.6 What are outliers in the data?)
- 수정 Z 점수 — `0.6745·(x − 중앙값)/MAD`, 절댓값 3.5 초과 시 이상치 후보
  (§1.3.5.17 Detection of Outliers)

데이터는 전부 가상이다. 실제 서비스 로그나 고객 데이터를 쓰지 않았다.

## 실행

```bash
python outlier_bias.py
```

환경: Python 3.13.5, Windows 11
