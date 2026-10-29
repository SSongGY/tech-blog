"""같은 숫자를 XBRL 인스턴스에서 꺼낼 때와 보고서 표에서 꺼낼 때의 차이를 본다.

가상 회사 '가나전자'의 값을 두 가지 모양으로 두고 같은 질문을 던진다.
  1. XBRL — 요소 이름과 기간(context)이 데이터에 붙어 있다
  2. 보고서 표 — 사람이 읽으라고 만든 문자열. 기간은 머리글에만 있다
숫자는 전부 지어낸 값이다.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

XBRLI = "{http://www.xbrl.org/2003/instance}"
DEMO = "{http://example.invalid/demo-taxonomy}"

# 보고서 본문에 실리는 모양. 단위가 머리글 한 줄에만 적히고,
# '제26기'가 어느 기간인지는 다른 장을 봐야 안다.
REPORT_TABLE = """\
                                                  (단위: 백만원)
구  분              제26기          제25기          제24기
매출액           1,842,300       1,710,800       1,655,400
영업이익           112,700         139,500         128,100
"""


def load_facts(path):
    """인스턴스에서 (요소, 기간, 값)을 전부 꺼낸다. 요소 이름을 미리 알 필요가 없다."""
    root = ET.parse(path).getroot()

    periods = {}
    for context in root.findall(f"{XBRLI}context"):
        period = context.find(f"{XBRLI}period")
        start = period.findtext(f"{XBRLI}startDate")
        end = period.findtext(f"{XBRLI}endDate")
        periods[context.get("id")] = (start, end)

    facts = []
    for element in root:
        if not element.tag.startswith(DEMO):
            continue
        name = element.tag[len(DEMO):]
        start, end = periods[element.get("contextRef")]
        facts.append((name, start, end, int(element.text)))
    return facts


def main():
    print(f"Python {sys.version.split()[0]}")
    print()

    instance = Path(__file__).with_name("gana_electronics.xml")
    facts = load_facts(instance)

    print("[ 1. XBRL 인스턴스에서 꺼낸 사실 ]")
    header = f"{'요소':<16} {'기간 시작':<12} {'기간 종료':<12} {'금액(원)':>18}"
    print(header)
    print("-" * len(header))
    for name, start, end, value in facts:
        print(f"{name:<16} {start:<12} {end:<12} {value:>18,}")

    print()
    print("[ 2. 보고서 표에 실린 같은 숫자 ]")
    print(REPORT_TABLE, end="")

    print()
    print("[ 3. 두 기간을 골라 증감을 센다 ]")
    revenue = {end: value for name, _, end, value in facts if name == "Revenue"}
    operating = {end: value for name, _, end, value in facts if name == "OperatingIncome"}
    prior, current = "2024-12-31", "2025-12-31"
    print(f"기준 기간      : {prior} -> {current}")
    print(f"매출액 증감률  : {(revenue[current] / revenue[prior] - 1) * 100:+.1f}%")
    print(f"영업이익 증감률: {(operating[current] / operating[prior] - 1) * 100:+.1f}%")
    print(f"영업이익률     : {operating[prior] / revenue[prior] * 100:.1f}%"
          f" -> {operating[current] / revenue[current] * 100:.1f}%")
    print()
    print("3번의 계산은 1번의 기간 표시만으로 성립한다. 2번에서 같은 계산을 하려면")
    print("'제26기'가 2025-12-31 로 끝나는 기간이라는 사실을 표 밖에서 먼저 찾아야 한다.")


if __name__ == "__main__":
    main()
