"""권한 프롬프트 앞에서 멈춘 회차를 찾는다.

멈춘 세션은 겉으로 `status: running` 이라 정상 수행과 구분되지 않는다. 구분되는 것은
**마지막 도구 호출에 결과가 돌아왔는지**다. 결과 없이 시간이 지나면 사람이 승인해 주기를
기다리는 중이다.

전사 기록은 ~/.claude/projects/<경로를 -로 바꾼 이름>/*.jsonl 에 쌓인다.
승인은 대신해 줄 수 없다. 무엇 때문에 멈췄는지만 짚어 준다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TASK_IDS = ("tech-blog-daily", "tech-blog-exam", "tech-blog-concept", "tech-blog-healthcheck")
URL_IN_INPUT = re.compile(r"https?://([^/\s\"']+)")


def transcript_dir(repo: Path) -> Path:
    """저장소 경로를 Claude Code 가 쓰는 폴더 이름으로 바꾼다.

    D:\\workspace\\claude\\tech_blog -> D--workspace-claude-tech-blog
    """
    override = os.environ.get("CLAUDE_PROJECTS_DIR")
    if override:
        return Path(override)
    slug = re.sub(r"[:\\/_]", "-", str(repo.resolve()))
    return Path.home() / ".claude" / "projects" / slug


def pending_call(rows: list[dict]) -> tuple[str, dict] | None:
    """결과가 돌아오지 않은 마지막 도구 호출."""
    last, done = None, set()
    for row in rows:
        message = row.get("message") or {}
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") == "tool_use":
                last = (block["id"], block["name"], block.get("input") or {})
            elif block.get("type") == "tool_result":
                done.add(block.get("tool_use_id"))
    if last and last[0] not in done:
        return last[1], last[2]
    return None


def owning_task(rows: list[dict]) -> str:
    """전사 앞부분에 스케줄 작업 이름이 들어 있다."""
    head = json.dumps(rows[:6], ensure_ascii=False)
    for task_id in TASK_IDS:
        if task_id in head:
            return task_id
    return "(수동 세션)"


def summarize(tool: str, payload: dict) -> str:
    if tool == "WebFetch":
        host = URL_IN_INPUT.search(str(payload.get("url", "")))
        return f"{payload.get('url', '')[:70]}  ← 도메인 승인 필요: {host.group(1) if host else '?'}"
    if tool == "Bash":
        return str(payload.get("command", ""))[:120]
    return json.dumps(payload, ensure_ascii=False)[:120]


def main() -> int:
    parser = argparse.ArgumentParser(description="멈춘 회차 찾기")
    parser.add_argument("--repo", default=".", help="저장소 경로")
    parser.add_argument("--idle-minutes", type=int, default=15,
                        help="이 시간 넘게 결과가 없으면 멈춘 것으로 본다")
    args = parser.parse_args()

    folder = transcript_dir(Path(args.repo))
    if not folder.is_dir():
        raise SystemExit(f"전사 폴더를 찾지 못했다: {folder}")

    cutoff = time.time() - args.idle_minutes * 60
    stuck = []
    for path in folder.glob("*.jsonl"):
        if path.stat().st_mtime > cutoff:
            continue  # 아직 움직이고 있다 (검사 세션 자신도 여기서 걸러진다)
        if path.stat().st_mtime < time.time() - 12 * 3600:
            continue  # 하루 지난 것은 이미 끝난 세션이다
        try:
            rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        except (OSError, json.JSONDecodeError):
            continue
        call = pending_call(rows)
        if not call:
            continue
        idle = int((time.time() - path.stat().st_mtime) / 60)
        stuck.append((owning_task(rows), idle, call[0], summarize(*call), path.name))

    if not stuck:
        print(f"멈춘 회차 없음 ({args.idle_minutes}분 기준)")
        return 0

    print(f"멈춰 있는 회차 {len(stuck)}건 — 승인을 기다리는 중이다\n")
    for task_id, idle, tool, detail, name in sorted(stuck, key=lambda s: -s[1]):
        print(f"  [{task_id}] {idle}분째 대기")
        print(f"      도구: {tool}")
        print(f"      내용: {detail}")
        print(f"      전사: {name}")
    print("\n승인은 대신할 수 없다. 해당 세션을 열어 수락하면 이어서 돈다.")
    print("같은 도메인이 반복되면 .claude/settings.json 의 allow 에")
    print('"WebFetch(domain:...)" 를 넣어 두면 다음부터 묻지 않는다.')
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
