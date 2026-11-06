# 예제 코드 — max(a, b)와 MAX(col)

표준 라이브러리만 쓴다. 두 개의 작은 표로 스칼라 `max()` 와 집계 `max()` 의 차이를 본다.

## 실행

```bash
python max_scalar_aggregate.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `max_scalar_aggregate.py` | 본문 출력을 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `exam_score` 에 두 점수가 모두 NULL 인 행을 더 넣어 3)의 `fixed` 가 어떻게 되는지 본다
- `product` 에서 `juice` 와 `coffee` 의 가격을 바꿔 5)의 동점 처리를 본다
- 4)에서 `'10'` 대신 `'abc'`, `X'00'`(BLOB) 을 넣어 타입 순서를 확인한다
