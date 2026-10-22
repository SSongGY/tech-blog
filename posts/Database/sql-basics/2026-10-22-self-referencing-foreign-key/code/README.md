# 예제 코드 — 자기참조 외래키 — 계층 데이터를 한 표에 담기

조직도 8행을 메모리 SQLite 에 넣고, 같은 표를 자기 자신과 잇는 외래키가
어디까지 영향을 주는지 여섯 가지로 확인한다. 추가 의존성은 없다.

## 실행

```bash
python self_fk.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `self_fk.py` | 본문의 출력 여섯 덩이를 그대로 찍는다 |
| `dbshow.py` | 표 정의와 데이터를 앞에 깔아 주는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- `SEED_ROWS` 의 `parent_id` — 트리 모양을 바꿔 보면 재귀 CTE 의 `depth` 가 따라 바뀐다.
- `build_database()` 의 `PRAGMA foreign_keys = ON` 을 `OFF` 로 — 3번의 `IntegrityError`
  가 사라지고, 4번의 `ON DELETE CASCADE` 도 함께 멈춘다. 둘 다 같은 스위치에 달려 있다.
- `SCHEMA` 의 `ON DELETE CASCADE` 를 `ON DELETE SET NULL` 로 — 손자 부서가 지워지는
  대신 뿌리 없는 부서로 남는다.
- 5번의 `UPDATE ... SET parent_id = 5` 대상 — 어느 행으로 고리를 만들어도 외래키 검사는
  통과한다.
