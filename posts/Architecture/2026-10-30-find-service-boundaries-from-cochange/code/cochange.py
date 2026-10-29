"""커밋 이력에서 함께 바뀌는 파일을 묶어 모듈 경계를 추정한다.

진짜 git 저장소를 임시 폴더에 만들어 정해 둔 이력을 커밋한 뒤,
`git log --name-only` 를 읽어 동시 변경 횟수를 센다. 저장소 이력은 가상이지만
집계와 군집화는 실제로 수행한 결과다.
"""

import itertools
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

# (커밋 메시지, 그 커밋이 건드린 파일) — 주문·배송·청구 세 갈래로 나눈 가상 서비스.
# 폴더는 셋인데 실제로 함께 바뀌는 묶음은 다르다는 것을 보이려고 짠 이력이다.
HISTORY = [
    ("주문 생성 API 추가", ["order/api.py", "order/service.py", "order/model.py", "common/config.py"]),
    ("주문 상태 전이 수정", ["order/api.py", "order/service.py"]),
    ("주문 취소 사유 컬럼", ["order/service.py", "order/model.py", "common/config.py"]),
    ("주문 확정 시 청구서 발행", ["order/api.py", "order/service.py", "billing/invoice.py"]),
    ("청구서 금액 반올림", ["order/service.py", "billing/invoice.py", "common/config.py"]),
    ("주문 목록 정렬", ["order/api.py", "order/model.py"]),
    ("부분 취소 시 청구서 조정", ["order/service.py", "billing/invoice.py", "common/config.py"]),
    ("주문 검증 규칙 보강", ["order/api.py", "order/service.py", "order/model.py"]),
    ("배송 접수 API", ["shipping/api.py", "shipping/service.py", "common/config.py"]),
    ("운송장 번호 채번", ["shipping/service.py", "shipping/tracking.py"]),
    ("배송 상태 조회", ["shipping/api.py", "shipping/service.py", "shipping/tracking.py", "common/config.py"]),
    ("배송 지연 알림", ["shipping/service.py", "shipping/tracking.py", "common/config.py"]),
    ("배송지 변경 허용", ["shipping/api.py", "shipping/service.py"]),
    ("운송장 재발급", ["shipping/service.py", "shipping/tracking.py"]),
    ("결제 수단 추가", ["billing/invoice.py", "billing/payment.py", "common/config.py"]),
    ("결제 실패 재시도", ["billing/payment.py", "common/config.py"]),
    ("결제 취소 처리", ["billing/invoice.py", "billing/payment.py", "common/config.py"]),
    ("결제 로그 보강", ["billing/payment.py"]),
    ("청구서 발행 시점 변경", ["order/service.py", "billing/invoice.py"]),
    ("타임아웃 기본값 조정", ["common/config.py", "order/api.py"]),
    ("재시도 횟수 조정", ["common/config.py", "shipping/api.py"]),
    ("커넥션 풀 크기 조정", ["common/config.py", "billing/payment.py"]),
    ("주문 벌크 생성", ["order/api.py", "order/service.py", "order/model.py"]),
    ("배송 묶음 처리", ["shipping/api.py", "shipping/service.py", "shipping/tracking.py"]),
    ("청구서 재발행", ["order/service.py", "billing/invoice.py"]),
    ("배송 API 응답 규격 변경", ["shipping/service.py", "shipping/api.py"]),
]

GIT_IDENTITY = [
    "-c", "user.name=example",
    "-c", "user.email=example@example.invalid",
    "-c", "commit.gpgsign=false",
]


def build_repository(root: Path) -> None:
    """정해 둔 이력을 실제 커밋으로 만든다."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for message, paths in HISTORY:
        for path in paths:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            # 내용은 중요하지 않다. 커밋에 그 파일이 들어갔다는 사실만 센다.
            with target.open("a", encoding="utf-8") as fp:
                fp.write(f"# {message}\n")
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), *GIT_IDENTITY, "commit", "-q", "-m", message],
            check=True,
        )


def read_commits(root: Path) -> list[set[str]]:
    """git log --name-only 를 읽어 커밋마다 바뀐 파일 집합을 만든다."""
    out = subprocess.run(
        ["git", "-C", str(root), "log", "--name-only", "--pretty=format:%x00"],
        check=True, capture_output=True, text=True,
    ).stdout
    commits = []
    for block in out.split("\x00"):
        files = {line.strip() for line in block.splitlines() if line.strip()}
        if files:
            commits.append(files)
    return commits


def count_changes(commits):
    """파일별 변경 횟수와 파일 쌍의 동시 변경 횟수를 센다."""
    changes = Counter()
    together = Counter()
    for files in commits:
        changes.update(files)
        for left, right in itertools.combinations(sorted(files), 2):
            together[(left, right)] += 1
    return changes, together


def jaccard(changes, together, pair):
    """동시 변경 횟수를 둘 중 하나라도 바뀐 커밋 수로 나눈다."""
    both = together[pair]
    either = changes[pair[0]] + changes[pair[1]] - both
    return both / either


def components(nodes, edges):
    """이어진 파일들을 하나의 묶음으로 모은다 (연결 요소)."""
    neighbor = defaultdict(set)
    for left, right in edges:
        neighbor[left].add(right)
        neighbor[right].add(left)

    seen, groups = set(), []
    for node in sorted(nodes):
        if node in seen:
            continue
        stack, group = [node], []
        seen.add(node)
        while stack:
            current = stack.pop()
            group.append(current)
            for other in neighbor[current] - seen:
                seen.add(other)
                stack.append(other)
        groups.append(sorted(group))
    return groups


def print_groups(groups):
    for index, group in enumerate(groups, start=1):
        print(f"  묶음 {index}: {', '.join(group)}")


def main():
    root = Path(tempfile.mkdtemp(prefix="cochange-"))
    try:
        build_repository(root)
        commits = read_commits(root)
        changes, together = count_changes(commits)

        print("=" * 64)
        print("1. 집계 대상")
        print("=" * 64)
        print(f"  커밋 {len(commits)}개 · 파일 {len(changes)}개")
        print("\n  파일별 변경 횟수")
        for name, count in sorted(changes.items()):
            print(f"    {name:24} {count:3}")

        print("\n" + "=" * 64)
        print("2. 동시 변경 횟수 상위 10쌍")
        print("=" * 64)
        ranked = sorted(together.items(), key=lambda kv: (-kv[1], kv[0]))
        print(f"  {'파일 쌍':54} {'동시':>4} {'자카드':>7}")
        for (left, right), count in ranked[:10]:
            score = jaccard(changes, together, (left, right))
            print(f"  {left + ' + ' + right:54} {count:4} {score:7.3f}")

        print("\n" + "=" * 64)
        print("3. 동시 변경 횟수만으로 묶으면")
        print("=" * 64)
        for threshold in (3, 4):
            edges = [pair for pair, count in together.items() if count >= threshold]
            groups = components(changes, edges)
            print(f"\n  동시 변경 {threshold}회 이상 — 묶음 {len(groups)}개")
            print_groups(groups)

        print("\n" + "=" * 64)
        print("4. 자카드 계수로 묶으면")
        print("=" * 64)
        for threshold in (0.3, 0.4):
            edges = [
                pair for pair in together
                if jaccard(changes, together, pair) >= threshold
            ]
            groups = components(changes, edges)
            print(f"\n  자카드 {threshold} 이상 — 묶음 {len(groups)}개")
            print_groups(groups)

        print("\n" + "=" * 64)
        print("5. 폴더 경계와 어긋나는 쌍")
        print("=" * 64)
        print(f"  {'파일 쌍':54} {'동시':>4} {'자카드':>7}")
        for pair in sorted(together):
            left, right = pair
            if left.split("/")[0] == right.split("/")[0]:
                continue
            score = jaccard(changes, together, pair)
            if score >= 0.3:
                print(f"  {left + ' + ' + right:54} {together[pair]:4} {score:7.3f}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
