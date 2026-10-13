# CHECK 제약 예제

SQLite 메모리 DB 위에서 CHECK 제약이 무엇을 막고 무엇을 못 막는지 확인한다.
외부 의존성이 없고 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python check_constraint.py
```

## 파일

| 파일 | 내용 |
|---|---|
| `check_constraint.py` | 본문에 실린 여섯 장면을 순서대로 실행한다 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍는 도우미 (저장소 공용) |
| `output.txt` | 실제로 돌린 기록. 본문의 출력은 전부 여기서 가져왔다 |

## 바꿔 볼 값

- `demo_text_leak()` 의 `one_sided` CHECK 를 `v >= 0` 에서 `v <= 100` 으로
  뒤집어 본다. 이번에는 `'abc'` 가 거부된다. 어느 쪽을 막느냐에 따라 결과가
  갈리는 것이 이 예제의 핵심이다.
- `demo_tighten()` 의 `typed_check` 에서 `typeof(v) = 'integer'` 를 빼 보면
  `'abc'` 가 다시 통과한다.
- `demo_existing_violations()` 의 `max(0, min(100, coalesce(v, 0)))` 을
  빼고 돌리면 한 행 때문에 네 행이 모두 안 들어간다.
