# 예제 코드 — sorted 와 heapq.nsmallest 의 손익분기

표준 라이브러리만 쓴다. 난수 시드를 고정한 20만 개 정수에서 k 를 바꿔 가며 `sorted(data)[:k]` 와 `heapq.nsmallest(k, data)` 의 시간을 잰다. 각 값은 5번 중 가장 빠른 것이다.

## 실행

```bash
python topk_bench.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `topk_bench.py` | 본문 표를 만드는 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `compare(200_000, ...)` 의 크기 — 줄이면 손익분기가 같은 k/n 비율에 머무는지 본다
- `key` 람다 — 더 무거운 함수로 바꾸면 두 방식의 간격이 어떻게 변하는지 본다
- 시간은 기계에 따라 다르다. 같은 구조(작은 k 에서 nsmallest 우세, 큰 k 에서 sorted 우세)가 나오는지를 본다
