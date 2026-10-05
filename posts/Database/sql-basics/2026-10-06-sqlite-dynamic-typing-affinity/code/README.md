# 예제 코드 — 자료형 — SQLite의 동적 타입

메모리 SQLite에 고객 표를 만들고, 선언한 타입과 실제로 저장되는 값의 종류(`typeof()`)가
어떻게 갈리는지 찍는다. 같은 값을 친화성이 다른 다섯 컬럼에 넣어 보고, 선언 이름이 어떤
친화성으로 읽히는지, 비교·정렬·합계에서 무엇이 달라지는지, `STRICT` 표가 무엇을 막는지 본다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python dynamic_typing.py
```

## 바꿔볼 값

- `SCHEMA` 의 `zip_code STRING` 을 `zip_code TEXT` 로 바꾸면 0-A 에서 앞자리 0이 남고, 3-A 가 한 행도 찾지 못한다.
- `show_affinity_by_name` 의 `declared` 에 `"POINT"`, `"INTERVAL"` 을 넣어 보면 각각 어느 규칙에 걸리는지 보인다.
- `SEED` 의 `"1,200"` 을 `"1200"` 으로 바꾸면 3-F 의 합계가 3500 이 된다.
