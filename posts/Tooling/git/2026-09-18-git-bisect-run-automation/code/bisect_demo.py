"""git bisect run이 버그 유입 커밋을 몇 단계 만에 찾는지 실제로 돌려 확인한다.

임시 저장소에 커밋 64개를 만들고, 그중 하나에 퍼센타일 계산 버그를 심는다.
일부 커밋은 일부러 import조차 되지 않게 만들어 exit 125(skip) 처리를 함께 확인한다.

실행:
    python bisect_demo.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOTAL_COMMITS = 64
BUG_COMMIT_INDEX = 41      # 이 커밋에서 percentile 구현이 잘못된 버전으로 바뀐다
# import 자체가 깨져 테스트할 수 없는 커밋.
# bisect가 실제로 밟는 지점에 심어야 skip(125) 경로가 동작하는 걸 확인할 수 있다.
BROKEN_COMMIT_INDEXES = (39, 43, 47)

GOOD_PERCENTILE = '''\
import math


def percentile(sorted_values, q):
    """q번째 퍼센타일. 빈 리스트는 호출하지 않는다고 가정한다."""
    if not sorted_values:
        raise ValueError("빈 입력")
    rank = math.ceil(len(sorted_values) * q / 100)
    return sorted_values[max(rank - 1, 0)]
'''

BAD_PERCENTILE = '''\
import math


def percentile(sorted_values, q):
    """q번째 퍼센타일. 빈 리스트는 호출하지 않는다고 가정한다."""
    if not sorted_values:
        raise ValueError("빈 입력")
    rank = int(len(sorted_values) * q / 100)
    return sorted_values[rank]
'''

BROKEN_SOURCE = "def percentile(sorted_values, q)\n    return None\n"  # 콜론 누락

CHECK_SCRIPT = '''\
"""git bisect run이 호출하는 판정 스크립트.

종료 코드 규약:
    0   = good  (버그 없음)
    1   = bad   (버그 있음)
    125 = skip  (판정 불가 — 빌드/임포트 실패)
"""

import sys

sys.path.insert(0, ".")

try:
    import stats
except SyntaxError:
    sys.exit(125)

try:
    assert stats.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 50) == 5
    assert stats.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 100) == 10
except (AssertionError, IndexError):
    sys.exit(1)

sys.exit(0)
'''


def git(repo_dir: Path, *args: str) -> str:
    """저장소에 git 명령을 실행하고 표준 출력을 돌려준다."""
    completed = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 and "bisect" not in args:
        raise RuntimeError(f"git {' '.join(args)} 실패:\n{completed.stderr}")
    return completed.stdout


def source_for(commit_index: int) -> str:
    if commit_index in BROKEN_COMMIT_INDEXES:
        return BROKEN_SOURCE
    return BAD_PERCENTILE if commit_index >= BUG_COMMIT_INDEX else GOOD_PERCENTILE


def build_repo(repo_dir: Path) -> list[str]:
    """커밋 64개짜리 저장소를 만들고 각 커밋 해시를 순서대로 돌려준다."""
    repo_dir.mkdir(parents=True)
    git(repo_dir, "init", "--quiet", "--initial-branch", "main")
    git(repo_dir, "config", "user.email", "demo@example.com")
    git(repo_dir, "config", "user.name", "bisect demo")

    commit_hashes = []
    for commit_index in range(TOTAL_COMMITS):
        (repo_dir / "stats.py").write_text(source_for(commit_index), encoding="utf-8")
        # 커밋마다 내용이 실제로 바뀌도록 무관한 파일도 함께 건드린다
        (repo_dir / "CHANGELOG.md").write_text(
            f"# 변경 이력\n\n- r{commit_index:03d} 수정\n", encoding="utf-8"
        )
        git(repo_dir, "add", ".")
        git(repo_dir, "commit", "--quiet", "-m", f"r{commit_index:03d}: 일상적인 수정")
        commit_hashes.append(git(repo_dir, "rev-parse", "HEAD").strip())
    return commit_hashes


def run_bisect(repo_dir: Path, check_script: Path, good_hash: str) -> tuple[str, int]:
    """git bisect run을 돌리고 (찾은 커밋 해시, 테스트 횟수)를 돌려준다."""
    git(repo_dir, "bisect", "start")
    git(repo_dir, "bisect", "bad", "HEAD")
    git(repo_dir, "bisect", "good", good_hash)

    completed = subprocess.run(
        ["git", "-C", str(repo_dir), "bisect", "run",
         sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout + completed.stderr
    print(output.rstrip())

    found = re.search(r"([0-9a-f]{40}) is the first bad commit", output)
    # "Bisecting:" 줄은 다음 후보를 고를 때만 찍힌다. 실제 테스트 횟수는
    # git이 스크립트를 실행할 때마다 남기는 "running" 줄로 센다.
    step_count = len(re.findall(r"^running ", output, re.MULTILINE))
    git(repo_dir, "bisect", "reset")

    if not found:
        raise RuntimeError("first bad commit을 찾지 못했다")
    return found.group(1), step_count


def main() -> None:
    workspace = Path(tempfile.mkdtemp(prefix="bisect_demo_"))
    repo_dir = workspace / "repo"
    check_script = workspace / "check_commit.py"  # 저장소 밖에 둬야 체크아웃에 지워지지 않는다

    try:
        commit_hashes = build_repo(repo_dir)
        check_script.write_text(CHECK_SCRIPT, encoding="utf-8")

        expected_hash = commit_hashes[BUG_COMMIT_INDEX]
        print(f"커밋 {TOTAL_COMMITS}개 생성 · 버그 유입 지점 r{BUG_COMMIT_INDEX:03d} "
              f"({expected_hash[:8]})")
        print(f"판정 불가 커밋: {', '.join(f'r{i:03d}' for i in BROKEN_COMMIT_INDEXES)}")
        print(f"이론상 필요한 테스트 횟수: 약 log2({TOTAL_COMMITS}) = 6회\n")
        print("-" * 70)

        found_hash, step_count = run_bisect(repo_dir, check_script, commit_hashes[0])

        print("-" * 70)
        print(f"찾은 커밋   : {found_hash[:8]}")
        print(f"실제 버그   : {expected_hash[:8]}")
        print(f"일치 여부   : {'일치' if found_hash == expected_hash else '불일치'}")
        print(f"테스트 횟수 : {step_count}회 (전수 조사라면 {TOTAL_COMMITS}회)")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    main()
