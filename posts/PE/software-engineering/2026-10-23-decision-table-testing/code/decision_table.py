"""결정 테이블의 전체 전개·실현 불가능 열 제거·열 병합을 계산으로 확인한다.

ISTQB CTFL v4.0.1 §4.2.3 이 적은 세 가지를 그대로 따라간다.
 - 전체 결정 테이블은 조건의 모든 조합을 덮을 만큼 열을 가진다
 - 실현 불가능한 조합의 열을 지워 단순화한다
 - 결과에 영향을 주지 않는 조건이 있는 열끼리 병합해 최소화한다
커버리지 항목은 실현 가능한 조합의 열이고, 분모는 그 열의 개수다.
"""

import itertools
import platform
import sys
import unicodedata

DASH = "–"  # 결과에 영향을 주지 않는 조건 (ISTQB 표기)
NA = "N/A"  # 실현 불가능한 조합


def full_table(condition_names, action_of, feasible=None):
    """조건 조합을 전부 전개해 (조합, 액션, 실현 가능 여부) 목록을 돌려준다."""
    rows = []
    for combo in itertools.product([True, False], repeat=len(condition_names)):
        ok = True if feasible is None else feasible(*combo)
        rows.append((combo, action_of(*combo) if ok else None, ok))
    return rows


def merge_columns(rows):
    """같은 액션을 내는 열끼리 한 조건만 다른 쌍을 반복해 묶는다.

    Quine-McCluskey 의 소항 생성과 같은 절차다. 묶인 자리는 DASH 가 되고,
    더 묶이지 않는 항만 남는다. 실현 불가능한 조합은 묶음 대상에서 빼므로
    (ISTQB 가 말하는 '열 삭제') 지워진 조합을 되살려 쓰지 않는다.
    """
    by_action = {}
    for combo, action, ok in rows:
        if ok:
            by_action.setdefault(action, []).append(tuple(combo))

    merged = {}
    for action, terms in by_action.items():
        current = {t: False for t in terms}  # 항 -> 더 큰 항에 흡수됐는가
        result = []
        while current:
            nxt = {}
            for a, b in itertools.combinations(current, 2):
                diff = [i for i in range(len(a)) if a[i] != b[i]]
                if len(diff) == 1:
                    combined = tuple(
                        DASH if i == diff[0] else a[i] for i in range(len(a))
                    )
                    nxt.setdefault(combined, False)
                    current[a] = True
                    current[b] = True
            result += [t for t, absorbed in current.items() if not absorbed]
            current = nxt
        merged[action] = sorted(set(result), key=str)
    return merged


def cell(value):
    if value == DASH:
        return DASH
    return "T" if value else "F"


def display_width(text):
    """한글은 터미널에서 두 칸을 차지하므로 len() 으로는 자리를 맞출 수 없다."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text, width):
    return text + " " * max(0, width - display_width(text))


def rpad(text, width):
    return " " * max(0, width - display_width(text)) + text


def print_table(title, condition_names, rows):
    print(f"[{title}] 전체 결정 테이블 — 조건 {len(condition_names)}개, "
          f"열 {len(rows)}개 (2^{len(condition_names)})")
    label = max([display_width(n) for n in condition_names] + [4]) + 2
    print(" " * label + "".join(rpad(str(i + 1), 5) for i in range(len(rows))))
    for i, name in enumerate(condition_names):
        line = pad(name, label)
        for combo, _action, ok in rows:
            line += rpad(NA if not ok else cell(combo[i]), 5)
        print(line)
    line = pad("액션", label)
    for _combo, action, ok in rows:
        line += rpad(NA if not ok else action, 5)
    print(line)
    feasible_count = sum(1 for _c, _a, ok in rows if ok)
    print(f"  실현 가능한 열 {feasible_count}개 / 전체 {len(rows)}개"
          f" → 100% 커버리지의 분모는 {feasible_count}")
    print()


def print_merged(title, condition_names, merged):
    total = sum(len(terms) for terms in merged.values())
    print(f"[{title}] 병합 후 — 열 {total}개 (조건 순서: "
          f"{', '.join(condition_names)})")
    for action in sorted(merged):
        for term in merged[action]:
            cells = "  ".join(rpad(cell(v), 3) for v in term)
            print(f"  {cells}  →  {action}")
    print()


def main():
    print(f"Python {platform.python_version()} ({sys.platform})")
    print()

    # 예 1 — API 요청 처리. 앞 조건이 거짓이면 뒤 조건은 결과를 바꾸지 못한다.
    api_conditions = ["토큰 유효", "한도 이내", "리소스 존재"]

    def api_action(token_valid, within_quota, resource_exists):
        if not token_valid:
            return "401"
        if not within_quota:
            return "429"
        if not resource_exists:
            return "404"
        return "200"

    api_rows = full_table(api_conditions, api_action)
    print_table("예 1 · API 요청", api_conditions, api_rows)
    print_merged("예 1 · API 요청", api_conditions, merge_columns(api_rows))

    # 예 2 — 같은 변수의 범위를 나눈 두 조건. 둘 다 참인 조합은 만들 수 없다.
    fare_conditions = ["만 19세 미만", "만 65세 이상"]

    def fare_action(under19, over65):
        if under19:
            return "학생"
        if over65:
            return "경로"
        return "일반"

    def fare_feasible(under19, over65):
        return not (under19 and over65)

    fare_rows = full_table(fare_conditions, fare_action, feasible=fare_feasible)
    print_table("예 2 · 요금 구분", fare_conditions, fare_rows)
    print_merged("예 2 · 요금 구분", fare_conditions, merge_columns(fare_rows))

    # 조합 폭발 — 조건 수에 따라 전체 열이 몇 개가 되는가
    print("[조합 폭발] 조건 n개의 전체 결정 테이블 열 수 = 2^n")
    for n in (3, 5, 10, 15, 20):
        print(f"  n = {n:>2} → {2 ** n:>9,} 열")


if __name__ == "__main__":
    main()
