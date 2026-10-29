"""같은 비밀번호를 여러 알고리즘으로 해시해 초당 시도 횟수를 잰다.

공격자가 유출된 해시 목록을 들고 무차별 대입을 할 때, 1초에 몇 번 시도할 수 있는지가
그대로 비밀번호의 수명이 된다. 그 숫자를 알고리즘별로 직접 재 본다.
"""

from __future__ import annotations

import hashlib
import platform
import secrets
import time
from importlib.metadata import version

import argon2
import bcrypt

PASSWORD = b"correct-horse-battery-staple"
SALT_BYTES = 16

# 측정 시간이 한 자릿수 초에 들어오도록 알고리즘마다 반복 횟수를 달리 잡는다.
# 빠른 알고리즘을 1회만 재면 타이머 분해능에 묻힌다.
FAST_ROUNDS = 200_000
SLOW_ROUNDS = 20


def measure(label: str, rounds: int, run) -> tuple[str, int, float, float]:
    started = time.perf_counter()
    for _ in range(rounds):
        run()
    elapsed = time.perf_counter() - started
    return label, rounds, elapsed, rounds / elapsed


def main() -> None:
    salt = secrets.token_bytes(SALT_BYTES)
    bcrypt_salts = {cost: bcrypt.gensalt(rounds=cost) for cost in (8, 10, 12)}
    # argon2 기본 파라미터는 라이브러리가 정한 값을 그대로 쓴다. 손으로 낮추지 않는다.
    argon_default = argon2.PasswordHasher()
    argon_light = argon2.PasswordHasher(time_cost=1, memory_cost=8 * 1024, parallelism=1)

    print("=" * 72)
    print("환경")
    print("=" * 72)
    print(f"  Python        {platform.python_version()}")
    print(f"  OS            {platform.system()} {platform.release()}")
    print(f"  bcrypt        {version('bcrypt')}")
    print(f"  argon2-cffi   {version('argon2-cffi')}")
    print(f"  hashlib       OpenSSL 기반 ({len(hashlib.algorithms_guaranteed)}종 보장)")
    print(f"  비밀번호      {PASSWORD.decode()!r} ({len(PASSWORD)}바이트)")
    print(f"  솔트          {SALT_BYTES}바이트 무작위")
    print()

    print("argon2-cffi 기본 파라미터")
    print(f"  time_cost     {argon_default.time_cost}")
    print(f"  memory_cost   {argon_default.memory_cost} KiB")
    print(f"  parallelism   {argon_default.parallelism}")
    print(f"  hash_len      {argon_default.hash_len} 바이트")
    print()

    cases = [
        ("SHA-256 (솔트 없음)", FAST_ROUNDS,
         lambda: hashlib.sha256(PASSWORD).digest()),
        ("SHA-256 + 솔트", FAST_ROUNDS,
         lambda: hashlib.sha256(salt + PASSWORD).digest()),
        ("PBKDF2-HMAC-SHA256 600k", SLOW_ROUNDS,
         lambda: hashlib.pbkdf2_hmac("sha256", PASSWORD, salt, 600_000)),
        ("bcrypt cost=8", SLOW_ROUNDS,
         lambda: bcrypt.hashpw(PASSWORD, bcrypt_salts[8])),
        ("bcrypt cost=10", SLOW_ROUNDS,
         lambda: bcrypt.hashpw(PASSWORD, bcrypt_salts[10])),
        ("bcrypt cost=12", SLOW_ROUNDS,
         lambda: bcrypt.hashpw(PASSWORD, bcrypt_salts[12])),
        ("argon2id 기본값", SLOW_ROUNDS,
         lambda: argon_default.hash(PASSWORD)),
        ("argon2id 8MiB·1회", SLOW_ROUNDS,
         lambda: argon_light.hash(PASSWORD)),
    ]

    results = [measure(label, rounds, run) for label, rounds, run in cases]
    baseline = results[0][3]  # SHA-256 의 초당 횟수

    print("=" * 72)
    print("해시 1회 비용과 초당 시도 횟수")
    print("=" * 72)
    print(f"  {'알고리즘':<26}{'측정 횟수':>10}{'총 초':>9}"
          f"{'1회 마이크로초':>14}{'초당 횟수':>14}")
    print("  " + "-" * 72)
    for label, rounds, elapsed, per_sec in results:
        pad = 26 - sum(2 if "가" <= ch <= "힣" else 1 for ch in label)
        print(f"  {label}{' ' * max(0, pad)}{rounds:>10,}{elapsed:>9.3f}"
              f"{elapsed / rounds * 1_000_000:>14,.1f}{per_sec:>14,.0f}")
    print()

    print("=" * 72)
    print("SHA-256 대비 몇 배 느린가")
    print("=" * 72)
    for label, _rounds, _elapsed, per_sec in results[1:]:
        pad = 26 - sum(2 if "가" <= ch <= "힣" else 1 for ch in label)
        ratio = baseline / per_sec
        shown = f"{ratio:,.1f}" if ratio < 100 else f"{ratio:,.0f}"
        print(f"  {label}{' ' * max(0, pad)}{shown:>12}배")
    print()

    # 저장되는 해시 문자열의 모양도 보인다. 파라미터가 해시 안에 들어 있다는 것이
    # 왜 중요한지는 본문에서 다룬다.
    print("=" * 72)
    print("저장되는 해시 문자열")
    print("=" * 72)
    print(f"  bcrypt    {bcrypt.hashpw(PASSWORD, bcrypt_salts[12]).decode()}")
    print(f"  argon2id  {argon_default.hash(PASSWORD)}")
    print()


if __name__ == "__main__":
    main()
