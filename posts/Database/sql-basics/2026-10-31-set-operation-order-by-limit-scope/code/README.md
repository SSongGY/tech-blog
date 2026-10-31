# 예제 코드 — 집합 연산에서 ORDER BY와 LIMIT이 걸리는 위치

메모리 SQLite에 서울·부산 점수표를 만들고, `UNION`·`UNION ALL`에 정렬과 개수
제한을 **어디에 적느냐**에 따라 결과가 어떻게 달라지는지 나란히 돌려 본다.
문법 오류가 나는 질의도 일부러 포함했고, 에러 메시지를 그대로 남긴다.

의존성은 없다. 파이썬 표준 라이브러리의 `sqlite3`만 쓴다.

## 실행

```bash
python set_operation_scope.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `set_operation_scope.py` | 본문에 실은 질의를 전부 돌린다 |
| `dbshow.py` | 표 정의와 실제 행을 출력 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | 돌린 기록. `blog.py run-example`이 만든다 |

## 바꿔 볼 값

- `BUSAN_ROWS`의 `("가은", 90)`을 지우면 `UNION`과 `UNION ALL`의 행 수가 같아진다.
  겹치는 행이 하나도 없으면 중복 제거가 할 일이 없다
- 3절 서브쿼리의 `LIMIT 2`를 `LIMIT 1`로 바꾸면 지역별 1등만 모인다.
  이게 다른 DB에서 윈도 함수로 푸는 "그룹별 상위 N" 문제다
- 5절의 `LIMIT 2, 3`에서 숫자를 바꿔 보면 앞이 OFFSET이라는 것이 바로 보인다
