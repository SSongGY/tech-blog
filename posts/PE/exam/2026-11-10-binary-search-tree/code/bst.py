"""이진 탐색 트리 답안 검산.

답안에 실은 예제 트리의 탐색 경로, 삭제 세 경우(Hibbard 삭제 포함),
정렬된 입력이 만드는 편향 트리, 무작위 입력의 평균 비교 횟수를 확인한다.
"""
import math
import random


class Node:
    __slots__ = ("key", "left", "right")

    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = insert(root.left, key)
    elif key > root.key:
        root.right = insert(root.right, key)
    # 같은 키는 무시한다 — 키 유일성을 전제로 한 정의를 그대로 따른다
    return root


def search_path(root, key):
    path = []
    node = root
    while node is not None:
        path.append(node.key)
        if key == node.key:
            return path, True
        node = node.left if key < node.key else node.right
    return path, False


def inorder(root):
    return [] if root is None else inorder(root.left) + [root.key] + inorder(root.right)


def height(root):
    # 노드 하나짜리 트리의 높이를 0으로 둔다 (간선 수 기준)
    return -1 if root is None else 1 + max(height(root.left), height(root.right))


def delete_min(node):
    if node.left is None:
        return node.right
    node.left = delete_min(node.left)
    return node


def delete(root, key):
    if root is None:
        return None
    if key < root.key:
        root.left = delete(root.left, key)
    elif key > root.key:
        root.right = delete(root.right, key)
    else:
        if root.left is None:
            return root.right
        if root.right is None:
            return root.left
        # 자식이 둘이면 오른쪽 서브트리의 최솟값(후속자)이 자리를 잇는다
        successor = root.right
        while successor.left is not None:
            successor = successor.left
        successor.right = delete_min(root.right)
        successor.left = root.left
        return successor
    return root


def build(keys):
    root = None
    for key in keys:
        root = insert(root, key)
    return root


def shape(root):
    if root is None:
        return "."
    if root.left is None and root.right is None:
        return str(root.key)
    return f"{root.key}({shape(root.left)}, {shape(root.right)})"


def average_hit_compares(root, keys):
    return sum(len(search_path(root, k)[0]) for k in keys) / len(keys)


def main():
    keys = [50, 30, 70, 20, 40, 60, 80, 35]
    root = build(keys)
    print("== 1. 예제 트리 ==")
    print("삽입 순서:", keys)
    print("구조    :", shape(root))
    print("중위 순회:", inorder(root))
    print("높이    :", height(root))

    print("\n== 2. 탐색 경로 ==")
    for key in (35, 65):
        path, found = search_path(root, key)
        print(f"찾는 키 {key}: 경로 {path}, 비교 {len(path)}회, {'성공' if found else '실패'}")

    print("\n== 3. 삭제 세 경우 ==")
    for key, label in ((20, "자식 0개"), (40, "자식 1개"), (50, "자식 2개")):
        root = delete(root, key)
        print(f"{key} 삭제({label}) -> {shape(root)}")
        print("  중위 순회:", inorder(root))

    print("\n== 4. 입력 순서와 높이 (N=15) ==")
    sorted_root = build(range(1, 16))
    balanced = [8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15]
    print("정렬 순서 입력 높이:", height(sorted_root))
    print("균형 순서 입력 높이:", height(build(balanced)))

    print("\n== 5. 무작위 입력의 평균 비교 횟수 ==")
    rng = random.Random(2026)
    for n in (1_000, 10_000):
        sample = rng.sample(range(n * 10), n)
        tree = build(sample)
        measured = average_hit_compares(tree, sample)
        print(f"N={n:>6}: 측정 {measured:.2f}회, "
              f"2 ln N = {2 * math.log(n):.2f}, lg N = {math.log2(n):.2f}, 높이 {height(tree)}")


if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(20_000)
    main()
