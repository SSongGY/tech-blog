"""트라이와 경로 압축 트라이(PATRICIA)의 구조적 성질을 직접 세어 확인한다.

확인하는 것은 넷이다.
  1. 경로 압축이 노드 수와 깊이를 얼마나 줄이는가
  2. 잎만 가진 트라이를 압축하면 노드 수가 2n-1 이 되는가
  3. 삽입 순서를 바꿔도 모양이 같은가
  4. 압축한 트라이의 최장 접두사 일치 결과가 전수 비교와 같은가
"""

import ipaddress
import random
import sys

PREFIX_TABLE = [
    ("0.0.0.0/0", "ISP-A"),
    ("10.0.0.0/8", "R1"),
    ("10.1.0.0/16", "R2"),
    ("10.1.2.0/24", "R3"),
    ("10.1.128.0/17", "R4"),
    ("10.128.0.0/9", "R5"),
    ("172.16.0.0/12", "R6"),
    ("192.168.0.0/16", "R7"),
]


class Node:
    """이진 트라이의 노드. skip 은 경로 압축으로 건너뛴 비트열이다."""

    __slots__ = ("child", "value", "skip")

    def __init__(self):
        self.child = [None, None]
        self.value = None
        self.skip = ""


def prefix_bits(cidr):
    network = ipaddress.IPv4Network(cidr)
    return format(int(network.network_address), "032b")[: network.prefixlen]


def address_bits(address):
    return format(int(ipaddress.IPv4Address(address)), "032b")


def build_trie(entries):
    """(비트열, 값) 쌍들로 압축하지 않은 이진 트라이를 만든다."""
    root = Node()
    for bits, value in entries:
        node = root
        for bit in bits:
            index = int(bit)
            if node.child[index] is None:
                node.child[index] = Node()
            node = node.child[index]
        node.value = value
    return root


def path_compress(node):
    """자식이 하나뿐이고 값이 없는 내부 노드를 없앤다.

    없앤 노드의 자리로 자식이 올라오므로, 사라진 비트를 자식의 skip 앞에 붙여
    경로가 가리키던 비트열을 보존한다.
    """
    for index in (0, 1):
        if node.child[index] is not None:
            node.child[index] = path_compress(node.child[index])
    if node.value is None:
        present = [i for i in (0, 1) if node.child[i] is not None]
        if len(present) == 1:
            only = present[0]
            child = node.child[only]
            child.skip = node.skip + str(only) + child.skip
            return child
    return node


def count_nodes(node):
    if node is None:
        return 0
    return 1 + count_nodes(node.child[0]) + count_nodes(node.child[1])


def max_depth(node, depth=0):
    """루트에서 가장 먼 노드까지의 간선 수."""
    if node is None:
        return depth - 1
    return max(max_depth(node.child[0], depth + 1),
               max_depth(node.child[1], depth + 1),
               depth)


def serialize(node):
    """모양 비교용 정규 표현. 자식 유무·skip·값을 괄호로 적는다."""
    if node is None:
        return "."
    return "({}|{}|{}{})".format(
        node.skip or "-",
        node.value or "-",
        serialize(node.child[0]),
        serialize(node.child[1]),
    )


def lookup(root, bits):
    """경로 위에서 만난 값을 덮어쓰며 내려간다. 마지막 값이 최장 일치다."""
    node, position, best = root, 0, None
    while node is not None:
        if not bits[position:].startswith(node.skip):
            break
        position += len(node.skip)
        if node.value is not None:
            best = node.value
        if position >= len(bits):
            break
        node = node.child[int(bits[position])]
        position += 1
    return best


def brute_force_lookup(address):
    """전수 비교. 맞는 접두사를 모두 찾아 길이가 가장 긴 것을 고른다."""
    target = ipaddress.IPv4Address(address)
    best_length, best_value = -1, None
    for cidr, value in PREFIX_TABLE:
        network = ipaddress.IPv4Network(cidr)
        if target in network and network.prefixlen > best_length:
            best_length, best_value = network.prefixlen, value
    return best_value


def report_compression():
    print("[1] 경로 압축이 줄이는 양 — 포워딩 테이블 항목 {}개".format(len(PREFIX_TABLE)))
    entries = [(prefix_bits(c), v) for c, v in PREFIX_TABLE]
    plain = build_trie(entries)
    print("    압축 전  노드 {:4d}개 · 최대 깊이 {:3d}".format(
        count_nodes(plain), max_depth(plain)))
    compressed = path_compress(build_trie(entries))
    print("    압축 후  노드 {:4d}개 · 최대 깊이 {:3d}".format(
        count_nodes(compressed), max_depth(compressed)))
    return compressed


def report_leaf_node_count():
    print("\n[2] 잎만 가진 트라이의 압축 후 노드 수 — 2n-1 이 되는지")
    generator = random.Random(20261025)
    for leaf_count in (4, 8, 16, 64, 256):
        keys = set()
        while len(keys) < leaf_count:
            keys.add(format(generator.getrandbits(32), "032b"))
        trie = path_compress(build_trie([(k, "leaf") for k in sorted(keys)]))
        actual = count_nodes(trie)
        expected = 2 * leaf_count - 1
        print("    n={:4d}  노드 {:4d}개  2n-1 = {:4d}  {}".format(
            leaf_count, actual, expected,
            "일치" if actual == expected else "불일치"))


def report_order_independence():
    print("\n[3] 삽입 순서를 바꿔도 모양이 같은지 — 무작위 순열 20가지")
    entries = [(prefix_bits(c), v) for c, v in PREFIX_TABLE]
    generator = random.Random(7)
    shapes = set()
    for _ in range(20):
        shuffled = entries[:]
        generator.shuffle(shuffled)
        shapes.add(serialize(path_compress(build_trie(shuffled))))
    print("    서로 다른 모양 {}가지".format(len(shapes)))
    print("    {}".format("모두 같다" if len(shapes) == 1 else "순서에 따라 갈린다"))


def report_lookup_agreement(compressed):
    print("\n[4] 압축 트라이의 최장 접두사 일치 == 전수 비교")
    samples = ["10.1.2.3", "10.1.3.1", "10.1.200.9", "10.200.0.1",
               "10.0.0.7", "172.16.5.5", "192.168.1.1", "8.8.8.8"]
    mismatch = 0
    for address in samples:
        by_trie = lookup(compressed, address_bits(address))
        by_scan = brute_force_lookup(address)
        mismatch += by_trie != by_scan
        print("    {:<14s} 트라이 {:<6s} 전수 {:<6s} {}".format(
            address, by_trie, by_scan, "일치" if by_trie == by_scan else "불일치"))

    generator = random.Random(1225)
    for _ in range(50000):
        address = str(ipaddress.IPv4Address(generator.getrandbits(32)))
        mismatch += lookup(compressed, address_bits(address)) != brute_force_lookup(address)
    print("    무작위 주소 50,000개 추가 대조 — 불일치 {}건".format(mismatch))
    return mismatch


def main():
    compressed = report_compression()
    report_leaf_node_count()
    report_order_independence()
    mismatch = report_lookup_agreement(compressed)
    return 1 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
