"""서머타임 경계에서 벽시계 시각이 사라지고 겹치는 것을 직접 뽑아 본다.

표준 라이브러리 zoneinfo 만 쓴다. 윈도우에는 IANA 타임존 DB 가 없으므로
tzdata 패키지가 필요하다 (requirements.txt 참고).
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import tzdata

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 68
NEW_YORK = ZoneInfo("America/New_York")
SEOUL = ZoneInfo("Asia/Seoul")
UTC = timezone.utc

# 2026년 미국 동부 전환일. 봄에는 02:00 -> 03:00, 가을에는 02:00 -> 01:00
SPRING = datetime(2026, 3, 8)
AUTUMN = datetime(2026, 11, 1)


def offset_text(moment: datetime) -> str:
    """timedelta 를 그대로 찍으면 '-1 day, 19:00:00' 이라 읽히지 않는다."""
    hours = moment.utcoffset().total_seconds() / 3600
    return f"{hours:+.0f}:00"


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def show_environment() -> None:
    section("환경")
    print(f"  Python   {platform.python_version()}")
    print(f"  tzdata   {tzdata.__version__}  (IANA {tzdata.IANA_VERSION})")
    print(f"  OS       {platform.system()} {platform.release()}")
    print()


def walk(start: datetime, zone: ZoneInfo, *, minutes: int, steps: int) -> None:
    """벽시계 시각을 분 단위로 만들어 UTC 로 바꿔 본다."""
    print(f"    {'만든 벽시계 시각':20s} {'약칭':6s} {'오프셋':8s} {'UTC 로 바꾸면':20s}")
    for i in range(steps):
        wall = start + timedelta(minutes=minutes * i)
        aware = wall.replace(tzinfo=zone)
        offset = aware.utcoffset()
        hours = offset.total_seconds() / 3600
        print(
            f"    {wall:%Y-%m-%d %H:%M}      "
            f"{aware.tzname():6s} {hours:+6.1f}  "
            f"{aware.astimezone(UTC):%Y-%m-%d %H:%M} UTC"
        )
    print()


def show_gap() -> None:
    section("1. 봄 — 02:00 부터 한 시간이 달력에서 사라진다")
    print("  뉴욕 2026-03-08, 10분 간격으로 벽시계 시각을 만들어 본다")
    walk(SPRING.replace(hour=1, minute=40), NEW_YORK, minutes=10, steps=9)

    ghost = datetime(2026, 3, 8, 2, 30, tzinfo=NEW_YORK)
    print("  존재하지 않는 02:30 을 만들어도 예외가 나지 않는다")
    print(f"    만든 값      {ghost:%Y-%m-%d %H:%M} {ghost.tzname()} {offset_text(ghost)}")
    round_trip = ghost.astimezone(UTC).astimezone(NEW_YORK)
    print(f"    UTC 왕복 후  {round_trip:%Y-%m-%d %H:%M} {round_trip.tzname()}")
    print(f"    같은 값인가  {ghost == round_trip}  (벽시계 표기는 {ghost:%H:%M} -> {round_trip:%H:%M})")
    print()

    print("  이 구간에서 fold 는 중복 구간과 반대로 움직인다")
    for fold in (0, 1):
        g = ghost.replace(fold=fold)
        print(f"    fold={fold}  {g.tzname()} {offset_text(g)}  ->  {g.astimezone(UTC):%H:%M} UTC")
    print()


def show_overlap() -> None:
    section("2. 가을 — 01:00 부터 한 시간이 두 번 온다")
    print("  뉴욕 2026-11-01, UTC 쪽에서 10분 간격으로 내려온다")
    print(f"    {'UTC':20s} {'뉴욕 벽시계':20s} {'약칭':6s} fold")
    base = datetime(2026, 11, 1, 4, 40, tzinfo=UTC)
    for i in range(13):
        moment = base + timedelta(minutes=10 * i)
        local = moment.astimezone(NEW_YORK)
        print(
            f"    {moment:%Y-%m-%d %H:%M}      "
            f"{local:%Y-%m-%d %H:%M}      "
            f"{local.tzname():6s} {local.fold}"
        )
    print()

    print("  같은 벽시계 시각 01:30 이 가리키는 두 순간")
    for fold in (0, 1):
        local = datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK, fold=fold)
        print(
            f"    fold={fold}  {local:%H:%M} {local.tzname()}  "
            f"UTC {local.astimezone(UTC):%H:%M}  "
            f"timestamp {local.timestamp():.0f}"
        )
    gap_seconds = (
        datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK, fold=1).timestamp()
        - datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK, fold=0).timestamp()
    )
    print(f"    두 순간의 간격  {gap_seconds:.0f}초")
    print()


def show_storage() -> None:
    section("3. 무엇을 저장했느냐가 갈림길이다")
    moments = [
        datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK, fold=0),
        datetime(2026, 11, 1, 1, 30, tzinfo=NEW_YORK, fold=1),
    ]
    print("  (가) 벽시계 문자열만 저장했을 때")
    for moment in moments:
        text = moment.strftime("%Y-%m-%d %H:%M")
        restored = datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=NEW_YORK)
        print(
            f"    원래 UTC {moment.astimezone(UTC):%H:%M}  ->  저장 '{text}'  ->  "
            f"되읽은 UTC {restored.astimezone(UTC):%H:%M}  (fold 기본값 {restored.fold})"
        )

    print("\n  (나) UTC 로 저장했을 때")
    for moment in moments:
        text = moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ")
        restored = datetime.strptime(text, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
        print(
            f"    원래 UTC {moment.astimezone(UTC):%H:%M}  ->  저장 '{text}'  ->  "
            f"되읽어 뉴욕 {restored.astimezone(NEW_YORK):%H:%M} {restored.astimezone(NEW_YORK).tzname()}"
        )
    print()


def show_arithmetic() -> None:
    section("4. 전환일에는 하루가 24시간이 아니다")
    for day in (SPRING, AUTUMN):
        start = day.replace(tzinfo=NEW_YORK)
        end = (day + timedelta(days=1)).replace(tzinfo=NEW_YORK)
        length = end.astimezone(UTC) - start.astimezone(UTC)
        print(f"    {day:%Y-%m-%d} 00:00 부터 다음 날 00:00 까지  {length}")
    print()

    print("  '하루 뒤'와 '24시간 뒤'가 갈린다 (뉴욕 2026-11-01 00:30 기준)")
    base = datetime(2026, 11, 1, 0, 30, tzinfo=NEW_YORK)
    by_day = base + timedelta(days=1)
    by_hours = (base.astimezone(UTC) + timedelta(hours=24)).astimezone(NEW_YORK)
    print(f"    + timedelta(days=1)        {by_day:%Y-%m-%d %H:%M} {by_day.tzname()}")
    print(f"    UTC 로 바꿔 + 24시간        {by_hours:%Y-%m-%d %H:%M} {by_hours.tzname()}")
    print()


def show_korea() -> None:
    section("5. 한국은 세 시기에 겪었다")
    print("  UTC 를 1시간씩 훑어 Asia/Seoul 의 오프셋이나 약칭이 바뀌는 지점을 찾는다")
    previous = None
    moment = datetime(1945, 1, 1, tzinfo=UTC)
    changes = 0
    while moment < datetime(1990, 1, 1, tzinfo=UTC):
        local = moment.astimezone(SEOUL)
        key = (local.utcoffset(), local.tzname())
        if key != previous:
            if previous is not None:
                changes += 1
                print(
                    f"    {moment:%Y-%m-%d %H:%M} UTC  ->  "
                    f"서울 {local:%Y-%m-%d %H:%M} {local.tzname():4s} "
                    f"{local.utcoffset().total_seconds() / 3600:+.1f}"
                )
            previous = key
        moment += timedelta(hours=1)
    print(f"\n    1945~1989 사이 전환 {changes}회")
    print()

    ghost = datetime(1987, 5, 10, 2, 30, tzinfo=SEOUL)
    print(f"    1987-05-10 02:30 도 사라진 시각이다  ->  "
          f"UTC {ghost.astimezone(UTC):%H:%M}, 되돌리면 {ghost.astimezone(UTC).astimezone(SEOUL):%H:%M}")
    print()


def main() -> None:
    show_environment()
    show_gap()
    show_overlap()
    show_storage()
    show_arithmetic()
    show_korea()


if __name__ == "__main__":
    main()
