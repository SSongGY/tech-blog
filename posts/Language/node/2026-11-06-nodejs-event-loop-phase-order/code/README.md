# 예제 코드 — Node.js 이벤트 루프 단계

Node.js 만 있으면 돈다. 외부 패키지가 없다.

## 실행

```bash
node event-loop-order.js
```

## 파일

| 파일 | 무엇 |
|---|---|
| `event-loop-order.js` | 네 가지 상황의 실행 순서를 찍는다. 마지막에 아래 파일을 불러 5번을 찍는다 |
| `timeout-vs-immediate-repeat.js` | 메인 모듈에서 `setTimeout 0` 과 `setImmediate` 의 순서를 자식 프로세스 30개로 센다 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `RUNS` — 반복 횟수를 늘리면 어느 쪽이 먼저 오는 비율이 더 안정적으로 보인다
- `MAX_TICKS` — `nextTick` 연쇄 길이. 이 횟수가 끝나야 `setImmediate` 가 돈다
