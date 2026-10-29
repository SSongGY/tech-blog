# 파라미터 바인딩 예제

문자열 조합과 파라미터 바인딩이 값에 하는 일을 일곱 가지 상황에서 나란히 돌려 본다.
따옴표·NULL·타입·자리표시자 문법·IN 목록·식별자·반복 비용 순서다.

표준 라이브러리만 쓴다. 설치할 것이 없다.

## 실행

```bash
python binding_basics.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `binding_basics.py` | 본문에 실은 일곱 절을 순서대로 돌린다 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍어 주는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- `demo_reuse(conn, repeat=...)` — 반복 횟수. 기본 20000.
  횟수를 줄이면 세 방식의 차이가 측정 잡음에 묻힌다
- `SEED` — 표에 들어가는 행. `nickname` 에 따옴표가 든 값과 `None` 이 하나씩 있어야
  1·2절이 뜻을 갖는다
- `demo_identifier` 의 `allowed` — 허용 목록에 없는 컬럼 이름을 넣으면
  `ValueError` 로 막히는 것을 볼 수 있다
