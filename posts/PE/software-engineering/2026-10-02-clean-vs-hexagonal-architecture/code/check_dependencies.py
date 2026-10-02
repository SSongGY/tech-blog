"""'의존성 방향을 뒤집는다'를 코드로 확인한다.

1. 두 설계의 import 문을 ast 로 뽑아 소스 코드 의존 방향을 찍는다
2. 실행 중 호출 방향을 기록해 import 방향과 반대인지 본다
3. 유스케이스를 고치지 않고 어댑터만 바꿔 끼운다
"""

import ast
import inspect
import sys
from pathlib import Path

HERE = Path(__file__).parent
# 동심원 안쪽일수록 작은 수. SQL 은 어댑터 층에만 있어야 하므로 sqlite3 를 어댑터와 같은 층에 둔다
RING = {"domain": 0, "adapters": 1, "main": 2, "order_service": 0, "sqlite3": 1}


def imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return [n for n in names if n in RING]


def show_dependencies(label: str, folder: Path) -> None:
    print(f"\n[{label}]")
    violations = 0
    for path in sorted(folder.glob("*.py")):
        module = path.stem
        for target in imports_of(path):
            outward = RING[target] > RING[module]
            violations += outward
            if outward:
                arrow = "바깥으로 (규칙 위반)"
            else:
                arrow = "안쪽으로" if RING[target] < RING[module] else "같은 층"
            print(f"  {module:<14} -> {target:<10} {arrow}")
    print(f"  바깥을 향한 의존: {violations}개")


class RecordingRepository:
    """누가 자신을 불렀는지 기록하는 어댑터."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _record(self, method: str) -> None:
        caller = inspect.stack()[2].frame.f_globals["__name__"]
        callee = f"{type(self).__module__}.{type(self).__name__}.{method}"
        self.calls.append(f"{caller} -> {callee}")

    def next_id(self) -> int:
        self._record("next_id")
        return 1

    def save(self, order) -> None:
        self._record("save")


def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    show_dependencies("1-A 계층형 (before)", HERE / "before")
    show_dependencies("1-B 포트와 어댑터 (after)", HERE / "after")

    sys.path.insert(0, str(HERE / "after"))
    from domain import PlaceOrder  # 경로를 잡은 뒤에야 import 할 수 있다
    import main as composition_root

    print("\n[2 실행 중 호출 방향]")
    repository = RecordingRepository()
    PlaceOrder(repository).execute(5000)
    for call in repository.calls:
        print(f"  {call}")

    print("\n[3 어댑터만 바꿔 끼운다 — PlaceOrder 는 그대로]")
    composition_root.run("InMemoryOrderRepository",
                         PlaceOrder(composition_root.InMemoryOrderRepository()))
    composition_root.run("SqliteOrderRepository",
                         PlaceOrder(composition_root.SqliteOrderRepository(":memory:")))


if __name__ == "__main__":
    main()
