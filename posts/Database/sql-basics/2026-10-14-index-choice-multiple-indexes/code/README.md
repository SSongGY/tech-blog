# 인덱스가 여럿일 때 무엇이 쓰이는가 — 예제

표준 SQL 과 파이썬 내장 `sqlite3` 만 쓴다. 따로 설치할 것이 없다.

## 실행

```bash
python index_choice.py
```

## 무엇을 보여 주는가

같은 2,000행, 같은 두 인덱스(`idx_emp_emp_no`, `idx_emp_status`)를 담은 DB 를
두 판 만든다. 둘의 차이는 **테이블에 컬럼을 선언한 순서 한 가지뿐**이다.

- `A판` — `emp_no`, `status` 순
- `B판` — `status`, `emp_no` 순

통계가 없을 때는 두 판의 실행계획이 갈리고, `ANALYZE` 를 돌린 뒤에는 둘 다
선택도가 높은 `idx_emp_emp_no` 로 모인다.

## 바꿔 볼 값

| 값 | 위치 | 바꾸면 |
|---|---|---|
| `ROW_COUNT` | `index_choice.py` 위쪽 | 행 수. 줄여도 선택 결과는 같다 |
| `status` 분포 | `build_database()` 의 `i % 100` | `i % 2` 로 바꾸면 두 값이 1,000행씩 고르게 나뉜다 |
| `QUERY` | 모듈 상수 | 조건을 하나만 남기면 고를 것이 없어 비교가 사라진다 |

## 파일

| 파일 | 무엇 |
|---|---|
| `index_choice.py` | 본문에 실은 예제 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |
