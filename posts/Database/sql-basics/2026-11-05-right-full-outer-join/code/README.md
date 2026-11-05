# 예제 코드 — RIGHT JOIN과 FULL OUTER JOIN

표준 라이브러리만 쓴다. 메모리 DB에 주문 4건과 입금 4건을 만들고 외부 조인 세 종류와 예전 우회 방식을 같은 데이터로 비교한다.
`RIGHT` · `FULL OUTER JOIN` 은 SQLite 3.39.0 이상에서만 돈다.

## 실행

```bash
python outer_join_demo.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `outer_join_demo.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `PAYMENTS` 에서 `order_id` 가 9인 행을 지우면 3번 결과에서 주문 없는 입금이 사라진다
- 6번의 `1000` — 기준을 올리면 ON 에 둔 쪽과 WHERE 에 둔 쪽의 행 수 차이가 더 벌어진다
