"""async/await 가 만들어 내는 상태 머신을 이벤트 루프 없이 손으로 돌려 본다.

python state_machine_demo.py
"""

import asyncio
import dis
import inspect
import sys


def banner(title):
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# --------------------------------------------------------------------------
async def one_await(n):
    value = await never_suspends(n)
    return value + 1


async def never_suspends(n):
    return n * 10


async def two_awaits(n):
    a = await never_suspends(n)
    b = await never_suspends(n + 1)
    return a + b


async def really_suspends():
    first = "지역 변수는 중단 중에도 살아 있다"
    await asyncio.sleep(0)
    return first


# --------------------------------------------------------------------------
def drive(coro, label):
    """이벤트 루프 없이 send(None) 만으로 코루틴을 끝까지 민다."""
    sent = 0
    while True:
        try:
            yielded = coro.send(None)
        except StopIteration as stop:
            print(f"  {label}: send {sent + 1}회 만에 종료, 반환값 {stop.value!r}")
            return stop.value
        sent += 1
        print(f"  {label}: {sent}번째 중단 — 바깥으로 넘긴 값 {yielded!r}")


def main():
    print("Python", sys.version.split()[0])

    banner("1. async 함수를 호출하면 몸통이 아니라 객체가 나온다")
    ran = []

    async def side_effect():
        ran.append("몸통 실행됨")
        return 1

    obj = side_effect()
    print("  호출 결과 :", type(obj).__name__)
    print("  상태      :", inspect.getcoroutinestate(obj))
    print("  몸통이 돌았나:", ran or "아니오 — 한 줄도 돌지 않았다")
    obj.close()

    banner("2. await 한 개가 컴파일된 모양")
    dis.dis(one_await)

    banner("3. await 가 둘인데 중단은 몇 번 일어나는가")
    drive(two_awaits(1), "two_awaits")
    print("  → await 를 두 번 적었는데 중단은 0회다.")

    banner("4. 진짜로 중단되는 await")
    coro = really_suspends()
    print("  생성 직후 :", inspect.getcoroutinestate(coro))
    yielded = coro.send(None)
    print("  첫 send 후:", inspect.getcoroutinestate(coro))
    print("  바깥으로 넘긴 값 :", repr(yielded))
    print("  무엇을 기다리는가:", type(coro.cr_await).__name__,
          getattr(coro.cr_await, "__qualname__", ""))
    frame = coro.cr_frame
    print("  멈춘 코드 :", frame.f_code.co_name, "/ 줄", frame.f_lineno)
    print("  살아 있는 지역 변수:", {k: v for k, v in frame.f_locals.items()})
    try:
        coro.send(None)
    except StopIteration as stop:
        print("  두 번째 send 로 종료, 반환값:", repr(stop.value))
    print("  최종 상태 :", inspect.getcoroutinestate(coro))

    banner("5. 같은 일을 제너레이터로 손으로 쓰면")

    def hand_written(n):
        """await 가 사라진 자리에 yield 가 그대로 들어간다."""
        a = n * 10
        yield "여기서 멈춘다"      # await 지점
        return a + 1

    gen = hand_written(1)
    print("  첫 next   :", next(gen))
    try:
        next(gen)
    except StopIteration as stop:
        print("  두 번째 next 로 종료, 반환값:", repr(stop.value))

    banner("6. 중단 지점이 없으면 동시성도 없다")

    async def busy(name, log):
        for step in range(3):
            log.append(f"{name}{step}")
        return name

    async def polite(name, log):
        for step in range(3):
            log.append(f"{name}{step}")
            await asyncio.sleep(0)       # 여기서 루프에 차례를 넘긴다
        return name

    async def race(worker):
        log = []
        await asyncio.gather(worker("A", log), worker("B", log))
        return log

    print("  await 없음 :", asyncio.run(race(busy)))
    print("  await 있음 :", asyncio.run(race(polite)))


if __name__ == "__main__":
    main()
