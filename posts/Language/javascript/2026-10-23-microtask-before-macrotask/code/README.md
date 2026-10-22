# 예제 코드 — 자바스크립트 이벤트 루프에서 마이크로태스크가 먼저인 이유

출력 순서 퀴즈 다섯 개를 차례로 돌린다. 외부 의존성은 없고 Node.js 내장 모듈만 쓴다.

## 실행

```bash
node event-loop-order.js
```

## 파일

| 파일 | 무엇 |
|---|---|
| `event-loop-order.js` | 퀴즈 다섯 개. 본문의 출력은 전부 여기서 나온다 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- `RACE_ROUNDS` — `setTimeout(0)` 과 `setImmediate` 의 경주 횟수. 메인 모듈 쪽은 돌릴
  때마다 집계가 달라지고, I/O 콜백 안쪽은 몇 번을 돌려도 한쪽으로만 나온다.
- 5번 `quizStarvation` 의 `LIMIT` — 마이크로태스크 반복 횟수. 늘릴수록 0ms 타이머가
  더 오래 밀린다.
- 3번 `quizAwaitOrder` 의 `await inner()` 를 `inner()` 로 바꾸면 — `outer` 의 다음 줄이
  마이크로태스크로 미뤄지지 않고 그 자리에서 이어진다.
