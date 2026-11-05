# 예제 코드 — INSTEAD OF 트리거

표준 라이브러리만 쓴다. 회원(`member`)과 지갑(`wallet`)을 조인한 뷰 `member_wallet` 에 INSERT·UPDATE·DELETE 를 걸어 보고, 트리거 유무와 종류에 따라 무엇이 달라지는지 확인한다.

## 실행

```bash
python instead_of_demo.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `instead_of_demo.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- 4번의 `balance < 600` — 조건을 넓히면 `audit_log` 에 쌓이는 행이 같이 늘어나는지 본다
- `INSTEAD_OF_TRIGGERS` 에서 `audit_log` 줄을 지우면 부수 효과 없이 두 표만 바뀐다
