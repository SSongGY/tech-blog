# 예제 코드 — 파티셔닝이 항상 빨라지지 않는 이유

메모리 SQLite에 같은 30,000행을 두 가지 모양으로 넣는다. 통짜 표 `order_flat` 하나와,
연도별로 쪼갠 `order_2024`·`order_2025`·`order_2026`을 `UNION ALL`로 묶은 뷰 `order_part`다.
통짜 표에는 전역 인덱스 두 개(`ordered_on`, `customer_id`), 각 파티션에는 `customer_id`
로컬 인덱스를 둔다. 같은 질의를 양쪽에 돌려 `EXPLAIN QUERY PLAN`과 일의 양을 비교한다.

일의 양은 시간이 아니라 **VDBE 명령 실행 횟수**로 잰다. `sqlite3.Connection.set_progress_handler`를
간격 1로 걸면 가상 머신 명령마다 콜백이 불리므로, 같은 입력이면 몇 번을 돌려도 같은 수가 나온다.
난수 시드는 42로 고정했다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python partition_pruning_cost.py
```

## 바꿔볼 값

- `ROWS_PER_YEAR`를 100,000으로 올려 3번(비파티션 키 조회)의 배수가 어떻게 변하는지 본다.
- 각 파티션의 `customer_id` 로컬 인덱스 생성을 지우고 3번을 다시 돌려 본다.
- `YEARS`에 2027·2028을 더해 파티션 수가 늘 때 5번(전 구간 집계)이 어떻게 되는지 본다.
