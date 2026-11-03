# 예제 코드 — VALUES 절을 표처럼 쓰기

표준 라이브러리만 쓴다. 메모리 DB에 매출 4건과 5만 행짜리 표를 만들고,
코드 매핑표를 `VALUES` 로 끼워 넣었을 때 무엇이 되고 무엇이 안 되는지 확인한다.

## 실행

```bash
python values_as_table.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `values_as_table.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `CHANNEL_CODES` — 코드표. 항목을 빼면 그 코드가 §4 의 "코드표에 없는 값"으로 넘어간다
- `BIG_ROW_COUNT` — §5 에서 조인 상대가 되는 표의 행 수.
  줄이면 인덱스가 없어도 전체 훑기가 싸져서 계획이 그대로일 수 있다
- §6 의 `VALUES ('1')` 을 `VALUES (1)` 로 바꾸면 두 매칭 건수가 모두 1이 된다
