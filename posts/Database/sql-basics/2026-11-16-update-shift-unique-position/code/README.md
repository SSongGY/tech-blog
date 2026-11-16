# UPDATE pos = pos + 1 과 UNIQUE

재생 목록 순번을 한 칸씩 밀 때 UNIQUE 제약에 걸리는 경우와 우회 방법을 SQLite 로 돌린다.
표준 라이브러리만 쓴다.

## 실행

```bash
python shift_position.py
```

## 바꿔 볼 값

- `[3-B]` 의 INSERT 에서 `item_id` 와 `position` 의 짝을 섞어 보면, 읽는 순서에 따라 성공·실패가 갈리는 것을 더 볼 수 있다
- `[6]` 의 `1000001` 을 표에 있는 최대값보다 작게 바꾸면 우회가 다시 충돌한다
