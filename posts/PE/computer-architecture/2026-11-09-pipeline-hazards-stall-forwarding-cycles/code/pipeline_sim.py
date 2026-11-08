"""5단계 파이프라인(IF ID EX MEM WB) 사이클 계산기.

명령은 순서대로만 흐르고, 막히면 ID 단계에서 기다린다(뒤 명령은 IF 에서 기다린다).
값이 언제 만들어지고 언제 필요한지만으로 각 명령의 단계별 사이클을 정한다.

  - ALU 결과는 EX 끝, 적재(lw) 결과는 MEM 끝에 생긴다
  - 포워딩이 있으면 값은 EX 시작에 필요하다
  - 포워딩이 없으면 값은 ID 에서 레지스터 파일을 읽을 때 필요하다
  - 레지스터 파일 우회(rf_bypass)가 있으면 WB 와 같은 사이클에 ID 가 읽을 수 있다
  - 분기는 branch_stage(EX 또는 ID) 끝에 결정된다. 예측은 '안 감'이다
  - unified_memory 면 명령 인출(IF)과 데이터 접근(MEM)이 메모리 하나를 나눠 쓴다
"""
from dataclasses import dataclass

STAGES = ("IF", "ID", "EX", "MEM", "WB")
PIPELINE_DEPTH = len(STAGES)


@dataclass
class Instr:
    text: str
    dest: str | None = None
    sources: tuple = ()
    is_load: bool = False
    is_store: bool = False
    is_branch: bool = False
    taken: bool = False


@dataclass
class Config:
    name: str
    forwarding: bool = True
    rf_bypass: bool = True
    branch_stage: str = "EX"
    unified_memory: bool = False


def schedule(trace, cfg):
    """명령마다 {단계: 사이클} 을 계산한다. 사이클은 1부터 센다."""
    timing = []
    last_writer = {}
    memory_busy = set()
    for i, ins in enumerate(trace):
        prev = timing[i - 1] if i else None
        if prev is None:
            fetch = 1
        else:
            # 앞 명령이 IF 를 비워야(=ID 로 가야) 다음 명령을 인출한다
            fetch = max(prev["IF"] + 1, prev["ID"])
            prev_ins = trace[i - 1]
            if prev_ins.is_branch and prev_ins.taken:
                # 예측이 틀렸다: 분기가 결정된 다음 사이클에야 목표 명령을 인출한다.
                # ID 결정은 ID 의 '마지막' 사이클 끝이다 — 값을 기다리며 머물렀으면 그만큼 늦다
                decided = prev["EX"] - 1 if cfg.branch_stage == "ID" else prev["EX"]
                fetch = max(fetch, decided + 1)
        while cfg.unified_memory and fetch in memory_busy:
            fetch += 1  # 구조 해저드: 앞선 명령의 MEM 이 메모리를 쓰고 있다

        decode = fetch + 1
        if prev is not None:
            decode = max(decode, prev["EX"])  # 앞 명령이 ID 를 비워야 들어간다
        execute = decode + 1

        for reg in ins.sources:
            if reg not in last_writer:
                continue
            producer_ins, producer = last_writer[reg]
            ready_end = producer["MEM"] if producer_ins.is_load else producer["EX"]
            if ins.is_branch and cfg.branch_stage == "ID":
                # ID 에서 비교하는 분기는 ID 의 마지막 사이클에 값이 있어야 한다
                execute = max(execute, ready_end + 2)
            elif cfg.forwarding:
                execute = max(execute, ready_end + 1)
            else:
                read_cycle = producer["WB"] if cfg.rf_bypass else producer["WB"] + 1
                execute = max(execute, read_cycle + 1)

        row = {"IF": fetch, "ID": decode, "EX": execute,
               "MEM": execute + 1, "WB": execute + 2}
        row["stall"] = execute - (decode + 1)
        timing.append(row)
        if ins.is_load or ins.is_store:
            memory_busy.add(row["MEM"])
        if ins.dest:
            last_writer[ins.dest] = (ins, row)
    return timing


def draw(trace, timing):
    """파이프라인 사이클 표. 막힌 사이클은 ID 를 반복해 찍는다."""
    total = timing[-1]["WB"]
    width = max(len(ins.text) for ins in trace) + 2
    head = " " * width + "".join(f"{c:>4}" for c in range(1, total + 1))
    lines = [head]
    for ins, row in zip(trace, timing):
        cells = [""] * (total + 1)
        cells[row["IF"]] = "IF"
        for c in range(row["IF"] + 1, row["ID"]):
            cells[c] = "if"  # 인출은 했지만 ID 가 차 있어 기다린다
        for c in range(row["ID"], row["EX"]):
            cells[c] = "ID" if c == row["ID"] else "id"
        cells[row["EX"]] = "EX"
        cells[row["MEM"]] = "ME"
        cells[row["WB"]] = "WB"
        lines.append(f"{ins.text:<{width}}" + "".join(f"{x:>4}" for x in cells[1:]))
    return "\n".join(lines)


def summarize(trace, timing):
    n = len(trace)
    total = timing[-1]["WB"]
    ideal = PIPELINE_DEPTH + n - 1
    stalls = sum(row["stall"] for row in timing)
    return total, ideal, stalls, (total - PIPELINE_DEPTH + 1) / n


def run(title, trace, cfg, show_table=True):
    timing = schedule(trace, cfg)
    total, ideal, stalls, cpi = summarize(trace, timing)
    print(f"--- {title} [{cfg.name}]")
    if show_table:
        print(draw(trace, timing))
    print(f"    명령 {len(trace)}개 · 총 {total} 사이클 · 이상적 k+n-1 = {ideal}"
          f" · 추가 {total - ideal} 사이클 (ID 대기 {stalls}) · CPI {cpi:.2f}")
    print()
    return total


def alu(dest, a, b, op="add"):
    return Instr(f"{op} {dest},{a},{b}", dest, (a, b))


def load(dest, base, offset):
    return Instr(f"lw {dest},{offset}({base})", dest, (base,), is_load=True)


def store(src, base, offset):
    return Instr(f"sw {src},{offset}({base})", None, (src, base), is_store=True)


def branch(a, b, taken):
    return Instr(f"beq {a},{b} ({'taken' if taken else 'not'})", None, (a, b),
                 is_branch=True, taken=taken)


FULL = Config("포워딩 있음")
NO_FWD = Config("포워딩 없음, RF 우회 있음", forwarding=False)
NO_FWD_NO_BYPASS = Config("포워딩·RF 우회 없음", forwarding=False, rf_bypass=False)


def section_ideal():
    print("== 1) 의존이 없는 명령 5개 — k+n-1 ==")
    trace = [alu(f"x{i + 1}", "x10", "x11") for i in range(5)]
    run("독립 명령", trace, FULL)


def section_alu_dependency():
    print("== 2) ALU 결과를 바로 다음 명령이 쓴다 ==")
    trace = [alu("x3", "x1", "x2"), alu("x5", "x3", "x4", "sub"),
             alu("x6", "x3", "x5", "or")]
    for cfg in (NO_FWD_NO_BYPASS, NO_FWD, FULL):
        run("add → sub → or", trace, cfg)


def section_load_use():
    print("== 3) 적재-사용 해저드 ==")
    trace = [load("x4", "x8", 20), alu("x6", "x4", "x1", "or"),
             alu("x7", "x2", "x3")]
    for cfg in (NO_FWD, FULL):
        run("lw → 바로 사용", trace, cfg)
    print("  -- 독립 명령을 사이에 끼워 넣으면(명령 재배치)")
    reordered = [load("x4", "x8", 20), alu("x7", "x2", "x3"),
                 alu("x6", "x4", "x1", "or")]
    run("lw → 독립 → 사용", reordered, FULL)


def section_branch():
    print("== 4) 제어 해저드 — 분기 결정 위치 ==")
    for taken in (False, True):
        # 비교할 x5 는 두 명령 앞에서 만든다 — 바로 앞 의존이 없는 경우
        trace = [alu("x5", "x6", "x7"), alu("x1", "x1", "x9", "addi"),
                 branch("x5", "x0", taken), alu("x2", "x2", "x9")]
        for stage in ("EX", "ID"):
            cfg = Config(f"분기 결정 {stage}", branch_stage=stage)
            run(f"분기 {'감' if taken else '안 감'}", trace, cfg)
    print("  -- ID 에서 결정하면 바로 앞 ALU 결과를 기다려야 한다")
    trace = [alu("x5", "x6", "x7"), branch("x5", "x0", True), alu("x2", "x2", "x9")]
    for stage in ("EX", "ID"):
        run("add → beq(감)", trace, Config(f"분기 결정 {stage}", branch_stage=stage))


def section_structural():
    print("== 5) 구조 해저드 — 명령·데이터 메모리를 하나로 쓰면 ==")
    trace = [load("x1", "x10", 0), alu("x2", "x11", "x12"), alu("x3", "x11", "x13"),
             alu("x4", "x11", "x14"), store("x2", "x10", 8), alu("x5", "x11", "x15")]
    run("lw 와 sw 가 섞인 6개", trace, FULL)
    run("lw 와 sw 가 섞인 6개", trace,
        Config("포워딩 있음, 메모리 1개", unified_memory=True))


def section_loop():
    print("== 6) 반복문 100회 — 조건별 CPI ==")
    body = [load("x4", "x10", 0), alu("x5", "x4", "x6"), store("x5", "x10", 0),
            alu("x10", "x10", "x8", "addi"), alu("x9", "x9", "x8", "addi")]
    trace = []
    for k in range(100):
        trace += body + [branch("x9", "x0", k < 99)]
    configs = [
        NO_FWD_NO_BYPASS,
        NO_FWD,
        FULL,
        Config("포워딩 있음, 분기 ID 결정", branch_stage="ID"),
    ]
    for cfg in configs:
        run("반복 100회 (600개)", trace, cfg, show_table=False)
    print("  -- 같은 반복을 재배치: lw 뒤에 독립 addi 를 먼저 둔다")
    reordered_body = [load("x4", "x10", 0), alu("x9", "x9", "x8", "addi"),
                      alu("x5", "x4", "x6"), store("x5", "x10", 0),
                      alu("x10", "x10", "x8", "addi")]
    trace = []
    for k in range(100):
        trace += reordered_body + [branch("x9", "x0", k < 99)]
    for cfg in (FULL, Config("포워딩 있음, 분기 ID 결정", branch_stage="ID")):
        run("재배치 반복 100회", trace, cfg, show_table=False)


def main():
    section_ideal()
    section_alu_dependency()
    section_load_use()
    section_branch()
    section_structural()
    section_loop()


if __name__ == "__main__":
    main()
