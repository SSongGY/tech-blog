"""Roaring 비트맵을 표준 라이브러리로 구현해 크기와 연산 횟수를 센다.

근거: Chambi, Lemire, Kaser, Godin, "Better bitmap performance with Roaring bitmaps" (2016)
  - 32비트 정수를 상위 16비트(키)로 나누고, 하위 16비트를 컨테이너에 담는다 (2장)
  - 원소가 4096개 이하면 정렬된 16비트 배열, 넘으면 2^16비트 비트맵 (2장)
  - 넣다가 4096을 넘으면 비트맵으로, 빼다가 4096이 되면 배열로 바꾼다 (3장)
  - 교집합: 비트맵끼리는 1024개 64비트 워드 AND, 배열·비트맵은 배열을 돌며 비트 확인,
    배열끼리는 병합 (4장)
"""
import random
from array import array
from bisect import bisect_left, insort

ARRAY_LIMIT = 4096          # 이 개수 이하는 배열 컨테이너
BITMAP_WORDS = 1024         # 2^16 비트 = 64비트 워드 1024개
BITMAP_BYTES = BITMAP_WORDS * 8


class OpCounter:
    """교집합에서 한 기본 연산(비교·워드 AND·비트 확인) 횟수를 센다."""

    def __init__(self):
        self.count = 0


class ArrayContainer:
    kind = "array"

    def __init__(self, values=()):
        self.values = array("H", sorted(values))

    def __len__(self):
        return len(self.values)

    def nbytes(self):
        return len(self.values) * 2

    def contains(self, low):
        i = bisect_left(self.values, low)
        return i < len(self.values) and self.values[i] == low

    def add(self, low):
        if not self.contains(low):
            insort(self.values, low)

    def remove(self, low):
        i = bisect_left(self.values, low)
        if i < len(self.values) and self.values[i] == low:
            del self.values[i]


class BitmapContainer:
    kind = "bitmap"

    def __init__(self, values=()):
        self.words = array("Q", bytes(BITMAP_BYTES))
        self.cardinality = 0
        for low in values:
            self.add(low)

    def __len__(self):
        return self.cardinality

    def nbytes(self):
        return BITMAP_BYTES

    def contains(self, low):
        return (self.words[low >> 6] >> (low & 63)) & 1 == 1

    def add(self, low):
        if not self.contains(low):
            self.words[low >> 6] |= 1 << (low & 63)
            self.cardinality += 1

    def remove(self, low):
        if self.contains(low):
            self.words[low >> 6] &= ~(1 << (low & 63)) & 0xFFFFFFFFFFFFFFFF
            self.cardinality -= 1

    def to_list(self):
        result = []
        for i, word in enumerate(self.words):
            while word:
                lowest = word & -word
                result.append(i * 64 + lowest.bit_length() - 1)
                word ^= lowest
        return result


class RoaringBitmap:
    def __init__(self, values=()):
        self.keys = []          # 정렬된 상위 16비트
        self.containers = []
        self.conversions = 0    # 컨테이너 종류가 바뀐 횟수
        for x in values:
            self.add(x)

    def _find(self, key):
        i = bisect_left(self.keys, key)
        return i, i < len(self.keys) and self.keys[i] == key

    def add(self, x):
        key, low = x >> 16, x & 0xFFFF
        i, found = self._find(key)
        if not found:
            self.keys.insert(i, key)
            self.containers.insert(i, ArrayContainer())
        container = self.containers[i]
        container.add(low)
        if container.kind == "array" and len(container) > ARRAY_LIMIT:
            self.containers[i] = BitmapContainer(container.values)
            self.conversions += 1

    def remove(self, x):
        key, low = x >> 16, x & 0xFFFF
        i, found = self._find(key)
        if not found:
            return
        container = self.containers[i]
        container.remove(low)
        if container.kind == "bitmap" and len(container) <= ARRAY_LIMIT:
            self.containers[i] = ArrayContainer(container.to_list())
            self.conversions += 1

    def __len__(self):
        return sum(len(c) for c in self.containers)

    def payload_bytes(self):
        return sum(c.nbytes() for c in self.containers)


def intersect_containers(a, b, counter):
    """논문 4장의 세 경우. 결과 원소 목록을 돌려준다."""
    if a.kind == "bitmap" and b.kind == "bitmap":
        result = []
        for i in range(BITMAP_WORDS):
            counter.count += 1
            word = a.words[i] & b.words[i]
            while word:
                lowest = word & -word
                result.append(i * 64 + lowest.bit_length() - 1)
                word ^= lowest
        return result
    if a.kind == "bitmap" or b.kind == "bitmap":
        small, bitmap = (a, b) if a.kind == "array" else (b, a)
        result = []
        for low in small.values:
            counter.count += 1
            if bitmap.contains(low):
                result.append(low)
        return result
    result, i, j = [], 0, 0
    va, vb = a.values, b.values
    while i < len(va) and j < len(vb):
        counter.count += 1
        if va[i] == vb[j]:
            result.append(va[i])
            i += 1
            j += 1
        elif va[i] < vb[j]:
            i += 1
        else:
            j += 1
    return result


def intersect(r1, r2, counter):
    result, i, j = [], 0, 0
    while i < len(r1.keys) and j < len(r2.keys):
        if r1.keys[i] == r2.keys[j]:
            lows = intersect_containers(r1.containers[i], r2.containers[j], counter)
            result.extend((r1.keys[i] << 16) | low for low in lows)
            i += 1
            j += 1
        elif r1.keys[i] < r2.keys[j]:
            i += 1
        else:
            j += 1
    return result
