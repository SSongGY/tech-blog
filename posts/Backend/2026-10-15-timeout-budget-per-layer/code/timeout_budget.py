"""계층마다 같은 타임아웃을 주면 무슨 일이 생기는지 실제로 재어 본다.

재는 것은 넷이다.
1) 바닥(DB)까지 내려간 호출이 몇 번인가
2) 클라이언트가 얼마 만에 손을 떼는가
3) 클라이언트가 손을 뗀 뒤에도 서버 쪽에서 몇 초를 더 돌았는가 (= 버려진 일)
4) 클라이언트가 받은 것이 '타임아웃'인가 '서버가 돌려준 실패'인가

(3)은 로그만 봐서는 안 보인다. 클라이언트 로그에는 타임아웃 한 줄이 남고
서버는 아무 일 없이 계속 돌기 때문이다. 그래서 서버 쪽 작업을 스레드로 띄워
끝까지 기다렸다가, 클라이언트가 포기한 시각과의 차이를 그대로 찍는다.
"""

from __future__ import annotations

import platform
import threading
import time
from concurrent.futures import ThreadPoolExecutor

RULE = "=" * 70

CLIENT_BUDGET_MS = 1000   # 사용자가 기다려 주는 시간
SAFETY_MARGIN_MS = 30     # 응답을 돌려보낼 시간. 예산 전부를 쓰지 않는다
LAYER_OVERHEAD_MS = 20    # 각 계층이 직렬화·큐 대기 등으로 쓰는 몫
DB_STALL_MS = 5000        # 막힌 의존성. 이만큼 지나야 응답이 온다
DB_HEALTHY_MS = 400       # 평소에 걸리는 시간
API_RETRIES = 2
SERVICE_RETRIES = 3
ATTEMPT_MS = 500          # 한 번 시도에 주는 시간 — 평소 400ms + 여유
MIN_ATTEMPT_MS = 100      # 이보다 적게 남으면 시도해 봐야 소용이 없다

db_calls = 0
db_lock = threading.Lock()


class LayerTimeout(Exception):
    """그 계층이 기다리기로 한 시간을 넘겼다."""


def reset_counter() -> None:
    global db_calls
    with db_lock:
        db_calls = 0


def resolve_latency(spec: int | list[int], call_index: int) -> int:
    """응답 시간을 호출 순서별로 다르게 줄 수 있게 한다 (일시적 지연을 흉내 낸다)."""
    if isinstance(spec, list):
        return spec[min(call_index, len(spec) - 1)]
    return spec


def fake_db(timeout_ms: int, latency_spec: int | list[int]) -> str:
    """읽기 타임아웃이 걸린 소켓과 같은 모양으로 움직인다.

    응답이 늦으면 타임아웃만큼만 기다리다 끊는다. 끊어도 상대편 작업이
    멈추는 것은 아니지만, 여기서 재는 것은 이쪽이 쓴 시간이다.
    """
    global db_calls
    with db_lock:
        db_calls += 1
        call_index = db_calls - 1
    latency_ms = resolve_latency(latency_spec, call_index)
    time.sleep(min(latency_ms, timeout_ms) / 1000)
    if latency_ms > timeout_ms:
        raise LayerTimeout(f"db read timeout after {timeout_ms}ms")
    return "row"


def call_with_retry(
    timeout_ms: int,
    retries: int,
    split_budget: bool,
    inner,
) -> str:
    """한 계층이 하는 일 — 자기 몫을 쓰고, 남은 것을 아래로 넘긴다.

    split_budget 이 False 면 '다들 같은 값으로 맞추자'는 흔한 설정이다.
    재시도를 몇 번 하든 매번 받은 타임아웃을 통째로 아래로 넘긴다.
    True 면 남은 예산을 시도 횟수로 나눠 넘긴다.
    """
    time.sleep(LAYER_OVERHEAD_MS / 1000)
    remaining_ms = timeout_ms - LAYER_OVERHEAD_MS
    per_attempt_ms = remaining_ms // retries if split_budget else timeout_ms
    last: Exception | None = None
    for _ in range(retries):
        try:
            return inner(per_attempt_ms)
        except LayerTimeout as exc:
            last = exc
    raise LayerTimeout(f"{retries}번 시도하고 포기") from last


def call_with_deadline(deadline: float, attempt_ms: int, inner) -> str:
    """남은 시간을 보고 한 번 더 시도할지 정한다.

    예산을 재시도 횟수로 미리 나누지 않는다. 한 번 시도에 줄 시간은 '평소 걸리는
    시간 + 여유'로 고정하고, 그만큼이 남아 있을 때만 다시 시도한다.
    """
    time.sleep(LAYER_OVERHEAD_MS / 1000)
    last: Exception | None = None
    while True:
        remaining_ms = int((deadline - time.monotonic()) * 1000)
        if remaining_ms < MIN_ATTEMPT_MS:
            break
        try:
            return inner(min(attempt_ms, remaining_ms))
        except LayerTimeout as exc:
            last = exc
    raise LayerTimeout("남은 예산이 없어 포기") from last


def server_call_with_deadline(
    budget_ms: int, attempt_ms: int, latency_ms: int | list[int]
) -> str:
    deadline = time.monotonic() + budget_ms / 1000

    def service(_unused: int) -> str:
        return call_with_deadline(
            deadline, attempt_ms, lambda ms: fake_db(ms, latency_ms)
        )

    # API 계층은 재시도하지 않고 같은 데드라인을 그대로 넘긴다
    return call_with_deadline(deadline, budget_ms, service)


def server_call(
    api_timeout_ms: int,
    api_retries: int,
    service_retries: int,
    split_budget: bool,
    latency_ms: int | list[int],
) -> str:
    def service(timeout_ms: int) -> str:
        return call_with_retry(
            timeout_ms,
            service_retries,
            split_budget,
            lambda ms: fake_db(ms, latency_ms),
        )

    return call_with_retry(api_timeout_ms, api_retries, split_budget, service)


def run_scenario(
    title: str,
    *,
    api_timeout_ms: int,
    api_retries: int,
    service_retries: int,
    split_budget: bool,
    latency_ms: int | list[int] = DB_STALL_MS,
    deadline_mode: bool = False,
) -> None:
    """서버 쪽을 스레드로 띄우고, 클라이언트는 자기 예산만큼만 기다린다."""
    reset_counter()
    print(f"[{title}]")
    if deadline_mode:
        print(
            f"  설정  예산 {api_timeout_ms}ms · 한 번 시도 {ATTEMPT_MS}ms "
            f"· DB 응답 {latency_ms}ms"
        )
    else:
        print(
            f"  설정  API 타임아웃 {api_timeout_ms}ms · 재시도 API {api_retries}회 "
            f"× 서비스 {service_retries}회 · DB 응답 {latency_ms}ms"
        )

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as pool:
        if deadline_mode:
            future = pool.submit(
                server_call_with_deadline, api_timeout_ms, ATTEMPT_MS, latency_ms
            )
        else:
            future = pool.submit(
                server_call,
                api_timeout_ms,
                api_retries,
                service_retries,
                split_budget,
                latency_ms,
            )
        try:
            future.result(timeout=CLIENT_BUDGET_MS / 1000)
            client_result = "성공 응답을 받았다"
        except TimeoutError:
            client_result = "기다리다 끊었다 (서버 응답 없음)"
        except LayerTimeout:
            client_result = "서버가 돌려준 실패 응답을 받았다"
        client_ms = (time.monotonic() - started) * 1000

        # 서버 쪽 작업이 실제로 끝날 때까지 기다려 본다. 운영에서는 아무도
        # 기다리지 않으므로 이 구간이 통째로 버려지는 일이다.
        try:
            future.result()
        except LayerTimeout:
            pass
        server_ms = (time.monotonic() - started) * 1000

    print(f"  클라이언트  {client_ms:6.0f}ms — {client_result}")
    print(f"  서버 작업   {server_ms:6.0f}ms 에 끝났다")
    print(f"  버려진 일   {server_ms - client_ms:6.0f}ms")
    print(f"  DB 호출     {db_calls}회")
    print()


def print_budget_table(layers: list[tuple[str, int]], start_ms: int) -> None:
    """예산이 아래로 내려가며 어떻게 쪼개지는지 계산해 찍는다."""
    header = (
        f"  {'계층':8s} {'받은 예산':>10s} {'오버헤드':>9s} "
        f"{'남은 예산':>10s} {'재시도':>7s} {'한 번 시도':>11s}"
    )
    print(header)
    print("  " + "-" * 62)
    budget_ms = start_ms
    for name, retries in layers:
        remaining_ms = budget_ms - LAYER_OVERHEAD_MS
        per_attempt_ms = remaining_ms // retries
        print(
            f"  {name:8s} {budget_ms:8d}ms {LAYER_OVERHEAD_MS:7d}ms "
            f"{remaining_ms:8d}ms {retries:6d}회 {per_attempt_ms:9d}ms"
        )
        budget_ms = per_attempt_ms
    print(f"  {'DB':8s} {budget_ms:8d}ms 안에 답해야 한다")
    print()


def main() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python  {platform.python_version()}")
    print(f"  OS      {platform.system()} {platform.release()}")
    print(f"  사용자가 기다려 주는 시간      {CLIENT_BUDGET_MS}ms")
    print(f"  막힌 의존성의 응답 시간        {DB_STALL_MS}ms")
    print(f"  평소 의존성의 응답 시간        {DB_HEALTHY_MS}ms")
    print(f"  계층 하나가 쓰는 오버헤드      {LAYER_OVERHEAD_MS}ms")
    print(f"  응답을 돌려보낼 여유           {SAFETY_MARGIN_MS}ms")
    print()

    print(RULE)
    print("1. 계층마다 같은 타임아웃을 준 경우 — 의존성이 막혔을 때")
    print(RULE)
    run_scenario(
        "API·서비스 모두 1000ms, 재시도 2회 × 3회",
        api_timeout_ms=CLIENT_BUDGET_MS,
        api_retries=API_RETRIES,
        service_retries=SERVICE_RETRIES,
        split_budget=False,
    )
    run_scenario(
        "같은 설정에서 재시도를 서비스 한 곳으로 모으면",
        api_timeout_ms=CLIENT_BUDGET_MS,
        api_retries=1,
        service_retries=SERVICE_RETRIES,
        split_budget=False,
    )

    print(RULE)
    print("2. 예산을 쪼개 내려보낸 경우 — 재시도는 서비스 한 곳")
    print(RULE)
    print_budget_table([("API", 1), ("서비스", SERVICE_RETRIES)],
                       CLIENT_BUDGET_MS - SAFETY_MARGIN_MS)
    run_scenario(
        "API 970ms 로 시작해 아래로 쪼갠다",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=SERVICE_RETRIES,
        split_budget=True,
    )

    print(RULE)
    print("3. 예산은 쪼개되 재시도를 양쪽에서 하는 경우")
    print(RULE)
    print_budget_table([("API", API_RETRIES), ("서비스", SERVICE_RETRIES)],
                       CLIENT_BUDGET_MS - SAFETY_MARGIN_MS)
    run_scenario(
        "의존성이 막혔을 때",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=API_RETRIES,
        service_retries=SERVICE_RETRIES,
        split_budget=True,
    )
    run_scenario(
        "의존성이 멀쩡할 때 (400ms 면 답이 온다)",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=API_RETRIES,
        service_retries=SERVICE_RETRIES,
        split_budget=True,
        latency_ms=DB_HEALTHY_MS,
    )
    run_scenario(
        "같은 상황에서 재시도를 서비스 한 곳으로 모으면",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=SERVICE_RETRIES,
        split_budget=True,
        latency_ms=DB_HEALTHY_MS,
    )

    print(RULE)
    print("4. 데드라인을 넘기고, 한 번 시도의 예산은 고정하는 경우")
    print(RULE)
    print("  재시도 횟수로 예산을 미리 나누지 않는다. 한 번 시도에 주는 시간은")
    print(f"  평소 걸리는 {DB_HEALTHY_MS}ms 에 여유를 더한 {ATTEMPT_MS}ms 로 고정하고,")
    print("  그만큼이 남아 있을 때만 다시 시도한다.")
    print()
    run_scenario(
        "의존성이 막혔을 때",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=1,
        split_budget=True,
        latency_ms=DB_STALL_MS,
        deadline_mode=True,
    )
    run_scenario(
        "의존성이 멀쩡할 때 (400ms 면 답이 온다)",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=1,
        split_budget=True,
        latency_ms=DB_HEALTHY_MS,
        deadline_mode=True,
    )
    run_scenario(
        "첫 호출만 막히고 다음부터 정상일 때",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=1,
        split_budget=True,
        latency_ms=[DB_STALL_MS, DB_HEALTHY_MS],
        deadline_mode=True,
    )
    run_scenario(
        "같은 상황을 예산 나누기로 처리하면",
        api_timeout_ms=CLIENT_BUDGET_MS - SAFETY_MARGIN_MS,
        api_retries=1,
        service_retries=SERVICE_RETRIES,
        split_budget=True,
        latency_ms=[DB_STALL_MS, DB_HEALTHY_MS],
    )


if __name__ == "__main__":
    main()
