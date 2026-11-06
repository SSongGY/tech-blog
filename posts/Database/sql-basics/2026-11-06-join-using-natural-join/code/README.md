# 예제 코드 — JOIN USING과 NATURAL JOIN

표준 라이브러리만 쓴다. 같은 데이터로 `ON`·`USING`·`NATURAL JOIN` 을 돌려 결과 컬럼 수를 비교하고, 양쪽 표에 같은 이름의 컬럼이 생겼을 때 `NATURAL JOIN` 결과가 바뀌는 것을 `ALTER TABLE` 로 재현한다.

## 실행

```bash
python join_using.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `join_using.py` | 본문 출력을 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `SCHEMA` 의 `INSERT` — 부서가 없는 사원, 사원이 없는 부서를 더 넣어 `LEFT JOIN` 결과를 본다
- `part_three` 의 `UPDATE` — `note` 값을 NULL·빈 문자열·다른 문자열로 바꿔 `NATURAL JOIN` 이 몇 행을 주는지 본다
