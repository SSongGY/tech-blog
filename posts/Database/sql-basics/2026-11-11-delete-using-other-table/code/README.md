# 예제 코드 — 다른 표를 기준으로 행 지우기

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python delete_other_table.py
```

실험마다 `BEGIN` 안에서 지우고 `ROLLBACK` 하므로 모든 실험이 같은 6행에서 시작한다.

## 바꿔 볼 값

- `removed_pair` 에 `(3, 20)` 을 더 넣으면 3)의 "컬럼마다 IN" 이 지우는 행 수가 어떻게 바뀌는지 본다
- `discontinued` 에 `NULL` 을 넣을 수 있게 표 정의에서 `PRIMARY KEY` 를 빼고, 2)를 `NOT IN` 으로 바꿔 돌려 본다 — 같은 저장소의 `in-exists-not-in-null` 글이 다룬 함정이 DELETE 에서도 나는지 확인할 수 있다
