# 예제 코드 — R*Tree 가상 테이블로 겹치는 기간 찾기

표준 라이브러리만 쓴다. 메모리 DB에 예약 20만 건을 보통 표와 `rtree` 가상 테이블에
같은 내용으로 넣고, 기간이 겹치는 행을 찾는 질의의 계획과 시간을 비교한다.

## 실행

```bash
python rtree_overlap.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `rtree_overlap.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `BOOKING_COUNT` — 예약 건수. 줄이면 B-tree 쪽도 충분히 빨라져 차이가 작아진다
- `QUERY_START`, `QUERY_END` — 찾는 기간. `DAY_SPAN` 가까이로 옮기면
  `start_day <= ?` 를 만족하는 행이 거의 전부가 되어 B-tree 쪽이 더 느려진다
- `MAX_STAY_DAYS` — 예약 하나의 길이 상한. 키울수록 겹치는 건수가 늘어난다
- §5 의 `samples` 에 2^24(16,777,216) 아래 값을 넣으면 `rtree` 도 정확히 돌려준다

시간 측정값은 PC 상태에 따라 흔들린다. 계획(`QUERY PLAN`)과 건수는 같아야 한다.
