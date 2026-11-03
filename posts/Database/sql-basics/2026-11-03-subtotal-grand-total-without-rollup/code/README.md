# 예제 코드 — 소계와 총계를 한 결과에

표준 라이브러리만 쓴다. 메모리 DB 에 매출 7건을 만들고, `GROUP BY` 결과에
소계·총계 행을 붙이는 방법 셋을 돌려 결과와 질의 계획을 본다.

## 실행

```bash
python subtotal_rows.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `subtotal_rows.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `SALES` — 매출 행. 지역을 하나 더 넣으면 5절의 소계가 한 묶음 늘어난다
- 4절의 `ORDER BY ord, region` 에서 `ord` 를 빼면 3절과 같은 결과가 된다
- 7절의 `MATERIALIZED` 를 `NOT MATERIALIZED` 로 바꾸면 계획이 코루틴으로 돌아간다
- 9절의 지역별 건수를 똑같이 맞추면 평균의 평균과 전체 평균이 같아진다
