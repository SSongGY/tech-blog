# 예제 코드 — OR REPLACE 의 부작용

표준 라이브러리만 쓴다. 메모리 DB 를 케이스마다 새로 만들어 같은 위반을 다섯 가지 해결 방식으로 겪게 한다.

## 실행

```bash
python conflict_demo.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `conflict_demo.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- 1번의 `VALUES (4, 'D', 40), (5, 'B', 50), (6, 'E', 60)` 에서 충돌하는 행의 위치를 바꾸면 FAIL 이 남기는 행이 달라진다
- 4번에서 `PRAGMA foreign_keys = ON` 을 지우면 `login_log` 가 지워지지 않는다
