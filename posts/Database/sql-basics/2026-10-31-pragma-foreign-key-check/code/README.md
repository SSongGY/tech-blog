# PRAGMA foreign_key_check 예제

외래키 강제를 끈 채 쌓인 데이터에서 깨진 참조를 찾아내고, 고친 뒤 제약을 켜는
순서를 그대로 재현한다. 메모리 DB만 쓰므로 파일을 만들지 않는다.

## 실행

```bash
python fk_check_demo.py
```

추가 설치는 없다. 표준 라이브러리 `sqlite3` 만 쓴다.

## 바꿔 볼 값

- `SEED` 의 `(3, '이서아', 30, 1)` 에서 `30` 을 `10` 으로 바꾸면 그 위반이 사라진다.
  결과에서 `team` 쪽 줄이 빠지는 것을 확인한다.
- `badge` 표의 `WITHOUT ROWID` 를 지우면 5번 절의 두 번째 칸이 `NULL` 대신
  실제 rowid 로 나온다.
- 6번 절에서 `UPDATE employee SET mentor_id = NULL WHERE emp_id = 4` 를 빼면
  자기 참조 외래키 위반이 끝까지 남는다.

## 파일

| 파일 | 무엇 |
|---|---|
| `fk_check_demo.py` | 본문에 실은 예제 전체 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |
