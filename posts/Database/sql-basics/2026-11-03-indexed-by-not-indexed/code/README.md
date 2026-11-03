# 예제 코드 — INDEXED BY와 NOT INDEXED — 옵티마이저에 손을 대는 두 구문

표준 라이브러리만 쓴다. 메모리 DB에 2만 행을 넣고 두 구문의 계획과 수행량을 비교한다.

## 실행

```bash
python indexed_by_demo.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `indexed_by_demo.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `SEED` — 난수 시드. 바꾸면 급여 분포가 달라져 스텝 수가 함께 움직인다
- `ROW_COUNT` — 행 수. 줄이면 전체 훑기와 인덱스 탐색의 차이가 좁아진다
- `salary > 8000` 의 경계값 — 8000을 4000 쪽으로 내리면 급여 인덱스로 걸러지는
  행이 늘어, ANALYZE 뒤에도 부서 인덱스가 더 싸지는 지점이 나온다
