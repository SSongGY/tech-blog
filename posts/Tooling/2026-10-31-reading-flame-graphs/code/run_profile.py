"""workload 를 표본 수집기 아래에서 돌리고, 접힌 스택과 플레임 그래프를 낸다.

출력 순서를 숫자 → 그림으로 잡았다. 접힌 스택과 자기 시간/포함 시간 표를 먼저
보고 나면, 그 아래 그림에서 어느 칸이 왜 그 폭인지가 따라 읽힌다.
"""

from __future__ import annotations

import platform
import sys
import threading
import time
from pathlib import Path

import flamekit
import workload

FIG_PATH = Path(__file__).resolve().parent.parent / "fig" / "sample-flame.svg"
INTERVAL = 0.001
# GIL 은 기본 5ms 마다 한 번만 다른 스레드로 넘어간다. 그대로 두면 수집기가
# 깨어나도 GIL 을 못 잡아 실제 주기가 16ms 까지 벌어졌다. 전환 간격을 줄여야
# 요청한 1ms 에 가까워진다. 측정 대상이 그만큼 느려지는 것은 감수한다.
SWITCH_INTERVAL = 0.0002


def print_environment() -> None:
    print("=" * 64)
    print("환경")
    print("=" * 64)
    print(f"  Python   {platform.python_version()}")
    print(f"  OS       {platform.system()} {platform.release()}")
    print(f"  표본 주기 {INTERVAL * 1000:.0f}ms 요청 (sys._current_frames 기반)")
    print(f"  GIL 전환 {SWITCH_INTERVAL * 1000:.1f}ms (sys.setswitchinterval)")
    print()


def compress(line: str) -> str:
    """같은 프레임이 3번 넘게 이어지면 'walk*25' 로 줄인다. 재귀 스택을 읽으려고."""
    out: list[str] = []
    for name in line.split(";"):
        if out and out[-1][0] == name:
            out[-1][1] += 1
        else:
            out.append([name, 1])
    return ";".join(n if c < 3 else f"{n}*{c}" for n, c in out)


def print_folded(folded: list[tuple[str, int]], total: int) -> None:
    print("=" * 64)
    print("접힌 스택 (collapsed stack) — 그림이 되기 직전의 중간 산출물")
    print("=" * 64)
    print("  재귀로 같은 프레임이 이어지는 자리는 '이름*횟수' 로 줄여 적었다.")
    for line, hits in sorted(folded, key=lambda item: -item[1]):
        print(f"  {hits:5d}  {hits / total * 100:5.1f}%  {compress(line)}")
    print(f"  {'-' * 56}")
    print(f"  {total:5d}  100.0%  합계")
    print()


def print_time_table(folded: list[tuple[str, int]], total: int) -> None:
    inclusive = flamekit.inclusive_counts(folded)
    own = flamekit.self_counts(folded)
    print("=" * 64)
    print("포함 시간과 자기 시간 — 플레임 그래프에서 폭과 윗면이 갈리는 지점")
    print("=" * 64)
    print(f"  {'함수':<18}{'포함 표본':>10}{'포함 %':>9}{'자기 표본':>10}{'자기 %':>9}")
    print(f"  {'-' * 54}")
    for name, hits in inclusive.most_common():
        print(
            f"  {name:<18}{hits:>10}{hits / total * 100:>8.1f}%"
            f"{own.get(name, 0):>10}{own.get(name, 0) / total * 100:>8.1f}%"
        )
    print()


def print_depth_table(folded: list[tuple[str, int]], total: int) -> None:
    print("=" * 64)
    print("스택 깊이별 표본 — 높이와 비용은 따로 논다")
    print("=" * 64)
    print(f"  {'깊이':>4}{'표본':>8}{'비율':>9}  맨 위 프레임")
    print(f"  {'-' * 54}")
    rows = sorted(folded, key=lambda item: len(item[0].split(";")))
    for line, hits in rows:
        frames = line.split(";")
        print(
            f"  {len(frames):>4}{hits:>8}{hits / total * 100:>8.1f}%  {frames[-1]}"
        )
    print()
    print("  가장 깊은 스택이 가장 비싼 스택이 아니다. 위 두 열을 나란히 본다.")
    print()


def burn(seconds: float) -> int:
    """정해진 시간 동안 CPU 를 쓴다. 표본 수집 주기를 재는 데만 쓴다."""
    end = time.perf_counter() + seconds
    total = 0
    while time.perf_counter() < end:
        for i in range(10_000):
            total = (total * 31 + i) % 1_000_003
    return total


def print_sample_rate() -> None:
    """GIL 전환 간격을 바꿔 가며 실제 표본 주기를 잰다.

    요청한 주기가 그대로 나오지 않는다. 수집기가 깨어나도 작업 스레드가 GIL 을
    쥐고 있으면 실행이 안 되기 때문이다. 그림을 믿기 전에 이걸 먼저 본다.
    """
    print("=" * 64)
    print("요청한 표본 주기 vs 실제로 집힌 주기")
    print("=" * 64)
    print(f"  {'GIL 전환 간격':<16}{'표본':>8}{'측정 시간':>10}  실제 주기")
    print(f"  {'-' * 54}")
    for switch in (0.005, 0.001, 0.0002):
        sys.setswitchinterval(switch)
        probe = flamekit.StackSampler(threading.get_ident(), INTERVAL)
        started = time.perf_counter()
        probe.start()
        burn(1.0)
        elapsed = time.perf_counter() - started
        probe.stop()
        hits = sum(probe.counts.values())
        note = " (기본값)" if switch == 0.005 else ""
        print(
            f"  {switch * 1000:>6.1f}ms{note:<9}{hits:>8}{elapsed:>9.2f}초"
            f"  {elapsed / max(hits, 1) * 1000:>6.1f}ms"
        )
    print(f"\n  요청 주기는 셋 다 {INTERVAL * 1000:.0f}ms 로 같다. 달라진 것은 GIL 전환 간격뿐이다.\n")


def main() -> int:
    print_environment()
    print_sample_rate()

    sys.setswitchinterval(SWITCH_INTERVAL)
    sampler = flamekit.StackSampler(threading.get_ident(), INTERVAL)
    started = time.perf_counter()
    sampler.start()
    workload.pipeline()
    elapsed = time.perf_counter() - started
    sampler.stop()

    total_samples = sum(sampler.counts.values())
    folded, dropped = flamekit.fold(sampler.counts, root="pipeline")
    total = sum(hits for _, hits in folded)
    print(f"  실행 시간 {elapsed:.2f}초 · 표본 {total_samples}개 "
          f"(평균 {elapsed / max(total_samples, 1) * 1000:.1f}ms 간격)")
    print(f"  측정 대상 밖이라 버린 표본 {dropped}개 · 그림에 쓰는 표본 {total}개\n")

    print_folded(folded, total)
    print_time_table(folded, total)
    print_depth_table(folded, total)

    tree = flamekit.build_tree(folded)
    svg = flamekit.render(
        tree,
        "workload.pipeline() 의 CPU 플레임 그래프",
        f"표본 {total}개 · 가로폭 = 그 스택이 표본에서 차지한 비율 · "
        f"형제 칸은 이름순 (시간순이 아니다)",
        total,
    )
    FIG_PATH.write_text(svg, encoding="utf-8")
    print(f"  플레임 그래프를 {FIG_PATH.name} 로 저장했다 ({len(svg)}바이트)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
