"""버퍼에만 있던 내용이 프로세스와 함께 사라지는지 확인하는 자식 프로세스.

부모가 두 번 띄운다. 한 번은 flush 없이, 한 번은 flush 를 넣고.
둘 다 파일을 닫지 않고 os._exit 로 즉사하므로 파이썬의 정리 절차가 돌지 않는다.
"""

from __future__ import annotations

import os
import sys

LINES = 500


def main() -> None:
    path = sys.argv[1]
    do_flush = sys.argv[2] == "flush"

    handle = open(path, "w", encoding="utf-8")
    for i in range(LINES):
        handle.write(f"line {i:04d}\n")
        if do_flush:
            handle.flush()
    # close 도 flush 도 거치지 않고 즉사한다. atexit·__del__ 전부 건너뛴다.
    os._exit(1)


if __name__ == "__main__":
    main()
