# 예제 코드 — B-Tree 인덱스를 못 타는 조건들

`app_user` 테이블 20만 행을 메모리 SQLite에 만들고, WHERE 절 표현만 바꿔가며
`EXPLAIN QUERY PLAN` 결과와 실행 시간을 측정한다.

## 요구 사항

- Python 3.9 이상 (표준 라이브러리만 사용, 추가 설치 없음)

## 실행

```bash
python index_probe.py
```

Windows 콘솔에서 한글이 깨지면 `PYTHONUTF8=1`을 앞에 붙인다.

## 출력 구성

| 섹션 | 내용 |
|---|---|
| `[A] SELECT user_id` | 인덱스만 읽어도 답이 나오는 커버링 상황 |
| `[B] SELECT login_name` | 인덱스에 없는 컬럼이라 테이블 재접근이 필요한 상황 |
| `[추가]` | `lower(email)` 표현식 인덱스를 만든 뒤 재측정 |

## 측정 조건

- 데이터는 `RANDOM_SEED = 20260918`으로 고정되어 매번 같은 값이 생성된다
- 각 케이스를 5회 실행해 **최솟값**을 쓴다 (`REPEAT_COUNT`)
- `status` 분포는 `active` 70% / `dormant` 25% / `locked` 5%로 의도적으로 치우쳐 있다
- 측정 전 `ANALYZE`로 통계를 수집한다. 통계가 없으면 스킵 스캔(⑧)이 나타나지 않는다

## 값을 바꿔가며 확인할 것

- `ROW_COUNT`를 줄이면 어느 지점부터 옵티마이저가 인덱스를 포기하는지 볼 수 있다
- `STATUS_WEIGHTS`를 균등하게 바꾸면 ⑧ 스킵 스캔과 ⑨의 계획이 달라진다
- `conn.execute("ANALYZE")` 한 줄을 지우고 돌리면 통계의 영향을 직접 확인할 수 있다
