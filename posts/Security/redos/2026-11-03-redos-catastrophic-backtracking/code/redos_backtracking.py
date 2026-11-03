"""정규식 백트래킹 폭발(ReDoS)을 재현하고, 무엇이 실제로 막는지 잰다.

Python 3.13.5 의 표준 re 모듈로 돌렸다. 7절만 선택 의존성 regex 를 쓴다
(없으면 그 절은 건너뛴다). 측정 시간은 환경에 따라 흔들리지만, 길이가 하나
늘 때 시간이 몇 배가 되는지(비율)는 같은 모양으로 나온다.
"""

import re
import sys
import threading
import time

EXP_LIMIT = 2.0        # 한 측정이 이 초를 넘으면 그 식은 더 늘리지 않는다
EXPONENTIAL_START = 18  # 지수 폭발 식의 시작 길이
EXPONENTIAL_STEPS = 10  # 길이를 하나씩 늘리는 횟수


def elapsed(pattern: str, text: str, flags: int = 0) -> tuple[float, bool]:
    """컴파일 시간은 빼고 매칭 시간만 잰다. 캐시에 걸리지 않게 매번 컴파일한다."""
    compiled = re.compile(pattern, flags)
    start = time.perf_counter()
    matched = compiled.fullmatch(text) is not None
    return time.perf_counter() - start, matched


def section(title: str) -> None:
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


def sweep(pattern: str, make_text, lengths, *, header: str) -> None:
    """길이를 늘려 가며 시간을 찍는다. 앞 측정 대비 배수를 함께 적는다."""
    print(f"  식: {pattern!r}   {header}")
    print(f"  {'n':>6} {'시간(초)':>10} {'직전 대비':>9}  결과")
    previous = None
    for n in lengths:
        seconds, matched = elapsed(pattern, make_text(n))
        ratio = f"×{seconds / previous:4.1f}" if previous and previous > 0 else "    -"
        print(f"  {n:>6} {seconds:>10.4f} {ratio:>9}  {'매칭' if matched else '불일치'}")
        previous = seconds
        if seconds > EXP_LIMIT:
            print(f"  … {EXP_LIMIT:.0f}초를 넘겨 여기서 멈춘다")
            break


def main() -> None:
    print(f"Python {sys.version.split()[0]} · re 모듈 (표준 라이브러리)")

    section("1. 중첩 반복 (a+)+ 는 길이가 하나 늘 때마다 시간이 두 배가 된다")
    sweep(
        r"(a+)+$",
        lambda n: "a" * n + "!",
        range(EXPONENTIAL_START, EXPONENTIAL_START + EXPONENTIAL_STEPS),
        header="입력: 'a'×n 뒤에 '!' (끝이 안 맞아 실패하는 입력)",
    )

    section("2. 같은 입력이라도 매칭에 성공하면 한 번에 끝난다")
    for n in (20, 25, 28):
        seconds, matched = elapsed(r"(a+)+$", "a" * n)
        print(f"  n={n:<3} {seconds:.6f}초  {'매칭' if matched else '불일치'}")
    print("  → 폭발은 '실패를 확정하려고 모든 분할을 시도할 때' 일어난다")

    section("3. 겹치는 선택지 (\\w+\\s?)* — 실무에서 흔한 모양")
    sweep(
        r"(\w+\s?)*$",
        lambda n: "a" * n + "!",
        range(EXPONENTIAL_START, EXPONENTIAL_START + EXPONENTIAL_STEPS),
        header="단어를 공백으로 이어 받는 식. 공백이 선택(?)이라 분할이 겹친다",
    )

    section("4. 다항 폭발 — 끝 공백을 찾는 \\s+$ 는 n² 으로 는다")
    print("  식: '\\s+$' (trim 대용으로 흔히 쓰는 식).  입력: 공백×n 뒤에 'x'")
    print(f"  {'n':>6} {'시간(초)':>10} {'직전 대비':>9}")
    previous = None
    for n in (5000, 10000, 20000, 40000):
        compiled = re.compile(r"\s+$")
        text = " " * n + "x"
        start = time.perf_counter()
        compiled.search(text)
        seconds = time.perf_counter() - start
        ratio = f"×{seconds / previous:4.1f}" if previous else "    -"
        print(f"  {n:>6} {seconds:>10.4f} {ratio:>9}")
        previous = seconds
    print("  → n 이 2배면 시간은 4배. 지수는 아니지만 길이 제한 없이는 역시 멈춘다")

    section("5. 길이 제한이 막는 것과 못 막는 것")
    for pattern, n, label in (
        (r"(a+)+$", 30, "지수 식 + 길이 30"),
        (r"\s+$", 30, "다항 식 + 길이 30"),
    ):
        text = "a" * n + "!" if "a" in pattern else " " * n + "x"
        start = time.perf_counter()
        re.compile(pattern).search(text)
        seconds = time.perf_counter() - start
        print(f"  {label:<18} {seconds:>10.4f}초")
    print("  → 다항 식은 길이 제한으로 충분하다. 지수 식은 30자도 못 버틴다")

    section("6. 식을 고친다 — 분할이 하나뿐이면 백트래킹할 것이 없다")
    fixes = [
        (r"a+$", "중첩을 푼다: (a+)+ 와 같은 언어를 받는다"),
        (r"(a++)+$", "소유 한정자 a++ (Python 3.11+): 한 번 먹은 글자를 돌려주지 않는다"),
        (r"(?>a+)+$", "원자 그룹 (?>...) (Python 3.11+): 그룹 안으로 되돌아가지 않는다"),
        (r"\w+(\s\w+)*$", "(\\w+\\s?)* 를 고친 것: 공백을 필수로 두어 분할을 하나로"),
    ]
    for pattern, note in fixes:
        n = 40
        seconds, matched = elapsed(pattern, "a" * n + "!")
        print(f"  {pattern:<16} n={n}  {seconds:.6f}초  — {note}")

    section("7. 타임아웃 — 표준 re 에는 없고, 스레드로 감싸도 제때 못 돌아온다")
    worker = threading.Thread(
        target=lambda: re.compile(r"(a+)+$").fullmatch("a" * 26 + "!"), daemon=True
    )
    start = time.perf_counter()
    worker.start()
    worker.join(timeout=0.1)
    waited = time.perf_counter() - start
    print(f"  join(timeout=0.1) 이 실제로 돌아오기까지 {waited:.3f}초")
    print("  → 매칭 루프가 C 안에서 GIL 을 쥔 채 돌아, 주 스레드가 0.1초 뒤에 깨어나지 못한다")

    section("8. 다른 엔진 — 폭발하는 식이 다르고, timeout 은 실제로 끊는다")
    try:
        import regex  # 선택 의존성. requirements.txt 참고
    except ImportError:
        print("  regex 모듈이 없어 이 절은 건너뛴다")
        return
    print(f"  regex {regex.__version__}")
    print(f"  {'식':<12} {'n':>3} {'re(초)':>9} {'regex(초)':>10}")
    for pattern, n in ((r"(a+)+$", 26), (r"(a|a)*$", 24)):
        text = "a" * n + "!"
        std_seconds, _ = elapsed(pattern, text)
        start = time.perf_counter()
        regex.fullmatch(pattern, text)
        alt_seconds = time.perf_counter() - start
        print(f"  {pattern:<12} {n:>3} {std_seconds:>9.4f} {alt_seconds:>10.4f}")
    print("  → (a+)+ 는 regex 가 접어서 즉시 끝내지만, (a|a)* 는 양쪽 다 폭발한다")
    start = time.perf_counter()
    try:
        regex.fullmatch(r"(a|a)*$", "a" * 26 + "!", timeout=0.1)
        print("  regex.fullmatch((a|a)*$, timeout=0.1): 예외 없이 끝남")
    except TimeoutError as exc:
        print(f"  regex.fullmatch((a|a)*$, timeout=0.1) → {type(exc).__name__}: {exc}"
              f"  ({time.perf_counter() - start:.3f}초 만에 중단)")


if __name__ == "__main__":
    main()
