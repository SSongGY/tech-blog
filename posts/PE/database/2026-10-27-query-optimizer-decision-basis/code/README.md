# 선택도 산식 검산

비용 기반 옵티마이저가 행 수를 추정할 때 쓰는 선택도 산식을, PostgreSQL 16
문서의 행 수 추정 예제에 적힌 통계값을 그대로 넣어 다시 계산한다.
문서에 적힌 값과 맞는지 나란히 찍는다. 표준 라이브러리만 쓴다.

## 실행

```bash
python selectivity_check.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `selectivity_check.py` | 선택도 6가지 경우를 계산하고 문서 값과 대조한다 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- 마지막 단계의 `n_distinct` 목록 — 고유값 추정치만 틀렸을 때 행 수 추정이
  얼마나 밀리는지 본다
- `HISTOGRAM_BOUNDS` — 버킷 경계를 바꿔 같은 값의 선택도가 어떻게 달라지는지 본다

> 출처: [PostgreSQL 16 — 76.1. Row Estimation Examples](https://www.postgresql.org/docs/16/row-estimation-examples.html)
