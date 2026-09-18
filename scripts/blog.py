#!/usr/bin/env python3
"""기술 블로그 운영 CLI.

사용법:
    python scripts/blog.py pick              # 오늘 쓸 주제 선정 (하루 5편, 트랙별 편성)
    python scripts/blog.py new <id> <slug>   # 글 폴더 스캐폴딩
    python scripts/blog.py related [feature] # 같은 기능으로 쓴 글 목록
    python scripts/blog.py relink            # 같은 기능 글끼리 상호 링크 재생성
    python scripts/blog.py lint              # 글 규칙 검사
    python scripts/blog.py index             # 글 목록 페이지(POSTS.md) 재생성
    python scripts/blog.py done <id>         # 주제를 done으로 표시하고 이력 기록
    python scripts/blog.py tistory <slug>    # 티스토리 붙여넣기용 변환
    python scripts/blog.py status            # 백로그 잔량과 발행 현황
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):  # 윈도우 cp949 콘솔에서 한글이 깨지는 것 방지
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
BACKLOG_PATH = ROOT / "topics" / "backlog.yaml"
PUBLISHED_PATH = ROOT / "topics" / "published.md"
POSTS_DIR = ROOT / "posts"
DIST_DIR = ROOT / "dist" / "tistory"

FIGURE_IMAGE = re.compile(r"!\[([^\]]*)\]\((fig/[^)]+)\)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

CORE_CATEGORIES = {"Database", "Backend", "Performance"}

TRACKS = ("basics", "product", "pe", "general")

# 하루 5편을 유지한다. 기본 문법(basics)을 다 쓰고 나면 그 한 자리를 기술사가 가져간다.
# pe = 정보관리기술사 시험 과목 기술. 목표가 걸린 트랙이라 줄어드는 일이 없다.
# product는 한 제품을 끝내면 다음 제품으로 넘어가므로 소진되지 않는다(PRODUCT_ROTATION).
PLAN_WITH_BASICS = {"basics": 1, "product": 1, "pe": 2, "general": 1}   # 합 5편
PLAN_AFTER_BASICS = {"basics": 0, "product": 1, "pe": 3, "general": 1}  # 합 5편


TRACK_LABEL = {
    "basics": "DB문법",
    "product": "DB기능",
    "pe": "기술사",
    "general": "일반",
}


def count_todo(data: dict, track: str) -> int:
    return sum(
        1 for t in data["topics"]
        if t["status"] == "todo" and track_of(t) == track
    )


def daily_plan(data: dict) -> dict[str, int]:
    """남은 기본 문법 주제 수에 따라 오늘의 트랙별 편수를 정한다.

    기본 문법이 남아 있으면 그 한 편을 쓰고, 소진되면 그 자리를 기술사가 가져간다.
    어느 쪽이든 하루 5편이다.
    """
    if count_todo(data, "basics") >= PLAN_WITH_BASICS["basics"]:
        return dict(PLAN_WITH_BASICS)
    return dict(PLAN_AFTER_BASICS)


# 트랙별 본문 길이 기준(공백·코드블록·표·인용·참고자료 제외)
# product 상한은 3,000으로 잡았다가 3,800으로 올렸다. 실행 검증된 제품 글은
# 속성 기본값·에러 코드·실측 출처를 함께 담아야 해서 서술이 길어진다.
# 실제로 첫 제품 글(Tibero 시퀀스)이 군살을 덜어내고도 3,700자를 넘었다.
BODY_CHARS_BY_TRACK = {
    "basics": (1200, 2500),
    "product": (1500, 3800),
    "pe": (1500, 3000),
    "general": (1800, 3500),
}


def track_of(topic: dict) -> str:
    track = topic.get("track") or "general"
    return track if track in TRACKS else "general"


def load_backlog() -> dict:
    return yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8"))


def set_status(topic_id: str, new_status: str) -> None:
    """해당 주제의 status 줄만 바꾼다.

    yaml.safe_dump로 전체를 다시 쓰면 주석과 인라인 리스트 표기가 사라진다.
    백로그는 사람이 직접 읽고 고치는 파일이므로 원문 포맷을 보존한다.
    """
    raw = BACKLOG_PATH.read_text(encoding="utf-8")
    block = re.compile(
        rf"(^  - id: {re.escape(topic_id)}\n(?:(?!^  - id: ).*\n)*?    status: )\w+",
        re.MULTILINE,
    )
    patched, hit_count = block.subn(rf"\g<1>{new_status}", raw)
    if hit_count != 1:
        raise SystemExit(f"{topic_id}의 status 줄을 정확히 찾지 못했다 (매칭 {hit_count}건).")
    BACKLOG_PATH.write_text(patched, encoding="utf-8")


def is_core(topic: dict) -> bool:
    return topic["category"] in CORE_CATEGORIES


def count_published(topics: list[dict]) -> tuple[int, int]:
    """이미 발행된 글의 (core, general) 편수."""
    done = [t for t in topics if t["status"] == "done"]
    core = sum(1 for t in done if is_core(t))
    return core, len(done) - core


def pick_general(data: dict, count: int) -> list[dict]:
    """일반 트랙에서 누적 core 비율이 목표(60%)에 가까워지도록 탐욕적으로 고른다."""
    topics = data["topics"]
    target_core = data["meta"]["target_ratio"]["core"]
    core_done, general_done = count_published(topics)

    available = [
        t for t in topics
        if t["status"] == "todo" and track_of(t) == "general"
    ]
    picked: list[dict] = []

    for _ in range(min(count, len(available))):
        core_pool = [t for t in available if is_core(t) and t not in picked]
        plain_pool = [t for t in available if not is_core(t) and t not in picked]
        if not core_pool and not plain_pool:
            break

        total = core_done + general_done + len(picked)
        current_core = core_done + sum(1 for t in picked if is_core(t))
        # 다음 한 편을 core로 뽑았을 때와 아닐 때의 목표 이탈도를 비교
        gap_if_core = abs((current_core + 1) / (total + 1) - target_core)
        gap_if_plain = abs(current_core / (total + 1) - target_core)

        prefer_core = gap_if_core <= gap_if_plain
        pool = (core_pool or plain_pool) if prefer_core else (plain_pool or core_pool)
        picked.append(pool[0])

    return picked


def pick_sequential(data: dict, track: str, count: int) -> list[dict]:
    """백로그 순서대로 고른다.

    제품 시리즈와 기본 문법은 순서대로 쌓아야 시리즈로 읽히므로 비율 계산을 하지 않는다.
    """
    available = [
        t for t in data["topics"]
        if t["status"] == "todo" and track_of(t) == track
    ]
    return available[:count]


def pick_topics(data: dict, counts: dict[str, int] | None = None) -> list[dict]:
    counts = counts or daily_plan(data)
    picked: list[dict] = []
    for track in ("basics", "product", "pe"):
        picked += pick_sequential(data, track, counts.get(track, 0))
    return picked + pick_general(data, counts.get("general", 0))


def cmd_pick(args: argparse.Namespace) -> int:
    data = load_backlog()
    counts = daily_plan(data)
    for track in TRACKS:
        override = getattr(args, track, None)
        if override is not None:
            counts[track] = override

    picked = pick_topics(data, counts)
    if not picked:
        print("백로그에 todo 주제가 없다. topics/backlog.yaml을 보충할 것.")
        return 1

    published = published_index()
    today = dt.date.today().isoformat()
    print(f"# {today} 작성 대상 {len(picked)}편\n")

    for i, topic in enumerate(picked, 1):
        area = topic["category"]
        if topic.get("subcategory"):
            area += f"/{topic['subcategory']}"
        label = TRACK_LABEL[track_of(topic)]
        print(f"[{i}] {topic['id']} · {label} · {area} · {topic['difficulty']}")
        print(f"    제목: {topic['title']}")
        print(f"    각도: {topic['angle']}")
        print(f"    예제: {topic['code']}  태그: {', '.join(topic['tags'])}")
        if topic.get("product"):
            print(f"    제품: {topic['product']} {topic['product_version']}"
                  f"  (버전을 본문과 프론트매터에 반드시 명시)")

        feature = topic.get("feature")
        if feature:
            siblings = [p for p in published.get(feature, []) if p["topic_id"] != topic["id"]]
            if siblings:
                print(f"    같은 기능({feature})으로 이미 쓴 글 — 링크와 비교 절을 넣을 것:")
                for sibling in siblings:
                    origin = sibling["product"] or sibling["environment"] or "?"
                    print(f"      · {sibling['title']}  [{origin}]")
                    print(f"        {sibling['path']}")
            else:
                print(f"    같은 기능({feature})으로 쓴 글 없음 — 비교 절 불필요")
        print()

    for track, need in counts.items():
        remaining = sum(
            1 for t in data["topics"]
            if t["status"] == "todo" and track_of(t) == track
        )
        if not need:
            print(f"{track:8s} todo {remaining:3d}개 (오늘은 배정 없음)")
            continue
        flag = "  ← 보충 필요" if remaining <= data["meta"]["low_watermark"] else ""
        print(f"{track:8s} todo {remaining:3d}개 (약 {remaining // need}일분){flag}")
    return 0


# ---------------------------------------------------------------- 제품 간 비교 연결

RELATED_BLOCK = re.compile(
    r"<!-- related:start -->\n.*?<!-- related:end -->\n", re.DOTALL
)


def read_meta(path: Path) -> dict | None:
    fm_match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    return yaml.safe_load(fm_match.group(1)) if fm_match else None


def published_index() -> dict[str, list[dict]]:
    """feature 키별로 이미 쓴 글 목록을 모은다."""
    index: dict[str, list[dict]] = {}
    for path in sorted(POSTS_DIR.glob("**/index.md")):
        meta = read_meta(path)
        if not meta or not meta.get("feature"):
            continue
        environment = meta.get("environment") or []
        index.setdefault(meta["feature"], []).append({
            "topic_id": meta.get("topic_id", ""),
            "title": meta.get("title", path.parent.name),
            "product": (
                f"{meta['product']} {meta.get('product_version', '')}".strip()
                if meta.get("product") else ""
            ),
            "environment": ", ".join(environment) if environment else "",
            "path": path,
        })
    return index


def cmd_related(args: argparse.Namespace) -> int:
    index = published_index()
    features = [args.feature] if args.feature else sorted(index)
    if not features:
        print("feature가 지정된 글이 없다.")
        return 1

    for feature in features:
        entries = index.get(feature, [])
        print(f"\n[{feature}] {len(entries)}편")
        for entry in entries:
            origin = entry["product"] or entry["environment"] or "?"
            print(f"  {entry['title']}")
            print(f"    {origin}  ·  {entry['path'].relative_to(POSTS_DIR)}")
    return 0


def cmd_relink(args: argparse.Namespace) -> int:
    """feature가 같은 글들끼리 서로를 가리키는 블록을 다시 만든다.

    새 글이 추가되면 기존 글에도 역링크가 생겨야 하므로 매번 전체를 재생성한다.
    """
    index = published_index()
    changed = 0

    for feature, entries in index.items():
        if len(entries) < 2:
            continue
        for entry in entries:
            others = [e for e in entries if e["path"] != entry["path"]]
            rows = []
            for other in others:
                rel = os.path.relpath(other["path"], entry["path"].parent)
                rel = rel.replace(os.sep, "/")
                origin = other["product"] or other["environment"] or ""
                suffix = f" — {origin}" if origin else ""
                rows.append(f"> - [{other['title']}]({rel}){suffix}")

            block = (
                "<!-- related:start -->\n"
                f"> **같은 기능을 다른 환경에서 다룬 글** (`{feature}`)\n"
                + "\n".join(rows)
                + "\n<!-- related:end -->\n"
            )
            text = entry["path"].read_text(encoding="utf-8")
            if RELATED_BLOCK.search(text):
                patched = RELATED_BLOCK.sub(lambda _: block, text)
            else:  # 첫 문단 앞, 프론트매터 바로 뒤에 넣는다
                fm_match = FRONTMATTER.match(text)
                cut = fm_match.end()
                patched = text[:cut] + "\n" + block + text[cut:]
            if patched != text:
                entry["path"].write_text(patched, encoding="utf-8")
                changed += 1
                print(f"갱신: {entry['path'].parent.relative_to(POSTS_DIR)}  ({feature})")

    print(f"\n{changed}개 글의 관련 글 블록을 갱신했다.")
    return 0


def post_dir_for(topic: dict, day: dt.date, slug: str) -> Path:
    """글이 들어갈 경로를 만든다.

    분야별로 찾아보기 쉽도록 카테고리 폴더 아래에 둔다. 특정 제품·도구에 묶인
    주제는 subcategory를 한 단계 더 둔다 (예: posts/Database/oracle/...).
    """
    parts = [topic["category"]]
    if topic.get("subcategory"):
        parts.append(topic["subcategory"])
    return POSTS_DIR.joinpath(*parts) / f"{day.isoformat()}-{slug}"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not slug:
        raise SystemExit("slug는 영문 소문자/숫자로 지정한다.")
    return slug


def cmd_new(args: argparse.Namespace) -> int:
    data = load_backlog()
    topic = next((t for t in data["topics"] if t["id"] == args.topic_id), None)
    if topic is None:
        print(f"주제 {args.topic_id}를 백로그에서 찾을 수 없다.")
        return 1

    today = dt.date.today()
    slug = slugify(args.slug)
    post_dir = post_dir_for(topic, today, slug)
    if post_dir.exists():
        print(f"이미 존재한다: {post_dir}")
        return 1

    (post_dir / "code").mkdir(parents=True)
    (post_dir / "fig").mkdir()

    is_product = track_of(topic) == "product"
    product_lines = ""
    if is_product:
        product_lines = (
            f"product: {topic['product']}\n"
            f"product_version: \"{topic['product_version']}\"\n"
        )
    # 제품 글은 기본이 매뉴얼 근거다. 실행 환경이 있으면 executed로 올린다.
    # 제품·기술사 글은 실행할 수 없는 경우가 많다. 기본을 매뉴얼 근거로 두고
    # 실행 환경이 있으면 executed로 올린다.
    verification = "executed" if track_of(topic) in ("basics", "general") else "manual-only"
    environment = f'["{topic["product"]} {topic["product_version"]}"]' if is_product else "[]"

    tags = ", ".join(topic["tags"])
    index_md = f"""---
title: "{topic['title']}"
date: {today.isoformat()}
categories: [{topic["category"]}]
subcategory: {topic.get("subcategory") or ""}
track: {track_of(topic)}
tags: [{tags}]
description: ""
difficulty: {topic['difficulty']}
{product_lines}feature: {topic.get("feature") or ""}
environment: {environment}
verification: {verification}
verified: false
topic_id: {topic['id']}
---

## 들어가며

## 개념

## 구조

![](fig/.svg)

> **구조 근거**: 공식 문서 링크 (섹션·앵커까지)

## 동작 원리

## 실습 예제

전체 소스: [`code/`](code/)

## 실무에서 주의할 점

## 정리

## 참고 자료
"""
    (post_dir / "index.md").write_text(index_md, encoding="utf-8")
    (post_dir / "code" / "README.md").write_text(
        f"# 예제 코드 — {topic['title']}\n\n## 실행\n\n```bash\n```\n",
        encoding="utf-8",
    )

    set_status(topic["id"], "writing")
    print(f"생성: {post_dir.relative_to(ROOT)}")
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    data = load_backlog()
    topic = next((t for t in data["topics"] if t["id"] == args.topic_id), None)
    if topic is None:
        print(f"주제 {args.topic_id}를 찾을 수 없다.")
        return 1

    set_status(topic["id"], "done")

    today = dt.date.today().isoformat()
    line = f"| {today} | {topic['id']} | {topic['category']} | {topic['title']} |\n"
    if not PUBLISHED_PATH.exists():
        PUBLISHED_PATH.write_text(
            "# 발행 이력\n\n새 주제를 고르기 전 이 목록에서 중복을 확인한다.\n\n"
            "| 날짜 | ID | 카테고리 | 제목 |\n|---|---|---|---|\n",
            encoding="utf-8",
        )
    with PUBLISHED_PATH.open("a", encoding="utf-8") as fp:
        fp.write(line)
    print(f"완료 처리: {topic['id']} — {topic['title']}")
    return 0


# 도식 SVG가 쓰는 font-family 이름들. 이 이름으로 한글 폰트를 등록해야
# reportlab이 한글을 두부(■)로 그리지 않는다.
SVG_FONT_NAMES = ("Segoe UI", "Malgun Gothic", "sans-serif", "Helvetica")

KOREAN_FONT_CANDIDATES = (
    # (일반, 굵게)
    (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf"),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
     "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
     "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
)

_fonts_ready: bool | None = None


def register_korean_fonts() -> bool:
    """한글이 그려지도록 폰트를 reportlab에 등록한다.

    svglib은 SVG의 font-family 이름을 그대로 reportlab에 넘긴다. 그 이름으로 등록된
    폰트가 없으면 Helvetica로 떨어지고, Helvetica에는 한글 글리프가 없어 ■로 나온다.
    """
    global _fonts_ready
    if _fonts_ready is not None:
        return _fonts_ready

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    regular = bold = None
    for regular_path, bold_path in KOREAN_FONT_CANDIDATES:
        if Path(regular_path).exists():
            regular = regular_path
            bold = bold_path if Path(bold_path).exists() else regular_path
            break

    if regular is None:
        _fonts_ready = False
        return False

    for name in SVG_FONT_NAMES:
        pdfmetrics.registerFont(TTFont(name, regular))
        pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
        pdfmetrics.registerFontFamily(name, normal=name, bold=f"{name}-Bold")

    _fonts_ready = True
    return True


def rasterize(svg_path: Path, out_dir: Path, scale: float = 2.0) -> Path | None:
    """도식 SVG를 PNG로 굽는다.

    티스토리·네이버 에디터는 SVG 업로드를 받아주지 않는 경우가 많다. PNG는 어디서나 된다.
    svglib이 없으면 건너뛰고 None을 돌려준다 (SVG 원본은 그대로 남는다).
    """
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg
    except ImportError:
        return None

    if not register_korean_fonts():
        raise SystemExit(
            "한글 폰트를 찾지 못했다. 이대로 구우면 한글이 ■로 나온다.\n"
            "KOREAN_FONT_CANDIDATES에 쓸 수 있는 폰트 경로를 추가할 것."
        )

    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        return None

    drawing.scale(scale, scale)  # 2배로 구워야 블로그에서 글자가 또렷하다
    drawing.width *= scale
    drawing.height *= scale

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{svg_path.stem}.png"
    renderPM.drawToFile(drawing, str(out_path), fmt="PNG", dpi=72)
    return out_path


def cmd_tistory(args: argparse.Namespace) -> int:
    """티스토리 마크다운 에디터에 그대로 붙여넣을 본문을 만든다."""
    matches = sorted(POSTS_DIR.glob(f"**/*-{args.slug}/index.md"))
    if not matches:
        print(f"posts/**/*-{args.slug}/index.md 를 찾을 수 없다.")
        return 1

    source = matches[-1]
    raw = source.read_text(encoding="utf-8")
    fm_match = FRONTMATTER.match(raw)
    if not fm_match:
        print("프론트매터가 없다.")
        return 1

    meta = yaml.safe_load(fm_match.group(1))
    body = raw[fm_match.end():]

    # 도식 SVG는 티스토리에 따로 업로드해야 한다. 자리에 표식을 남겨 빠뜨리지 않게 한다.
    figures = FIGURE_IMAGE.findall(body)
    body = FIGURE_IMAGE.sub(
        lambda m: f"[[도식 {m.group(2)} — 업로드 후 이 줄을 이미지로 교체]]", body
    )

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out = DIST_DIR / f"{source.parent.name}.md"
    out.write_text(body.lstrip(), encoding="utf-8")

    print(f"변환 완료: {out.relative_to(ROOT)}\n")
    print("--- 티스토리 발행 정보 (에디터에 직접 입력) ---")
    print(f"제목    : {meta['title']}")
    print(f"카테고리: {meta['categories'][0]}")
    print(f"태그    : {','.join(meta['tags'])}")
    print(f"요약    : {meta.get('description', '')}")
    if figures:
        print(f"\n업로드할 도식 {len(figures)}개 (PNG로 구워 둠):")
        missing_converter = False
        for alt_text, rel_path in figures:
            svg_path = source.parent / rel_path
            png_path = rasterize(svg_path, out.parent / source.parent.name)
            if png_path is None:
                missing_converter = True
                print(f"  {svg_path}  (PNG 변환 실패 — SVG 원본)")
            else:
                print(f"  {png_path}")
            print(f"      대체 텍스트: {alt_text}")
        print("  변환본의 [[도식 ...]] 표식 자리에 업로드한 이미지를 넣을 것.")
        if missing_converter:
            print("\n  PNG 변환기가 없다: python -m pip install svglib reportlab")
    if not meta.get("verified"):
        print("\n경고: verified=false. 예제 코드 실행 검증이 끝나지 않았다.")
    return 0


CODE_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
REFERENCE_SECTION = re.compile(r"^## 참고 자료\n.*", re.MULTILINE | re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SOURCE_NOTE = re.compile(r"^> \*\*[^*]*근거\*\*", re.MULTILINE)

BODY_MIN_CHARS = 1800
BODY_MAX_CHARS = 3500


def body_length(text: str) -> int:
    """읽는 분량만 센다.

    프론트매터·코드블록·표·인용(출처)·참고 자료·링크 URL은 읽는 분량이 아니므로 제외한다.
    """
    body = FRONTMATTER.sub("", text)
    body = REFERENCE_SECTION.sub("", body)
    body = CODE_FENCE.sub("", body)
    body = "\n".join(
        line for line in body.splitlines()
        if not line.startswith(("|", ">", "!["))
    )
    body = MARKDOWN_LINK.sub(r"\1", body)  # 링크는 표시 텍스트만 남긴다
    return len(re.sub(r"\s", "", body))


HAS_VERSION_NUMBER = re.compile(r"\d")
MANUAL_ONLY_NOTICE = "실행 검증 없음"


def lint_versions(meta: dict, text: str) -> list[str]:
    """버전 명시와 검증 방식 표기를 검사한다.

    독자가 "내 버전에서도 그런가"를 판단할 수 있어야 하므로 버전은 필수다.
    """
    problems: list[str] = []

    environment = meta.get("environment") or []
    if not environment:
        problems.append("environment가 비어 있다 — 쓴 도구·DB의 버전을 명시할 것")
    for item in environment:
        if not HAS_VERSION_NUMBER.search(str(item)):
            problems.append(f'environment "{item}"에 버전 숫자가 없다')

    verification = meta.get("verification")
    if verification not in ("executed", "manual-only"):
        problems.append(
            f"verification이 executed/manual-only가 아니다: {verification!r}"
        )
    elif verification == "manual-only" and MANUAL_ONLY_NOTICE not in text:
        problems.append(
            f'verification: manual-only인데 본문에 "{MANUAL_ONLY_NOTICE}" 안내가 없다'
        )

    if meta.get("product"):
        version = str(meta.get("product_version") or "")
        if not version:
            problems.append("product는 있는데 product_version이 없다")
        elif not HAS_VERSION_NUMBER.search(version):
            problems.append(f'product_version "{version}"에 버전 숫자가 없다')
        if version and version not in meta.get("title", ""):
            problems.append(f'제목에 제품 버전("{version}")이 드러나지 않는다')

    return problems


def lint_related(meta: dict, path: Path, text: str) -> list[str]:
    """같은 feature 글이 이미 있으면 상호 링크가 들어 있어야 한다."""
    feature = meta.get("feature")
    if not feature:
        return []

    siblings = [
        entry for entry in published_index().get(feature, [])
        if entry["path"] != path
    ]
    if not siblings:
        return []
    if not RELATED_BLOCK.search(text):
        names = ", ".join(e["title"] for e in siblings)
        return [
            f"같은 기능({feature})의 글이 있는데 관련 글 블록이 없다 "
            f"— blog.py relink 실행 필요 (대상: {names})"
        ]
    return []


def lint_post(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    fm_match = FRONTMATTER.match(text)
    if not fm_match:
        return ["프론트매터가 없다"]
    meta = yaml.safe_load(fm_match.group(1))

    if not meta.get("verified"):
        problems.append("verified: false — 검증이 끝나지 않았다")
    if not meta.get("description"):
        problems.append("description이 비어 있다")

    problems += lint_versions(meta, text)
    problems += lint_related(meta, path, text)

    track = track_of(meta)
    low, high = BODY_CHARS_BY_TRACK[track]
    chars = body_length(text)
    if not low <= chars <= high:
        problems.append(f"본문 {chars:,}자 ({track} 기준 {low:,}~{high:,})")

    # 코드 블록 안의 마크다운 예시는 실제 도식·링크가 아니므로 제외한다
    linkable = CODE_FENCE.sub("", text)

    figures = FIGURE_IMAGE.findall(linkable)
    if not figures:
        problems.append("도식이 없다 (최소 1개)")
    source_count = len(SOURCE_NOTE.findall(linkable))
    if source_count < len(figures):
        problems.append(f"도식 {len(figures)}개인데 출처 표기는 {source_count}개")
    if "```mermaid" in text:
        problems.append("mermaid 블록이 남아 있다 (SVG로 바꿀 것)")

    for link in re.findall(r"\]\((?!https?:)([^)#]+)\)", linkable):
        if not (path.parent / link).exists():
            problems.append(f"깨진 링크: {link}")

    return problems


def cmd_lint(args: argparse.Namespace) -> int:
    targets = sorted(POSTS_DIR.glob("**/index.md"))
    if args.slug:
        targets = [p for p in targets if args.slug in p.parent.name]
    if not targets:
        print("검사할 글이 없다.")
        return 1

    failed = 0
    for path in targets:
        rel = path.parent.relative_to(POSTS_DIR)
        problems = lint_post(path)
        if problems:
            failed += 1
            print(f"[NG] {rel}")
            for problem in problems:
                print(f"     - {problem}")
        else:
            print(f"[OK] {rel}  본문 {body_length(path.read_text(encoding='utf-8')):,}자")
    return 1 if failed else 0


INDEX_PATH = ROOT / "POSTS.md"

VERIFICATION_LABEL = {
    "executed": "실행 검증",
    "manual-only": "문서 근거",
}


def cmd_index(args: argparse.Namespace) -> int:
    """글 목록 페이지를 다시 만든다.

    글이 카테고리 폴더 여러 단계 아래에 흩어져 있어 폴더를 헤집지 않고는 볼 수가 없다.
    GitHub에서 바로 눌러 들어갈 수 있는 목록을 한 장으로 만든다.
    """
    entries: list[dict] = []
    for path in POSTS_DIR.glob("**/index.md"):
        meta = read_meta(path)
        if not meta:
            continue
        entries.append({"meta": meta, "path": path})

    if not entries:
        print("아직 작성된 글이 없다.")
        return 1

    entries.sort(key=lambda e: (str(e["meta"].get("date", "")), e["path"].parent.name),
                 reverse=True)

    today = dt.date.today().isoformat()
    lines = [
        "# 글 목록\n\n",
        f"총 **{len(entries)}편** · 갱신 {today}\n\n",
        "> 이 파일은 `python scripts/blog.py index`가 생성한다. 직접 고치지 말 것.\n\n",
    ]

    for track in TRACKS:
        group = [e for e in entries if track_of(e["meta"]) == track]
        if not group:
            continue
        lines.append(f"## {TRACK_LABEL[track]} ({track}) — {len(group)}편\n\n")
        lines.append("| 날짜 | 제목 | 난이도 | 환경 | 검증 |\n")
        lines.append("|---|---|---|---|---|\n")
        for entry in group:
            meta, path = entry["meta"], entry["path"]
            link = path.relative_to(ROOT).as_posix()
            environment = ", ".join(meta.get("environment") or []) or "—"
            verification = VERIFICATION_LABEL.get(
                meta.get("verification"), meta.get("verification") or "—"
            )
            if not meta.get("verified"):
                verification += " (미완)"
            lines.append(
                f"| {meta.get('date', '')} | [{meta.get('title', path.parent.name)}]({link}) "
                f"| {meta.get('difficulty', '')} | {environment} | {verification} |\n"
            )
        lines.append("\n")

    # 같은 기능을 여러 환경에서 다룬 글 묶음
    index = published_index()
    crossing = {f: e for f, e in index.items() if len(e) > 1}
    if crossing:
        lines.append("## 같은 기능을 여러 환경에서 다룬 글\n\n")
        for feature, group in sorted(crossing.items()):
            lines.append(f"**`{feature}`**\n\n")
            for entry in group:
                link = entry["path"].relative_to(ROOT).as_posix()
                origin = entry["product"] or entry["environment"] or "—"
                lines.append(f"- [{entry['title']}]({link}) — {origin}\n")
            lines.append("\n")

    INDEX_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"생성: {INDEX_PATH.relative_to(ROOT)} ({len(entries)}편)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    data = load_backlog()
    topics = data["topics"]
    by_status: dict[str, int] = {}
    for topic in topics:
        by_status[topic["status"]] = by_status.get(topic["status"], 0) + 1

    core_done, general_done = count_published(topics)
    total_done = core_done + general_done
    ratio = core_done / total_done if total_done else 0.0

    plan = daily_plan(data)
    total_per_day = sum(plan.values())
    print(f"백로그   : 전체 {len(topics)}편 (하루 {total_per_day}편 기준)")
    for status in ("todo", "writing", "done"):
        print(f"  {status:8s} {by_status.get(status, 0)}")

    print("\n트랙별 잔량")
    for track, need in plan.items():
        remaining = sum(
            1 for t in topics if t["status"] == "todo" and track_of(t) == track
        )
        flag = "  ← 보충 필요" if remaining <= data["meta"]["low_watermark"] else ""
        print(f"  {track:8s} todo {remaining:3d}개 · 하루 {need}편 → 약 "
              f"{remaining // need if need else 0}일분{flag}")

    print(
        f"\n일반 트랙 비율: core {core_done} / general {general_done} "
        f"= {ratio:.0%} (목표 {data['meta']['target_ratio']['core']:.0%})"
    )

    manual_only = 0
    unverified = []
    for path in sorted(POSTS_DIR.glob("**/index.md")):
        meta = read_meta(path) or {}
        if not meta.get("verified"):
            unverified.append(path)
        if meta.get("verification") == "manual-only":
            manual_only += 1

    if manual_only:
        print(f"\n실행 검증 없는 글: {manual_only}편 "
              f"(실행 환경이 있는 곳에서 `blog.py lint` 후 executed로 승격 가능)")
    if unverified:
        print(f"\n미검증 글 {len(unverified)}편:")
        for path in unverified:
            print(f"  {path.parent.relative_to(POSTS_DIR)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="기술 블로그 운영 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    composition = " + ".join(f"{t} {n}" for t, n in PLAN_WITH_BASICS.items())
    p_pick = sub.add_parser("pick", help=f"오늘 쓸 주제 선정 ({composition})")
    for track, need in PLAN_WITH_BASICS.items():
        p_pick.add_argument(f"--{track}", type=int, help=f"기본 {need}")
    p_pick.set_defaults(func=cmd_pick)

    p_related = sub.add_parser("related", help="같은 feature로 쓴 글 목록")
    p_related.add_argument("feature", nargs="?", help="생략하면 전체 feature")
    p_related.set_defaults(func=cmd_related)

    p_relink = sub.add_parser("relink", help="같은 feature 글끼리 상호 링크 블록 재생성")
    p_relink.set_defaults(func=cmd_relink)

    p_new = sub.add_parser("new", help="글 폴더 스캐폴딩")
    p_new.add_argument("topic_id")
    p_new.add_argument("slug", help="영문 소문자 slug")
    p_new.set_defaults(func=cmd_new)

    p_done = sub.add_parser("done", help="발행 완료 처리")
    p_done.add_argument("topic_id")
    p_done.set_defaults(func=cmd_done)

    p_tistory = sub.add_parser("tistory", help="티스토리용 변환")
    p_tistory.add_argument("slug")
    p_tistory.set_defaults(func=cmd_tistory)

    p_lint = sub.add_parser("lint", help="글 규칙 검사 (길이·도식·출처·링크·검증)")
    p_lint.add_argument("slug", nargs="?", help="생략하면 전체 검사")
    p_lint.set_defaults(func=cmd_lint)

    p_index = sub.add_parser("index", help="글 목록 페이지(POSTS.md) 재생성")
    p_index.set_defaults(func=cmd_index)

    p_status = sub.add_parser("status", help="백로그/발행 현황")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
