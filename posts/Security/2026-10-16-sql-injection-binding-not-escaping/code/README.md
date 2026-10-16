# SQL 인젝션 — 예제 코드

파이썬 표준 라이브러리의 `sqlite3` 모듈만 쓴다. 따로 설치할 것이 없다.
표에 들어 있는 값은 전부 가상의 예제 값이다.

## 실행

```bash
python main.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `main.py` | 문자열 조합 → 이스케이프 → 바인딩 순서로 같은 입력을 넣어 본다 |
| `dbshow.py` | 표 정의와 데이터를 출력 맨 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |

## 바꿔 볼 값

- `tautology` 를 `" OR 1=1 --` 처럼 큰따옴표로 바꿔 보면, SQLite 가 큰따옴표를
  식별자로 먼저 해석하는 탓에 결과가 달라진다.
- 5번 절의 `numeric` 을 `0 UNION SELECT login, secret FROM member` 로 바꾸면
  컬럼 수가 맞을 때 다른 표의 값이 섞여 나오는 것을 볼 수 있다.
- 8번 절의 `allowed` 집합에서 `role` 을 빼면 허용 목록이 어떻게 막는지 보인다.
