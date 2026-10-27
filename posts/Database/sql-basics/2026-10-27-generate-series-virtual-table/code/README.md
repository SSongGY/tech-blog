# 없는 행을 만들어 쓰기 — 예제

메모리 SQLite 에 주문 로그를 만들고, 날짜 빈칸을 채우는 세 가지 방법을
같은 데이터 위에서 돌려 본다. 표준 라이브러리만 쓰므로 설치할 것이 없다.

## 실행

```bash
python series_fill.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `series_fill.py` | 본문에 실린 질의를 순서대로 돌린다 |
| `dbshow.py` | 표 정의와 행을 출력 맨 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `probe_series.py` | 이 빌드에 `generate_series` 가 있는지 확인한 기록 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- `FIRST_DAY` · `LAST_DAY` — 달력 범위. 범위를 늘리면 재귀 깊이가 그만큼 늘어난다
- `ORDER_ROWS` — 주문이 없는 날을 더 만들거나 없애 본다
- 5번 단계의 `digit` 교차 조인 — `tens`/`ones` 두 벌이면 0~99 다.
  `hundreds` 를 한 벌 더 붙이면 0~999 가 된다
