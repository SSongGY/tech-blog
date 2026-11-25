# 예제 코드 — 누적 비율로 ABC 등급 나누기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.
Python 3.13.5, SQLite 3.49.1 에서 돌렸다. `dbshow.py` 는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python abc_grade.py
```

## 바꿔 볼 값

- `P05` 의 매출을 80 에서 79 로 바꾸면 동점이 사라져 [3] 의 `cum_range` 와 `cum_rows` 가 같아지고, [5] 도 [4-2] 와 같은 결과를 낸다
- [6] 의 `80 * total` 을 `70 * total` 로 바꾸면 경계 행이 `P03` 으로 옮겨 간다. `P03` 의 누적 전 비율은 60% 다
- [4-1] 과 [4-2] 를 섞어 쓰지 않는다. 한 보고서 안에서 기준을 하나로 정하고 그 기준을 표 머리에 적는다
- `GROUPS` 프레임(SQLite 3.28.0 부터)으로 바꾸면 동점 행을 한 묶음으로 다룬다. [3] 에 `GROUPS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` 를 넣어 `RANGE` 와 같은 값이 나오는지 본다
