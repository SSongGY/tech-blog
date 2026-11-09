"""BST·AVL·레드-블랙 트리에 같은 키를 넣고 높이와 회전 횟수를 비교한다.

AVL 은 MIT 6.006 Fall 2011 Lecture 6 의 정의(자식 높이 차 ±1, nil 높이 -1)를,
레드-블랙은 Stanford CS161 Winter 2018 슬라이드의 RB-Insert / RB-Insert-Fixup
(CLRS 13장 의사코드)을 그대로 옮겼다.
"""
import math
import random

RED, BLACK = "R", "B"


# ---------- 단순 BST: 정렬 입력이면 깊이가 N 까지 가므로 반복문으로 넣는다 ----------
class BSTNode:
    __slots__ = ("key", "left", "right")

    def __init__(self, key):
        self.key, self.left, self.right = key, None, None


def bst_height_after_inserts(keys):
    root, height = None, -1
    for key in keys:
        if root is None:
            root, height = BSTNode(key), 0
            continue
        node, depth = root, 0
        while True:
            depth += 1
            branch = "left" if key < node.key else "right"
            child = getattr(node, branch)
            if child is None:
                setattr(node, branch, BSTNode(key))
                break
            node = child
        height = max(height, depth)
    return height


# ---------- AVL ----------
class AVLNode:
    __slots__ = ("key", "left", "right", "height")

    def __init__(self, key):
        self.key, self.left, self.right, self.height = key, None, None, 0


def avl_h(node):
    return node.height if node else -1  # nil 의 높이를 -1 로 둔다 (MIT 노트)


class AVLTree:
    def __init__(self):
        self.root = None
        self.rotations = 0
        self.cases = []

    def _update(self, node):
        node.height = 1 + max(avl_h(node.left), avl_h(node.right))

    def _rotate_right(self, y):
        x = y.left
        y.left, x.right = x.right, y
        self._update(y)
        self._update(x)
        self.rotations += 1
        return x

    def _rotate_left(self, x):
        y = x.right
        x.right, y.left = y.left, x
        self._update(x)
        self._update(y)
        self.rotations += 1
        return y

    def _rebalance(self, node):
        self._update(node)
        balance = avl_h(node.left) - avl_h(node.right)
        if balance > 1:
            if avl_h(node.left.left) >= avl_h(node.left.right):
                self.cases.append(f"LL@{node.key}")
            else:
                self.cases.append(f"LR@{node.key}")
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1:
            if avl_h(node.right.right) >= avl_h(node.right.left):
                self.cases.append(f"RR@{node.key}")
            else:
                self.cases.append(f"RL@{node.key}")
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    def _insert(self, node, key):
        if node is None:
            return AVLNode(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        return self._rebalance(node)

    def insert(self, key):
        self.cases = []
        self.root = self._insert(self.root, key)

    def check(self):
        """모든 노드에서 자식 높이 차가 1 이하인지, 저장된 높이가 맞는지 본다."""
        def walk(node):
            if node is None:
                return -1
            lh, rh = walk(node.left), walk(node.right)
            assert abs(lh - rh) <= 1 and node.height == 1 + max(lh, rh)
            return node.height
        return walk(self.root)


# ---------- 레드-블랙 (CLRS 의사코드, 센티널 NIL 하나) ----------
class RBNode:
    __slots__ = ("key", "left", "right", "parent", "color")

    def __init__(self, key, color, nil=None):
        self.key, self.color = key, color
        self.left = self.right = self.parent = nil


class RBTree:
    def __init__(self):
        self.nil = RBNode(None, BLACK)
        self.root = self.nil
        self.rotations = 0
        self.cases = []

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        if y.left is not self.nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self.nil:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left, x.parent = x, y
        self.rotations += 1

    def _right_rotate(self, y):
        x = y.left
        y.left = x.right
        if x.right is not self.nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is self.nil:
            self.root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right, y.parent = y, x
        self.rotations += 1

    def insert(self, key):
        self.cases = []
        z = RBNode(key, RED, self.nil)
        y, x = self.nil, self.root
        while x is not self.nil:
            y = x
            x = x.left if key < x.key else x.right
        z.parent = y
        if y is self.nil:
            self.root = z
        elif key < y.key:
            y.left = z
        else:
            y.right = z
        self._fixup(z)

    def _fixup(self, z):
        while z.parent.color == RED:
            gp = z.parent.parent
            left_side = z.parent is gp.left
            uncle = gp.right if left_side else gp.left
            if uncle.color == RED:                       # Case 1: 색만 바꾸고 2단계 위로
                z.parent.color = uncle.color = BLACK
                gp.color = RED
                z = gp
                self.cases.append("1")
                continue
            inner = z is (z.parent.right if left_side else z.parent.left)
            if inner:                                    # Case 2: 바깥쪽으로 돌려 Case 3 으로
                z = z.parent
                (self._left_rotate if left_side else self._right_rotate)(z)
                self.cases.append("2")
            z.parent.color = BLACK                       # Case 3: 색 바꾸고 조부모를 회전
            z.parent.parent.color = RED
            (self._right_rotate if left_side else self._left_rotate)(z.parent.parent)
            self.cases.append("3")
        self.root.color = BLACK

    def check(self):
        """성질 2·4·5 를 검사하고 (높이, 루트의 흑색 높이)를 돌려준다.
        성질 1(색은 둘 중 하나)·3(NIL 은 흑색)은 자료구조가 보장한다."""
        assert self.root.color == BLACK

        def walk(node):
            if node is self.nil:
                return -1, 1                             # NIL 도 흑색 노드로 센다
            if node.color == RED:
                assert node.left.color == BLACK and node.right.color == BLACK
            lh, lb = walk(node.left)
            rh, rb = walk(node.right)
            assert lb == rb
            return 1 + max(lh, rh), lb + (node.color == BLACK)
        return walk(self.root)


def shape(node, nil=None, color=False):
    """괄호 표기: 키(왼쪽 서브트리, 오른쪽 서브트리)."""
    if node is None or node is nil:
        return "."
    label = f"{node.key}{node.color if color else ''}"
    if (node.left is None or node.left is nil) and (node.right is None or node.right is nil):
        return label
    return f"{label}({shape(node.left, nil, color)},{shape(node.right, nil, color)})"


def section(title):
    print(f"\n== {title} ==")


def main():
    section("1. 높이 h 인 AVL 트리의 최소 노드 수 N(h) = N(h-1) + N(h-2) + 1")
    fib = [0, 1]
    while len(fib) < 20:
        fib.append(fib[-1] + fib[-2])
    n_min = {-1: 0, 0: 1}
    for height in range(1, 11):
        n_min[height] = n_min[height - 1] + n_min[height - 2] + 1
    print(" h  N(h)  F(h+3)-1  같은가")
    for height in range(0, 11):
        print(f"{height:2d} {n_min[height]:5d} {fib[height + 3] - 1:9d}  {n_min[height] == fib[height + 3] - 1}")

    section("2. 정렬된 키 1..7 을 차례로 넣을 때")
    avl, rb = AVLTree(), RBTree()
    print("키  AVL 보정        AVL 모양                          RB 보정(경우)  RB 모양")
    for key in range(1, 8):
        avl.insert(key)
        rb.insert(key)
        avl_cases = ",".join(avl.cases) or "-"
        rb_cases = ",".join(rb.cases) or "-"
        print(f"{key:2d}  {avl_cases:12s}  {shape(avl.root):32s}  {rb_cases:13s}  {shape(rb.root, rb.nil, True)}")
    print(f"누적 회전: AVL {avl.rotations}회, RB {rb.rotations}회")
    print(f"높이: AVL {avl.check()}, RB {rb.check()[0]} (BST 였다면 {bst_height_after_inserts(range(1, 8))})")

    section("3. 높이 비교 (높이 = 루트에서 가장 먼 노드까지 간선 수)")
    rng = random.Random(20261110)
    print("입력     N        BST     AVL   RB   1.44 lg N  2 lg(N+1)  회전/삽입 AVL  RB    삽입당 최대 회전 AVL RB")
    for order in ("정렬", "무작위"):
        for n in (1_000, 100_000):
            keys = list(range(n))
            if order == "무작위":
                rng.shuffle(keys)
            avl, rb = AVLTree(), RBTree()
            avl_max = rb_max = 0
            for key in keys:
                before = avl.rotations
                avl.insert(key)
                avl_max = max(avl_max, avl.rotations - before)
                before = rb.rotations
                rb.insert(key)
                rb_max = max(rb_max, rb.rotations - before)
            avl_height = avl.check()
            rb_height, rb_black = rb.check()
            # 정렬 입력의 BST 는 삽입마다 끝까지 내려가 O(N^2) 이므로 큰 N 은 돌리지 않는다
            if order == "정렬" and n > 1_000:
                bst_height = "생략"
            else:
                bst_height = bst_height_after_inserts(keys)
            print(f"{order:4s} {n:7,d}  {bst_height:>7}  {avl_height:4d} {rb_height:4d}"
                  f"  {1.44 * math.log2(n):9.2f}  {2 * math.log2(n + 1):9.2f}"
                  f"  {avl.rotations / n:13.3f} {rb.rotations / n:5.3f}"
                  f"  {avl_max:19d} {rb_max:2d}")
    print("모든 트리에서 AVL 균형 조건과 레드-블랙 성질 2·4·5 검사 통과")


if __name__ == "__main__":
    main()
