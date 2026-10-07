"""공시 시한 — 법이 정한 달력과 거래소가 정한 달력.

정기공시(사업보고서·분기·반기보고서)는 자본시장법이 '며칠 이내'로 정하고, 기간은
민법 방식(역에 의한 계산)으로 센다. 거래소 수시공시·조회공시는 '당일·익일'로 정하고,
매매거래일로 센다. 가상 회사 두 곳(가나전자 12월 결산, 다라물산 3월 결산)의 시한을
두 방식으로 계산한다.
"""
import datetime as dt
import platform
import sys

WEEKDAY_KO = "월화수목금토일"

# 예제 날짜 범위에 걸리는 공휴일만 넣었다. 다른 해·다른 날짜를 계산하려면 보태야 한다.
HOLIDAYS = {
    dt.date(2024, 5, 15): "부처님오신날",
    dt.date(2026, 2, 16): "설날 연휴",
    dt.date(2026, 2, 17): "설날",
    dt.date(2026, 2, 18): "설날 연휴",
    dt.date(2026, 10, 5): "개천절 대체공휴일",
    dt.date(2026, 10, 9): "한글날",
}


def fmt(day: dt.date) -> str:
    return f"{day.isoformat()}({WEEKDAY_KO[day.weekday()]})"


def is_closed(day: dt.date) -> bool:
    return day.weekday() >= 5 or day in HOLIDAYS


def statutory_deadline(period_end: dt.date, days: int) -> tuple[dt.date, dt.date]:
    """기간 말일 다음 날 0시에 시작하므로 그날을 1일째로 센다(민법 제157조 단서).

    말일이 토요일·공휴일이면 그 다음 날 만료한다(민법 제161조).
    돌려주는 값은 (산술상 말일, 실제 만료일).
    """
    raw = period_end + dt.timedelta(days=days)
    due = raw
    while is_closed(due):
        due += dt.timedelta(days=1)
    return raw, due


def next_trading_day(day: dt.date) -> dt.date:
    nxt = day + dt.timedelta(days=1)
    while is_closed(nxt):
        nxt += dt.timedelta(days=1)
    return nxt


def print_rules() -> None:
    print("[0] 기간을 세는 두 방식")
    print("  정기공시  : 자본시장법 '경과 후 N일 이내' — 역(달력)으로 센다")
    print("              결산일 다음 날 0시부터 시작하므로 그날이 1일째, 말일이 토·공휴일이면 다음 날")
    print("  거래소공시: 공시규정 '당일·익일' — 매매거래일로 센다 (주말·휴장일 건너뜀)")
    print()


def print_periodic(name: str, year_end_month: int, years: list[int]) -> None:
    print(f"[1] {name} — {year_end_month}월 결산, 정기보고서 법정 시한")
    print(f"  {'회계연도':<8} {'보고서':<10} {'기간 말일':<15} {'+N일':>5}  {'산술상 말일':<15} {'제출 시한':<15} 비고")
    for year in years:
        # 사업연도 말일과 그 앞 세 분기 말일
        fy_end = dt.date(year, year_end_month, 31 if year_end_month in (3, 12) else 30)
        q_ends = []
        for back in (9, 6, 3):
            month = (year_end_month - back - 1) % 12 + 1
            q_year = year if month < year_end_month else year - 1
            last_day = (dt.date(q_year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)).day
            q_ends.append(dt.date(q_year, month, last_day))
        rows = [
            ("1분기보고서", q_ends[0], 45),
            ("반기보고서", q_ends[1], 45),
            ("3분기보고서", q_ends[2], 45),
            ("사업보고서", fy_end, 90),
        ]
        for label, end, days in rows:
            raw, due = statutory_deadline(end, days)
            note = ""
            if raw != due:
                skipped = [HOLIDAYS.get(raw + dt.timedelta(days=i), "주말") for i in range((due - raw).days)]
                note = f"{fmt(raw)}부터 {len(skipped)}일 쉼({'·'.join(dict.fromkeys(skipped))}) → 다음 날"
            print(f"  FY{year:<6} {label:<10} {fmt(end):<15} {days:>5}  {fmt(raw):<15} {fmt(due):<15} {note}")
    print()


def print_leap_year() -> None:
    print("[2] 같은 '90일'이 윤년에는 하루 당겨진다 (12월 결산 사업보고서)")
    for year in (2025, 2026, 2027):
        fy_end = dt.date(year, 12, 31)
        raw, due = statutory_deadline(fy_end, 90)
        feb = (dt.date(year + 1, 3, 1) - dt.date(year + 1, 2, 1)).days
        print(f"  FY{year} → {year + 1}년 2월 {feb}일  산술상 말일 {fmt(raw)}  제출 시한 {fmt(due)}")
    print()


def print_exchange() -> None:
    print("[3] 가나전자 거래소 공시 — 매매거래일로 센다")
    cases = [
        ("수시공시(당일)", "이사회 결의", dt.date(2026, 10, 16), "15:00", "same"),
        ("수시공시(익일)", "사유 발생", dt.date(2026, 10, 16), "11:00", "next"),
        ("수시공시(익일)", "사유 발생", dt.date(2026, 10, 8), "11:00", "next"),
        ("조회공시 풍문·보도", "오전 요구", dt.date(2026, 10, 16), "10:00", "same"),
        ("조회공시 풍문·보도", "오후 요구", dt.date(2026, 10, 16), "14:00", "next_noon"),
        ("조회공시 시황급변", "요구", dt.date(2026, 10, 8), "10:00", "next"),
    ]
    print(f"  {'구분':<14} {'계기':<8} {'발생·요구 시각':<22} 시한")
    for kind, trigger, day, time, rule in cases:
        if rule == "same":
            due = f"{fmt(day)} 18:00"
        elif rule == "next":
            due = f"{fmt(next_trading_day(day))} 18:00"
        else:
            due = f"{fmt(next_trading_day(day))} 12:00"
        print(f"  {kind:<14} {trigger:<8} {fmt(day) + ' ' + time:<22} {due}")
    calendar_next = dt.date(2026, 10, 8) + dt.timedelta(days=1)
    print(f"  * 10-08(목) 다음 날을 달력으로 세면 {fmt(calendar_next)} {HOLIDAYS[calendar_next]},"
          f" 매매거래일로 세면 {fmt(next_trading_day(dt.date(2026, 10, 8)))}")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print_rules()
    print_periodic("가나전자", 12, [2024, 2025])
    print_periodic("다라물산", 3, [2026])
    print_leap_year()
    print_exchange()


if __name__ == "__main__":
    main()
