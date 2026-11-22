"""병합 t-digest — Dunning·Ertl(2019) Algorithm 1 을 그대로 옮긴 최소 구현.

척도 함수는 논문 식 (6)·(7) 의 k0(선형)과 k1(아크사인) 두 가지다.
분위수 보간은 §2.9 의 기본 가정(a) "클러스터 표본의 절반은 중심 왼쪽, 절반은 오른쪽"
만 쓰고, 단일 표본 클러스터 보정은 넣지 않았다. 양 끝은 실제 최솟값·최댓값까지 잇는다.
"""

import math


def k0(q, delta):
    return delta * q / 2


def k0_inverse(k, delta):
    return min(1.0, max(0.0, 2 * k / delta))


def k1(q, delta):
    return delta / (2 * math.pi) * math.asin(2 * q - 1)


def k1_inverse(k, delta):
    # k1 의 치역은 [-δ/4, δ/4] 이므로 그 밖은 끝값으로 자른다
    if k >= delta / 4:
        return 1.0
    return (math.sin(2 * math.pi * k / delta) + 1) / 2


SCALES = {"k0": (k0, k0_inverse), "k1": (k1, k1_inverse)}


class TDigest:
    def __init__(self, delta, scale="k1", buffer_factor=10):
        self.delta = delta
        self.scale, self.scale_inverse = SCALES[scale]
        self.buffer_size = buffer_factor * math.ceil(delta)
        self.centroids = []  # [평균, 개수] 를 평균 오름차순으로
        self.buffer = []
        self.minimum = math.inf
        self.maximum = -math.inf

    def add(self, value):
        self.buffer.append([value, 1])
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)
        if len(self.buffer) >= self.buffer_size:
            self._merge()

    def merge_digest(self, other):
        """다른 다이제스트의 중심들을 입력으로 넣고 한 번 병합한다."""
        self._merge()
        other._merge()
        self.buffer = [c[:] for c in other.centroids]
        self.minimum = min(self.minimum, other.minimum)
        self.maximum = max(self.maximum, other.maximum)
        self._merge()

    def _merge(self):
        if not self.buffer:
            return
        # Algorithm 1 의 1~16 행
        points = sorted(self.centroids + self.buffer, key=lambda c: c[0])
        self.buffer = []
        total = sum(c[1] for c in points)
        merged = []
        q0 = 0.0
        q_limit = self.scale_inverse(self.scale(q0, self.delta) + 1, self.delta)
        sigma = points[0][:]
        for point in points[1:]:
            q = q0 + (sigma[1] + point[1]) / total
            if q <= q_limit:
                count = sigma[1] + point[1]
                sigma = [sigma[0] + (point[0] - sigma[0]) * point[1] / count, count]
            else:
                merged.append(sigma)
                q0 += sigma[1] / total
                q_limit = self.scale_inverse(self.scale(q0, self.delta) + 1, self.delta)
                sigma = point[:]
        merged.append(sigma)
        self.centroids = merged

    def count(self):
        self._merge()
        return sum(c[1] for c in self.centroids)

    def quantile(self, q):
        self._merge()
        cents = self.centroids
        target = q * self.count()
        # 각 중심이 자기 클러스터의 가운데(누적 개수 + 절반)에 있다고 본다
        position = 0.0
        prev_x, prev_rank = self.minimum, 0.0
        for mean, count in cents:
            rank = position + count / 2
            if target <= rank:
                span = rank - prev_rank
                frac = 0.0 if span == 0 else (target - prev_rank) / span
                return prev_x + frac * (mean - prev_x)
            prev_x, prev_rank = mean, rank
            position += count
        span = position - prev_rank
        frac = 0.0 if span == 0 else (target - prev_rank) / span
        return prev_x + frac * (self.maximum - prev_x)
