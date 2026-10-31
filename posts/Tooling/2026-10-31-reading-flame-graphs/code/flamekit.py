"""표본 수집기와 플레임 그래프 SVG 생성기.

플레임 그래프는 **스택 표본의 모음**을 그린 그림이다. 그래서 만드는 순서도 셋이다.

1. 일정 주기로 대상 스레드의 호출 스택을 통째로 집는다 (sample)
2. 같은 스택끼리 묶어 "a;b;c 횟수" 한 줄로 접는다 (fold, collapsed stack)
3. 접힌 줄을 트리로 되돌려 가로폭을 표본 수에 비례시켜 그린다 (render)

바깥 도구(py-spy, perf + flamegraph.pl)가 하는 일도 이 셋이다. 중간 산출물인
접힌 스택이 텍스트라서, 그림을 그리기 전에 숫자를 먼저 확인할 수 있다.
"""

from __future__ import annotations

import sys
import threading
import time
from collections import Counter

FONT_SIZE = 13
ROW_HEIGHT = 22
CANVAS_WIDTH = 880
MARGIN_X = 10
LABEL_PAD = 6
# check-svg 가 쓰는 폭 추정과 같은 계수. 라벨이 칸을 넘지 않게 여기서 미리 잰다.
ASCII_CHAR_RATIO = 0.55

PALETTE = ["#d9a05b", "#c98b4b", "#e0b473", "#bf7a3c", "#d19a56", "#cf8f4f"]


class StackSampler(threading.Thread):
    """대상 스레드의 호출 스택을 주기적으로 집는 표본 수집기.

    sys._current_frames() 는 살아 있는 모든 스레드의 현재 프레임을 돌려준다.
    거기서 f_back 을 따라 올라가면 그 순간의 스택 전체가 나온다. 대상 스레드를
    멈추지 않으므로, 집는 동안에도 프로그램은 그대로 돈다.
    """

    def __init__(self, target_ident: int, interval: float = 0.001) -> None:
        super().__init__(daemon=True)
        self.target_ident = target_ident
        self.interval = interval
        self.counts: Counter[tuple[str, ...]] = Counter()
        self.missed = 0
        self._stop = threading.Event()

    def run(self) -> None:
        while not self._stop.is_set():
            frame = sys._current_frames().get(self.target_ident)
            if frame is None:
                self.missed += 1
            else:
                stack = []
                while frame is not None:
                    stack.append(frame.f_code.co_name)
                    frame = frame.f_back
                self.counts[tuple(reversed(stack))] += 1
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self.join()


def fold(counts: Counter[tuple[str, ...]], root: str) -> tuple[list[tuple[str, int]], int]:
    """접힌 스택(collapsed stack) 줄로 바꾼다.

    root 프레임이 없는 표본은 버린다. 수집기를 띄우는 동안에도 표본이 잡히는데,
    그건 측정 대상 바깥이라 그림에 넣으면 폭이 그만큼 왜곡된다. 몇 개를 버렸는지는
    같이 돌려주고 출력에 적는다 — 조용히 버리면 합계가 왜 안 맞는지 알 수 없다.
    """
    folded: Counter[str] = Counter()
    dropped = 0
    for stack, hits in counts.items():
        if root in stack:
            trimmed = stack[stack.index(root):]
            folded[";".join(trimmed)] += hits
        else:
            dropped += hits
    return sorted(folded.items()), dropped


def build_tree(folded: list[tuple[str, int]]) -> dict:
    """접힌 줄을 트리로 되돌린다. value 는 그 프레임을 포함한 표본 수다."""
    root: dict = {"name": "all", "value": 0, "children": {}}
    for line, hits in folded:
        node = root
        node["value"] += hits
        for name in line.split(";"):
            node = node["children"].setdefault(
                name, {"name": name, "value": 0, "children": {}}
            )
            node["value"] += hits
    return root


def self_counts(folded: list[tuple[str, int]]) -> Counter[str]:
    """맨 위 프레임만 센다. 그 함수가 직접 쓰고 있던 시간이다."""
    leaves: Counter[str] = Counter()
    for line, hits in folded:
        leaves[line.split(";")[-1]] += hits
    return leaves


def inclusive_counts(folded: list[tuple[str, int]]) -> Counter[str]:
    """스택 어디에든 나오면 센다. 같은 스택에 두 번 나와도 한 번만 센다."""
    totals: Counter[str] = Counter()
    for line, hits in folded:
        for name in set(line.split(";")):
            totals[name] += hits
    return totals


def _fit(label: str, box_width: float) -> str:
    """칸에 들어가는 만큼만 남긴다. 넘치면 라벨을 아예 넣지 않는다."""
    room = box_width - LABEL_PAD * 2
    per_char = FONT_SIZE * ASCII_CHAR_RATIO
    chars = int(room // per_char)
    if chars < 3:
        return ""
    if len(label) <= chars:
        return label
    return label[: chars - 1] + "~"


def _layout(node: dict, depth: int, x: float, scale: float, out: list) -> None:
    width = node["value"] * scale
    out.append((depth, x, width, node["name"], node["value"]))
    cursor = x
    # 자식을 이름순으로 놓는다. 플레임 그래프의 가로축이 시간이 아닌 이유가 이것이다.
    for name in sorted(node["children"]):
        child = node["children"][name]
        _layout(child, depth + 1, cursor, scale, out)
        cursor += child["value"] * scale


def render(tree: dict, title: str, subtitle: str, total: int) -> str:
    cells: list = []
    usable = CANVAS_WIDTH - MARGIN_X * 2
    _layout(tree, 0, MARGIN_X, usable / tree["value"], cells)

    depth_max = max(depth for depth, *_ in cells)
    top = 70
    height = top + (depth_max + 1) * ROW_HEIGHT + 16

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" '
        f'height="{height}" viewBox="0 0 {CANVAS_WIDTH} {height}" '
        f"font-family=\"'Consolas','D2Coding',monospace\">",
        f'<rect width="{CANVAS_WIDTH}" height="{height}" fill="#f8f9fa"/>',
        f'<text x="{MARGIN_X}" y="28" font-size="16" font-weight="bold" '
        f'fill="#212529">{title}</text>',
        f'<text x="{MARGIN_X}" y="50" font-size="13" fill="#495057">{subtitle}</text>',
    ]
    for index, (depth, x, width, name, value) in enumerate(cells):
        if width < 1:
            continue
        y = top + (depth_max - depth) * ROW_HEIGHT
        fill = "#e9ecef" if depth == 0 else PALETTE[index % len(PALETTE)]
        share = value / total * 100
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{max(width - 1, 0.5):.1f}" '
            f'height="{ROW_HEIGHT - 2}" fill="{fill}" stroke="#495057" '
            f'stroke-width="0.6"><title>{name} — {value}표본 ({share:.1f}%)</title></rect>'
        )
        label = _fit(name, width)
        if label:
            parts.append(
                f'<text x="{x + LABEL_PAD:.1f}" y="{y + ROW_HEIGHT - 8}" '
                f'font-size="{FONT_SIZE}" fill="#212529">{label}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
