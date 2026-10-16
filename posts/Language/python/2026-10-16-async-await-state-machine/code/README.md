# async/await 상태 머신 예제

코루틴 객체를 이벤트 루프 없이 `send(None)` 으로 직접 밀어 본다. `await` 가
어떤 바이트코드가 되는지, 중단이 실제로 몇 번 일어나는지, 중단된 프레임에
무엇이 남아 있는지를 확인한다. 표준 라이브러리만 쓴다.

## 실행

```bash
python state_machine_demo.py
```

## 바꿔 볼 값

- `never_suspends()` 안의 `return n * 10` 을 `await asyncio.sleep(0)` 다음에 두면,
  3번 절의 중단 횟수가 0에서 2로 바뀐다. **`await` 를 적은 횟수가 아니라
  대상이 실제로 중단하느냐가 횟수를 정한다**는 점이 바로 보인다.
- 6번 절 `polite()` 의 `await asyncio.sleep(0)` 을 지우면 `busy()` 와 같은
  순서가 나온다. `asyncio.gather` 는 차례를 넘길 지점이 있어야 끼어든다.
- 2번 절의 `dis.dis(one_await)` 를 `dis.dis(two_awaits)` 로 바꾸면
  `SEND`/`YIELD_VALUE` 묶음이 두 벌 나온다.

바이트코드 모양은 파이썬 판마다 달라진다. 이 출력은 3.13.5 기준이다.
`probe_dis.py` 는 규칙을 확인하려고 찔러 본 쪽이라 예제에 싣지 않았다.
