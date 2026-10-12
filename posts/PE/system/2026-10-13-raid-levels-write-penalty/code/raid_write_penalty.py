"""RAID 레벨별로 블록 하나를 고쳐 쓸 때 디스크 I/O가 몇 번 일어나는지 센다.

디스크를 바이트열 목록으로 흉내 내고, 읽기·쓰기를 할 때마다 횟수를 센다.
패리티는 XOR(P), RAID 6의 두 번째 패리티는 GF(2^8) 리드-솔로몬(Q)이다.
Q의 정의와 두 디스크 복구 식은 H. Peter Anvin, "The mathematics of RAID-6"의 식 (2)·(19)·(20)을 따른다.
"""

import random
from functools import reduce

BLOCK_SIZE = 8
GF_POLY = 0x11D  # x^8 + x^4 + x^3 + x^2 + 1 (Anvin 1절)


def gf_mul2(a: int) -> int:
    a <<= 1
    return (a ^ GF_POLY) & 0xFF if a & 0x100 else a


GF_EXP = [1] * 510
for _i in range(1, 255):
    GF_EXP[_i] = gf_mul2(GF_EXP[_i - 1])
for _i in range(255, 510):
    GF_EXP[_i] = GF_EXP[_i - 255]
GF_LOG = {GF_EXP[i]: i for i in range(255)}


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def gf_pow2(n: int) -> int:
    return GF_EXP[n % 255]


def gf_inv(a: int) -> int:
    return GF_EXP[255 - GF_LOG[a]]


def xor(*blocks: bytes) -> bytes:
    return bytes(reduce(lambda x, y: x ^ y, column) for column in zip(*blocks))


def scale(coef: int, block: bytes) -> bytes:
    return bytes(gf_mul(coef, b) for b in block)


def make_p(data: list[bytes]) -> bytes:
    return xor(*data)


def make_q(data: list[bytes]) -> bytes:
    # Q = g^0·D0 + g^1·D1 + ... (Anvin 식 2, g = {02})
    return xor(*(scale(gf_pow2(i), d) for i, d in enumerate(data)))


class Array:
    """디스크 묶음. read·write 를 부를 때마다 횟수를 센다."""

    def __init__(self, disk_count: int):
        self.disks = [b"\x00" * BLOCK_SIZE for _ in range(disk_count)]
        self.reads = 0
        self.writes = 0
        self.log: list[str] = []

    def read(self, disk: int) -> bytes:
        self.reads += 1
        self.log.append(f"R{disk}")
        return self.disks[disk]

    def write(self, disk: int, block: bytes) -> None:
        self.writes += 1
        self.log.append(f"W{disk}")
        self.disks[disk] = block

    def reset_counter(self) -> None:
        self.reads = self.writes = 0
        self.log = []


def random_block(rng: random.Random) -> bytes:
    return bytes(rng.randrange(256) for _ in range(BLOCK_SIZE))


# ---- 레벨별 작은 쓰기 (한 스트라이프 안의 데이터 블록 하나를 고친다) ----

def small_write_raid0(arr: Array, data_idx: int, new: bytes) -> None:
    arr.write(data_idx, new)


def small_write_raid1(arr: Array, data_idx: int, new: bytes) -> None:
    # 거울 쌍 두 디스크에 같은 블록을 쓴다 (RAID 10은 쌍 하나만 건드린다)
    pair = data_idx * 2
    arr.write(pair, new)
    arr.write(pair + 1, new)


def small_write_raid5_rmw(arr: Array, n_data: int, data_idx: int, new: bytes) -> None:
    # 감산 방식: 새 패리티 = (옛 데이터 xor 새 데이터) xor 옛 패리티
    p_disk = n_data
    old_data = arr.read(data_idx)
    old_p = arr.read(p_disk)
    arr.write(data_idx, new)
    arr.write(p_disk, xor(old_data, new, old_p))


def small_write_raid5_reconstruct(
    arr: Array, n_data: int, data_idx: int, new: bytes
) -> None:
    # 가산 방식: 나머지 데이터 블록을 전부 읽어 패리티를 새로 만든다
    others = [arr.read(i) for i in range(n_data) if i != data_idx]
    arr.write(data_idx, new)
    arr.write(n_data, xor(new, *others))


def small_write_raid6_rmw(arr: Array, n_data: int, data_idx: int, new: bytes) -> None:
    # P·Q 둘 다 선형이므로 바뀐 몫(delta)만 더하면 된다
    p_disk, q_disk = n_data, n_data + 1
    old_data = arr.read(data_idx)
    old_p = arr.read(p_disk)
    old_q = arr.read(q_disk)
    delta = xor(old_data, new)
    arr.write(data_idx, new)
    arr.write(p_disk, xor(old_p, delta))
    arr.write(q_disk, xor(old_q, scale(gf_pow2(data_idx), delta)))


# ---- 복구 ----

def recover_one(blocks: list[bytes | None], p: bytes) -> bytes:
    alive = [b for b in blocks if b is not None]
    return xor(p, *alive)


def recover_two(
    blocks: list[bytes | None], x: int, y: int, p: bytes, q: bytes
) -> tuple[bytes, bytes]:
    # 잃은 두 칸을 {00}으로 두고 Pxy·Qxy를 만든 뒤 Anvin 식 (17)~(20)
    zeroed = [b if b is not None else b"\x00" * BLOCK_SIZE for b in blocks]
    p_xy, q_xy = make_p(zeroed), make_q(zeroed)
    g_yx = gf_pow2(y - x)
    denom_inv = gf_inv(g_yx ^ 1)
    coef_a = gf_mul(g_yx, denom_inv)
    coef_b = gf_mul(gf_pow2(-x), denom_inv)
    d_x = xor(scale(coef_a, xor(p, p_xy)), scale(coef_b, xor(q, q_xy)))
    d_y = xor(p, p_xy, d_x)
    return d_x, d_y


def show(title: str) -> None:
    print(f"\n-- {title}")


def main() -> None:
    rng = random.Random(42)
    n_data = 4

    show("1. 데이터 디스크 4개 기준, 블록 하나 고쳐 쓰기 (작은 쓰기)")
    print("   레벨                      디스크 수  읽기  쓰기  합계  순서")
    cases = []

    arr = Array(n_data)
    arr.reset_counter()
    small_write_raid0(arr, 1, random_block(rng))
    cases.append(("RAID 0", n_data, arr))

    arr = Array(n_data * 2)
    arr.reset_counter()
    small_write_raid1(arr, 1, random_block(rng))
    cases.append(("RAID 10 (1+0)", n_data * 2, arr))

    data = [random_block(rng) for _ in range(n_data)]
    arr5 = Array(n_data + 1)
    arr5.disks = data + [make_p(data)]
    arr5.reset_counter()
    small_write_raid5_rmw(arr5, n_data, 1, random_block(rng))
    cases.append(("RAID 5 감산(RMW)", n_data + 1, arr5))

    arr5b = Array(n_data + 1)
    arr5b.disks = data + [make_p(data)]
    arr5b.reset_counter()
    small_write_raid5_reconstruct(arr5b, n_data, 1, random_block(rng))
    cases.append(("RAID 5 가산(재구성)", n_data + 1, arr5b))

    arr6 = Array(n_data + 2)
    arr6.disks = data + [make_p(data), make_q(data)]
    arr6.reset_counter()
    small_write_raid6_rmw(arr6, n_data, 1, random_block(rng))
    cases.append(("RAID 6 감산(RMW)", n_data + 2, arr6))

    for name, disk_count, a in cases:
        total = a.reads + a.writes
        print(f"   {name:<22} {disk_count:>6}  {a.reads:>4}  {a.writes:>4}  {total:>4}  "
              + " ".join(a.log))

    show("2. 고쳐 쓴 뒤 패리티가 맞는가 — 처음부터 다시 계산한 값과 비교")
    d5 = arr5.disks[:n_data]
    print(f"   RAID 5 감산 P 일치: {arr5.disks[n_data] == make_p(d5)}")
    d5b = arr5b.disks[:n_data]
    print(f"   RAID 5 가산 P 일치: {arr5b.disks[n_data] == make_p(d5b)}")
    d6 = arr6.disks[:n_data]
    print(f"   RAID 6 감산 P 일치: {arr6.disks[n_data] == make_p(d6)}")
    print(f"   RAID 6 감산 Q 일치: {arr6.disks[n_data + 1] == make_q(d6)}")

    show("3. 감산 방식과 가산 방식의 I/O 수 — 데이터 디스크 수 N에 따라")
    print("   N   감산(2R+2W)  가산((N-1)R+2W)  적은 쪽")
    for n in range(2, 9):
        sub, add = 4, (n - 1) + 2
        better = "가산" if add < sub else ("같음" if add == sub else "감산")
        print(f"   {n:<3} {sub:>11}  {add:>15}  {better}")

    show("4. 전체 스트라이프 쓰기 — 데이터 4블록을 한꺼번에")
    new_stripe = [random_block(rng) for _ in range(n_data)]
    arr5f = Array(n_data + 1)
    arr5f.reset_counter()
    for i, b in enumerate(new_stripe):
        arr5f.write(i, b)
    arr5f.write(n_data, make_p(new_stripe))
    print(f"   RAID 5: 읽기 {arr5f.reads}, 쓰기 {arr5f.writes} "
          f"(데이터 블록당 {arr5f.writes / n_data:.2f}회)")
    arr6f = Array(n_data + 2)
    arr6f.reset_counter()
    for i, b in enumerate(new_stripe):
        arr6f.write(i, b)
    arr6f.write(n_data, make_p(new_stripe))
    arr6f.write(n_data + 1, make_q(new_stripe))
    print(f"   RAID 6: 읽기 {arr6f.reads}, 쓰기 {arr6f.writes} "
          f"(데이터 블록당 {arr6f.writes / n_data:.2f}회)")

    show("5. 디스크 1개 고장 — RAID 5에서 잃은 블록 읽기")
    arr5.reset_counter()
    lost = 2
    survivors = [arr5.read(i) if i != lost else None for i in range(n_data)]
    p = arr5.read(n_data)
    rebuilt = recover_one(survivors, p)
    print(f"   잃은 디스크 {lost}, 읽은 횟수 {arr5.reads} ({' '.join(arr5.log)})")
    print(f"   복구한 블록 일치: {rebuilt == arr5.disks[lost]}")

    show("6. 데이터 디스크 2개 고장 — RAID 6 복구 (Anvin 식 19·20)")
    for x, y in [(0, 1), (1, 3), (0, 3)]:
        blocks = [None if i in (x, y) else arr6.disks[i] for i in range(n_data)]
        d_x, d_y = recover_two(
            blocks, x, y, arr6.disks[n_data], arr6.disks[n_data + 1]
        )
        ok = d_x == arr6.disks[x] and d_y == arr6.disks[y]
        print(f"   D{x}·D{y} 잃음 -> 복구 일치: {ok}")

    show("7. 같은 두 디스크를 RAID 5에서 잃으면 — P 하나로 풀 수 있는가")
    blocks = [None if i in (0, 1) else arr5.disks[i] for i in range(n_data)]
    guess = recover_one(blocks, arr5.disks[n_data])
    print(f"   P xor 남은 블록 = D0 xor D1 : {guess == xor(arr5.disks[0], arr5.disks[1])}")
    print(f"   그 값이 D0과 같은가: {guess == arr5.disks[0]}")

    show("8. 디스크 8개로 묶을 때 — 용량 효율과 무작위 작은 쓰기 처리량")
    print("   (R = 디스크 1개의 무작위 I/O 처리량. 모든 디스크가 고르게 바쁘다고 가정)")
    print("   레벨     용량(디스크 수)  효율    견디는 고장  작은 쓰기 I/O  작은 쓰기 처리량")
    disks = 8
    layouts = [
        ("RAID 0", disks, "0개", 1),
        ("RAID 10", disks // 2, "쌍마다 1개", 2),
        ("RAID 5", disks - 1, "1개", 4),
        ("RAID 6", disks - 2, "아무 2개", 6),
    ]
    for name, usable, tolerance, ios in layouts:
        print(f"   {name:<8} {usable:>14}  {usable / disks:>6.1%}  {tolerance:<10} "
              f"{ios:>12}  {disks}/{ios} R = {disks / ios:.2f} R")


if __name__ == "__main__":
    main()
