"""플레임 그래프로 읽을 대상 프로그램.

모양을 일부러 어긋나게 만들었다. **깊은 쪽이 싼 일이고 얕은 쪽이 비싼 일이다.**
플레임 그래프에서 높이와 비용이 따로 논다는 것을 보려면 이런 대비가 필요하다.

- stage_validate 는 25단을 재귀로 내려가지만 각 단이 하는 일은 거의 없다
- stage_load 는 깊이 2에서 끝나지만 그 안에서 대부분의 시간을 쓴다
"""

CHECKSUM_ROUNDS = 27_000_000
INDEX_ROUNDS = 8_000_000
VALIDATE_DEPTH = 25
VALIDATE_ROUNDS = 400
VALIDATE_ITERATIONS = 30_000
FORMAT_ROUNDS = 3_200_000
SORT_SIZE = 800_000
SORT_PASSES = 5


def checksum_rows(rows):
    """깊이는 얕지만 가장 오래 도는 함수. 플레임 그래프의 넓은 평지가 된다."""
    total = 0
    for _ in range(CHECKSUM_ROUNDS):
        total = (total * 31 + rows) % 1_000_003
    return total


def build_index(rows):
    table = {}
    for i in range(INDEX_ROUNDS):
        table[i % rows] = i
    return len(table)


def stage_load(rows):
    return checksum_rows(rows), build_index(rows)


def walk(depth):
    """한 단마다 거의 아무 일도 하지 않는 재귀. 높지만 좁은 탑이 된다."""
    if depth == 0:
        total = 0
        for i in range(VALIDATE_ROUNDS):
            total += i
        return total
    return walk(depth - 1)


def stage_validate():
    result = 0
    for _ in range(VALIDATE_ITERATIONS):
        result += walk(VALIDATE_DEPTH)
    return result


def format_rows(rows):
    out = 0
    for i in range(FORMAT_ROUNDS):
        out += len(f"{i:08d}|{rows}")
    return out


def sort_rows():
    # 시드를 쓰지 않고 결정적인 수열을 만든다. 돌릴 때마다 같은 입력이어야 한다.
    last = 0
    for pass_no in range(SORT_PASSES):
        data = [(i * 7919 + pass_no) % SORT_SIZE for i in range(SORT_SIZE)]
        data.sort()
        last = data[-1]
    return last


def stage_report(rows):
    return format_rows(rows), sort_rows()


def pipeline(rows=512):
    """표본 수집기가 잘라 낼 기준점. 이 프레임 아래만 플레임 그래프에 들어간다."""
    loaded = stage_load(rows)
    checked = stage_validate()
    reported = stage_report(rows)
    return loaded, checked, reported
