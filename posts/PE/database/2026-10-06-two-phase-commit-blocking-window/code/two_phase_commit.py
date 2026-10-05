"""2단계 커밋(2PC)에서 조정자가 어느 시점에 멈추면 참여자가 막히는지 확인한다.

참여자 셋은 각자 SQLite 파일 DB를 갖고, 준비(YES 투표)는 쓰기 트랜잭션을 열어 둔 채
DT 로그에 yes 를 남기는 것으로 구현한다. 조정자의 멈춤 지점을 바꿔 가며, 참여자들이
협력 종료 프로토콜(Bernstein·Hadzilacos·Goodman 1987, 그림 7-4)로 결정을 얻는지 본다.
"""

import sqlite3
import tempfile
from pathlib import Path

YES, NO = "YES", "NO"
COMMIT, ABORT = "COMMIT", "ABORT"


class Participant:
    def __init__(self, name: str, db_path: Path, delta: int) -> None:
        self.name = name
        self.db_path = db_path
        self.delta = delta
        self.dt_log: list[str] = []
        self.conn = sqlite3.connect(db_path, timeout=0, isolation_level=None)

    @property
    def state(self) -> str:
        if COMMIT.lower() in self.dt_log:
            return "결정: 커밋"
        if ABORT.lower() in self.dt_log:
            return "결정: 철회"
        if "yes" in self.dt_log:
            return "불확실"
        return "투표 전"

    def on_vote_req(self) -> str:
        # 쓰기 잠금을 잡고 변경을 해 둔 채 커밋하지 않는다. 이것이 '준비'다.
        self.conn.execute("BEGIN IMMEDIATE")
        self.conn.execute(
            "UPDATE account SET balance = balance + ? WHERE id = 1", (self.delta,)
        )
        self.dt_log.append("yes")  # yes 기록은 YES 를 보내기 전에 남긴다
        return YES

    def on_vote_req_timeout(self) -> None:
        self.dt_log.append("abort")  # 투표 전이므로 혼자 철회할 수 있다

    def decide(self, decision: str) -> None:
        if self.conn.in_transaction:
            self.conn.execute("COMMIT" if decision == COMMIT else "ROLLBACK")
        self.dt_log.append(decision.lower())

    def answer_decision_req(self) -> str | None:
        """그림 7-4 응답자: 결정을 알거나 혼자 철회할 수 있으면 답하고, 불확실하면 답하지 않는다."""
        if "commit" in self.dt_log:
            return COMMIT
        if "abort" in self.dt_log or "yes" not in self.dt_log:
            return ABORT
        return None

    def close(self) -> None:
        self.conn.close()


def make_participants(work_dir: Path) -> list[Participant]:
    plan = [("P1 출금 은행", -100_000), ("P2 입금 은행", 100_000), ("P3 포인트", 100)]
    participants = []
    for i, (name, delta) in enumerate(plan, start=1):
        path = work_dir / f"p{i}.db"
        with sqlite3.connect(path) as setup:
            setup.execute("CREATE TABLE account (id INTEGER PRIMARY KEY, balance INTEGER)")
            setup.execute("INSERT INTO account VALUES (1, 500000)")
        setup.close()
        participants.append(Participant(name, path, delta))
    return participants


def run_coordinator(participants: list[Participant], stop_at: str | None) -> list[str]:
    """그림 7-3 조정자. stop_at 지점에서 멈춘다(사이트 장애). 조정자의 DT 로그를 돌려준다."""
    coord_log = ["start-2PC"]
    votes = []
    for i, p in enumerate(participants):
        if stop_at == "VOTE-REQ 일부만 보낸 뒤" and i == len(participants) - 1:
            return coord_log
        votes.append(p.on_vote_req())
    if stop_at == "YES 를 다 받고 결정 기록 전":
        return coord_log
    decision = COMMIT if all(v == YES for v in votes) else ABORT
    coord_log.append(decision.lower())  # COMMIT 을 보내기 전에 기록한다
    if stop_at == "commit 기록 직후, 전송 전":
        return coord_log
    for i, p in enumerate(participants):
        if stop_at == "P1 에게만 COMMIT 을 보낸 뒤" and i == 1:
            return coord_log
        p.decide(decision)
    return coord_log


def cooperative_termination(participants: list[Participant]) -> None:
    """불확실한 참여자가 다른 참여자에게 DECISION-REQ 를 보낸다(그림 7-4 개시자)."""
    for p in participants:
        if p.state == "투표 전":
            p.on_vote_req_timeout()
    for p in participants:
        if p.state != "불확실":
            continue
        answers = {q.name: q.answer_decision_req() for q in participants if q is not p}
        got = next((a for a in answers.values() if a), None)
        shown = ", ".join(f"{k}={v or '응답 없음(불확실)'}" for k, v in answers.items())
        print(f"    {p.name} 이 물음 -> {shown}")
        if got:
            p.decide(got)
        else:
            print(f"    {p.name}: 막힘 — 조정자가 돌아올 때까지 기다린다")


def probe_locks(p: Participant) -> None:
    """막힌 참여자의 DB 에 다른 세션이 붙으면 무엇을 겪는지 본다."""
    other = sqlite3.connect(p.db_path, timeout=0, isolation_level=None)
    seen = other.execute("SELECT balance FROM account WHERE id = 1").fetchone()[0]
    print(f"    다른 세션 읽기  : balance={seen} (준비 전 값)")
    try:
        other.execute("UPDATE account SET balance = balance + 1 WHERE id = 1")
        print("    다른 세션 쓰기  : 성공")
    except sqlite3.OperationalError as exc:
        print(f"    다른 세션 쓰기  : 실패 -> {exc}")
    other.close()


def recover_coordinator(participants: list[Participant], coord_log: list[str]) -> None:
    # 결정 기록이 없으면 철회로 정한다. COMMIT 을 보내기 전에 기록하므로 안전하다(7.4절 Recovery).
    decision = COMMIT if "commit" in coord_log else ABORT
    print(f"    조정자 복구: DT 로그 {coord_log} -> {decision}")
    for p in participants:
        if p.state == "불확실":
            p.decide(decision)


def show(participants: list[Participant]) -> None:
    """balance 는 다른 세션에서 읽는다. 준비만 된 변경은 커밋 전이라 보이지 않는다."""
    for p in participants:
        reader = sqlite3.connect(p.db_path, timeout=0)
        balance = reader.execute("SELECT balance FROM account WHERE id = 1").fetchone()[0]
        reader.close()
        print(f"    {p.name:<10} DT 로그={p.dt_log!s:<17} 상태={p.state:<8} 커밋된 balance={balance}")


def scenario(title: str, stop_at: str | None) -> None:
    print(f"\n== {title} ==")
    with tempfile.TemporaryDirectory() as tmp:
        participants = make_participants(Path(tmp))
        try:
            coord_log = run_coordinator(participants, stop_at)
            print(f"  조정자 멈춤 지점: {stop_at or '없음'} / 조정자 DT 로그: {coord_log}")
            print("  [멈춘 직후]")
            show(participants)
            if stop_at:
                print("  [협력 종료 프로토콜]")
                cooperative_termination(participants)
                blocked = [p for p in participants if p.state == "불확실"]
                if blocked:
                    print(f"  [막힌 동안 {blocked[0].name} 의 DB]")
                    probe_locks(blocked[0])
                    print("  [조정자 복구]")
                    recover_coordinator(participants, coord_log)
            print("  [끝]")
            show(participants)
        finally:
            # 열린 연결이 있으면 윈도에서 임시 폴더를 지우지 못한다
            for p in participants:
                p.close()


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version}")
    scenario("S1 장애 없음", None)
    scenario("S2 조정자가 VOTE-REQ 를 P3 에 보내기 전에 멈춤", "VOTE-REQ 일부만 보낸 뒤")
    scenario("S3 조정자가 P1 에게만 COMMIT 을 보내고 멈춤", "P1 에게만 COMMIT 을 보낸 뒤")
    scenario("S4 조정자가 YES 를 다 받고 결정을 기록하기 전에 멈춤", "YES 를 다 받고 결정 기록 전")
    scenario("S5 조정자가 commit 을 기록한 직후 보내기 전에 멈춤", "commit 기록 직후, 전송 전")


if __name__ == "__main__":
    main()
