#!/usr/bin/env python3
"""기술 블로그 운영 CLI.

사용법:
    python scripts/blog.py pick              # 오늘 쓸 주제 2개 선정
    python scripts/blog.py new <id> <slug>   # 글 폴더 스캐폴딩
    python scripts/blog.py done <id>         # 주제를 done으로 표시하고 이력 기록
    python scripts/blog.py tistory <slug>    # 티스토리 붙여넣기용 변환
    python scripts/blog.py lint              # 글 규칙 검사
    python scripts/blog.py status            # 백로그 잔량과 발행 현황
"""

from __future__ import annotations

import argparse
import datetime as dt
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

CORE_CATEGORIES = {"Database", "Backend", "Performance"}
POSTS_PER_DAY = 2


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


def pick_topics(data: dict, count: int = POSTS_PER_DAY) -> list[dict]:
    """누적 발행 비율이 목표(core 60%)에 가까워지도록 탐욕적으로 고른다."""
    topics = data["topics"]
    target_core = data["meta"]["target_ratio"]["core"]
    core_done, general_done = count_published(topics)

    available = [t for t in topics if t["status"] == "todo"]
    picked: list[dict] = []

    for _ in range(min(count, len(available))):
        core_pool = [t for t in available if is_core(t) and t not in picked]
        general_pool = [t for t in available if not is_core(t) and t not in picked]

        total = core_done + general_done + len(picked)
        current_core = core_done + sum(1 for t in picked if is_core(t))
        # 다음 한 편을 core로 뽑았을 때와 general로 뽑았을 때의 목표 이탈도를 비교
        gap_if_core = abs((current_core + 1) / (total + 1) - target_core)
        gap_if_general = abs(current_core / (total + 1) - target_core)

        prefer_core = gap_if_core <= gap_if_general
        pool = (core_pool or general_pool) if prefer_core else (general_pool or core_pool)
        picked.append(pool[0])

    return picked


def cmd_pick(args: argparse.Namespace) -> int:
    data = load_backlog()
    picked = pick_topics(data, args.count)
    if not picked:
        print("백로그에 todo 주제가 없다. topics/backlog.yaml을 보충할 것.")
        return 1

    today = dt.date.today().isoformat()
    print(f"# {today} 작성 대상 {len(picked)}편\n")
    for i, topic in enumerate(picked, 1):
        area = topic["category"]
        if topic.get("subcategory"):
            area += f"/{topic['subcategory']}"
        print(f"[{i}] {topic['id']} · {area} · {topic['difficulty']}")
        print(f"    제목: {topic['title']}")
        print(f"    각도: {topic['angle']}")
        print(f"    예제: {topic['code']}  태그: {', '.join(topic['tags'])}")
        print()

    remaining = sum(1 for t in data["topics"] if t["status"] == "todo")
    if remaining <= data["meta"]["low_watermark"]:
        print(f"경고: todo 주제가 {remaining}개 남았다. 백로그를 보충할 것.")
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
    tags = ", ".join(topic["tags"])
    index_md = f"""---
title: "{topic['title']}"
date: {today.isoformat()}
categories: [{topic["category"]}]
subcategory: {topic.get("subcategory") or ""}
tags: [{tags}]
description: ""
difficulty: {topic['difficulty']}
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


FIGURE_IMAGE = re.compile(r"!\[([^\]]*)\]\((fig/[^)]+)\)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


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
        print(f"\n업로드할 도식 {len(figures)}개:")
        for alt_text, rel_path in figures:
            print(f"  {source.parent / rel_path}")
            print(f"      대체 텍스트: {alt_text}")
        print("  변환본의 [[도식 ...]] 표식 자리에 업로드한 이미지를 넣을 것.")
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


def lint_post(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    fm_match = FRONTMATTER.match(text)
    if not fm_match:
        return ["프론트매터가 없다"]
    meta = yaml.safe_load(fm_match.group(1))

    if not meta.get("verified"):
        problems.append("verified: false — 예제 검증이 끝나지 않았다")
    if not meta.get("description"):
        problems.append("description이 비어 있다")

    chars = body_length(text)
    if not BODY_MIN_CHARS <= chars <= BODY_MAX_CHARS:
        problems.append(f"본문 {chars:,}자 (기준 {BODY_MIN_CHARS:,}~{BODY_MAX_CHARS:,})")

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


def cmd_status(args: argparse.Namespace) -> int:
    data = load_backlog()
    topics = data["topics"]
    by_status: dict[str, int] = {}
    for topic in topics:
        by_status[topic["status"]] = by_status.get(topic["status"], 0) + 1

    core_done, general_done = count_published(topics)
    total_done = core_done + general_done
    ratio = core_done / total_done if total_done else 0.0
    todo = by_status.get("todo", 0)

    print(f"백로그   : 전체 {len(topics)}편")
    for status in ("todo", "writing", "done"):
        print(f"  {status:8s} {by_status.get(status, 0)}")
    print(f"남은 일수: 약 {todo // POSTS_PER_DAY}일 (하루 {POSTS_PER_DAY}편 기준)")
    print(
        f"비율     : core {core_done} / general {general_done} "
        f"= {ratio:.0%} (목표 {data['meta']['target_ratio']['core']:.0%})"
    )
    unverified = [
        p for p in POSTS_DIR.glob("**/index.md")
        if "verified: true" not in p.read_text(encoding="utf-8")
    ]
    if unverified:
        print(f"\n미검증 글 {len(unverified)}편:")
        for path in unverified:
            print(f"  {path.parent.relative_to(POSTS_DIR)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="기술 블로그 운영 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pick = sub.add_parser("pick", help="오늘 쓸 주제 선정")
    p_pick.add_argument("-n", "--count", type=int, default=POSTS_PER_DAY)
    p_pick.set_defaults(func=cmd_pick)

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

    p_status = sub.add_parser("status", help="백로그/발행 현황")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
