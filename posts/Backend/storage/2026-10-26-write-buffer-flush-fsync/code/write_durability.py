"""write / flush / fsync 가 각각 어디까지 보장하는지를 시간과 생존 여부로 가른다.

  write  -> 프로세스 안 버퍼까지
  flush  -> 운영체제까지 (프로세스가 죽어도 남는다)
  fsync  -> 저장 장치까지 (전원이 끊겨도 남는다고 문서가 말한다)

앞의 둘은 여기서 직접 확인한다. 셋째는 전원을 끊어야 하므로 문서 근거만 쓴다.
"""

from __future__ import annotations

import io
import os
import platform
import subprocess
import sys
import tempfile
import time

LINES = 10_000
PAYLOAD = "2026-10-26 10:00:00 INFO  주문이 접수되었다 order_id=%06d\n"
CHILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_child.py")


def write_lines(path: str, mode: str) -> float:
    """mode 에 따라 flush/fsync 를 끼워 넣고 걸린 시간을 돌려준다."""
    start = time.perf_counter()
    with open(path, "w", encoding="utf-8") as handle:
        for i in range(LINES):
            handle.write(PAYLOAD % i)
            if mode in ("flush", "fsync"):
                handle.flush()
            if mode == "fsync":
                os.fsync(handle.fileno())
        if mode == "fsync-once":
            handle.flush()
            os.fsync(handle.fileno())
    return time.perf_counter() - start


def visible_bytes(path: str) -> int:
    """다른 핸들로 열어 지금 읽히는 바이트 수. 버퍼에만 있으면 0 이다."""
    with open(path, "rb") as reader:
        return len(reader.read())


def section(title: str) -> None:
    print()
    print(title)


def main() -> None:
    workdir = tempfile.mkdtemp(prefix="fsync_demo_")

    section("환경")
    print(f"  Python                {platform.python_version()}")
    print(f"  OS                    {platform.system()} {platform.release()}")
    print(f"  기본 버퍼 크기        io.DEFAULT_BUFFER_SIZE = {io.DEFAULT_BUFFER_SIZE:,} 바이트")
    print(f"  한 줄 길이            {len(PAYLOAD % 0):,} 바이트 (UTF-8 로는 더 길다)")
    print(f"  쓸 줄 수              {LINES:,}")

    section("1. write 직후 파일에는 무엇이 있는가")
    probe = os.path.join(workdir, "probe.log")
    with open(probe, "w", encoding="utf-8") as handle:
        handle.write(PAYLOAD % 0)
        print(f"  write 한 줄 직후      다른 핸들로 읽히는 바이트 {visible_bytes(probe):>8,}")
        handle.flush()
        print(f"  flush 한 뒤           다른 핸들로 읽히는 바이트 {visible_bytes(probe):>8,}")
        for i in range(LINES):
            handle.write(PAYLOAD % i)
        seen = visible_bytes(probe)
        print(f"  {LINES:,}줄을 더 쓴 뒤    다른 핸들로 읽히는 바이트 {seen:>8,}")
        print("  버퍼가 가득 차면 쓰라고 하지 않아도 넘어간다. 경계는 내가 정하지 않는다.")

    section("2. 같은 10,000줄을 네 가지로 쓰며 시간을 잰다")
    results = {}
    for mode, label in (
        ("buffer", "버퍼만 — 닫을 때 한 번"),
        ("fsync-once", "마지막에 fsync 한 번"),
        ("flush", "줄마다 flush"),
        ("fsync", "줄마다 flush + fsync"),
    ):
        path = os.path.join(workdir, f"{mode}.log")
        elapsed = write_lines(path, mode)
        results[mode] = elapsed
        size = os.path.getsize(path)
        print(f"  {label:24} {elapsed:8.3f}초   파일 {size:,} 바이트")

    base = results["buffer"]
    print()
    print(f"  {'버퍼만 대비':24} {'배수':>8}")
    for mode, label in (
        ("fsync-once", "마지막에 fsync 한 번"),
        ("flush", "줄마다 flush"),
        ("fsync", "줄마다 flush + fsync"),
    ):
        print(f"  {label:24} {results[mode] / base:7.1f}배")

    section("3. 프로세스가 죽으면 버퍼는 같이 사라진다")
    print("  자식 프로세스가 500줄을 쓰고 close 없이 os._exit(1) 로 즉사한다.")
    for arg, label in (("noflush", "flush 없이"), ("flush", "줄마다 flush")):
        path = os.path.join(workdir, f"crash_{arg}.log")
        proc = subprocess.run([sys.executable, CHILD, path, arg])
        size = os.path.getsize(path) if os.path.exists(path) else 0
        with open(path, "r", encoding="utf-8") as reader:
            kept = sum(1 for _ in reader)
        print(f"  {label:12} 종료코드 {proc.returncode}  남은 바이트 {size:>7,}  남은 줄 {kept:>4} / 500")

    section("4. fsync 를 모아서 부르면 얼마나 싸지는가")
    for batch in (1, 10, 100, 1000):
        path = os.path.join(workdir, f"batch_{batch}.log")
        start = time.perf_counter()
        with open(path, "w", encoding="utf-8") as handle:
            for i in range(LINES):
                handle.write(PAYLOAD % i)
                if (i + 1) % batch == 0:
                    handle.flush()
                    os.fsync(handle.fileno())
            handle.flush()
            os.fsync(handle.fileno())
        elapsed = time.perf_counter() - start
        calls = -(-LINES // batch) + 1
        print(f"  {batch:>4}줄마다 fsync   호출 {calls:>6,}회   {elapsed:7.3f}초")

    print()
    print(f"작업 폴더: {workdir}")


if __name__ == "__main__":
    main()
