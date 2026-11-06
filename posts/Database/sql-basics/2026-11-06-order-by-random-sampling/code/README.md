# 예제 코드 — 무작위로 N행 뽑기

표준 라이브러리만 쓴다. 10행짜리 표로 결과 모양을, 큰 표로 비용과 치우침을 확인한다.

## 실행

```bash
python random_sampling.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `random_sampling.py` | 본문 출력을 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `BIG_ROW_COUNT` — 줄이면 두 방법의 시간 차가 줄어든다
- `section_rowid_bias()` 의 삭제 범위 — 빈 구간을 넓히면 그 뒤 첫 행이 뽑히는 비율이 커진다
- `SEED` — 3)·4)에서 파이썬이 만드는 목표 id 를 정한다. SQLite 의 `random()` 은 시드를 줄 수 없다

1)의 결과는 실행할 때마다 다르다. 나머지는 시드가 고정돼 같은 값이 나온다(시간 제외).
