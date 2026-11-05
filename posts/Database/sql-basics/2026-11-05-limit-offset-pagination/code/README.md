# 예제 코드 — LIMIT/OFFSET 으로 쪽 넘기기

표준 라이브러리만 쓴다. 12행짜리 표로 동률·삽입 문제를, 20만 행짜리 표로 OFFSET 비용을 확인한다.

## 실행

```bash
python limit_offset.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `limit_offset.py` | 본문 출력을 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `BIG_ROW_COUNT` — 줄이면 OFFSET 방식과 키셋 방식의 시간 차가 줄어든다
- `PAGE_SIZE` — 쪽 크기. 동률 묶음보다 작으면 쪽 경계가 동률 한가운데에 걸린다
