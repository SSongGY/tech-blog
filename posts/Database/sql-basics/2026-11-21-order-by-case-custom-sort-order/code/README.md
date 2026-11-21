# 예제 코드 — ORDER BY CASE — 가나다순이 아닌 업무 순서로 정렬하기

파이썬 표준 라이브러리 `sqlite3` 만 쓴다. SQLite 3.49.1 에서 돌렸다.

## 실행

```bash
python custom_sort.py
```

## 바꿔 볼 값

- `[3-1]` 의 CASE 에 `ELSE` 가 없을 때 `'later'` 와 `NULL` 이 맨 위로 오는 것을, `ORDER BY ... NULLS LAST` 로 바꿔 비교해 본다
- `priority_rank` 표의 `sort_rank` 값을 바꾸면 질의를 고치지 않고 순서가 바뀐다
- `[7-2]` 처럼 식 인덱스와 글자가 다른 CASE 를 쓰면 인덱스를 타는지 본다
