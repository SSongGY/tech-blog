# ANALYZE와 통계 — 예제 코드

파이썬 표준 라이브러리의 `sqlite3` 모듈만 쓴다. 따로 설치할 것이 없다.

## 실행

```bash
python main.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `main.py` | 통계 없음 → ANALYZE → 데이터 변경 → 재-ANALYZE 순서로 계획을 찍는다 |
| `dbshow.py` | 표 정의와 데이터를 출력 맨 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |

## 바꿔 볼 값

- `build_database()` 의 `i % 50` — 부서 수를 2로 줄이면 두 인덱스의 선택도가
  비슷해져서 ANALYZE 를 해도 계획이 안 바뀐다. 통계가 언제 쓸모없는지 보인다.
- `"active" if i % 10 else "retired"` — 재직 비율을 바꾸면 `sqlite_stat1` 의
  두 번째 숫자(값 하나당 평균 행 수)가 그대로 따라 움직인다.
- 4번 절에서 넣는 9,000행을 900행으로 줄이면 통계가 낡아도 계획이 안 바뀐다.
  통계가 얼마나 틀어져야 손해가 되는지 가늠해 볼 수 있다.
