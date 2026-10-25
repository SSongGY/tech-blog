# AR(1)·MA(1) 식별 확인

AR(1)과 MA(1) 표본경로를 만들어 자기상관함수(ACF)와 편자기상관함수(PACF)가
NIST/SEMATECH e-Handbook §6.4.4.6의 식별 규칙대로 끊기는지 확인한다.
표준 라이브러리만 쓴다.

## 실행

```bash
python arma_identify.py
```

## 환경

- Python 3.13.5
