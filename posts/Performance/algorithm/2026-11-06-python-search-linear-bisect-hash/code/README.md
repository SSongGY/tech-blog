# 예제 코드 — 파이썬 탐색 방식별 조회 시간

표준 라이브러리만 쓴다. `list in`(선형), `bisect`(이진), `set`·`dict`(해시)의 조회 시간을 크기별로 재고, 해시 값이 전부 같은 키로 dict 를 채울 때 삽입 시간이 어떻게 늘어나는지 본다.

## 실행

```bash
python search_bench.py
```

약 20초 걸린다.

## 파일

| 파일 | 무엇 |
|---|---|
| `search_bench.py` | 측정 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `SIZES` — 원소 수. 10배씩 늘렸을 때 각 열이 몇 배가 되는지 본다
- `SameHash.__hash__` — 상수 대신 `hash(self.number)` 를 돌려주면 충돌이 사라지는지 본다
- 측정 시간은 환경에 따라 다르다. 절대값이 아니라 크기가 늘 때의 배율을 비교한다
