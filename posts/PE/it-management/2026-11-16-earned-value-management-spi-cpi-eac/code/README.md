# 예제 코드 — 획득가치관리(EVM) 지표 계산

파이썬 표준 라이브러리만 쓴다. 설치할 것이 없다. Python 3.13.5 에서 돌렸다.

## 실행

```bash
python evm_calc.py
```

## 바꿔 볼 값

- `monthly_actual` 을 `monthly_earned` 와 똑같이 바꾸면 CPI 가 1.0 이 되고 세 EAC 중 `EAC(1.0)` 과 `EAC(CPI)` 가 같아진다
- `monthly_earned` 앞쪽을 키우고 뒤쪽을 줄이면 초반 SPI 가 1 을 넘는다. 그래도 완료 시점에는 SPI 가 1.0 이 된다
- `print_status` 에 넘기는 시점을 바꿔 EAC 세 식이 실제 최종 원가에 언제 가까워지는지 본다
