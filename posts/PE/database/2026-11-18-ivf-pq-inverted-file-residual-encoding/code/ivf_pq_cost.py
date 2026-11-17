"""IVF와 IVF-PQ를 직접 만들어 비용 식, 불균형 계수, 잔차 부호화를 확인한다.

Faiss를 쓰지 않고 numpy로 k-평균·역리스트·곱 양자화를 직접 구현한다.
라이브러리 내부를 감추지 않아야 거리 계산 횟수를 정확히 셀 수 있기 때문이다.
"""
import platform
import sys

import numpy as np

SEED = 7
DIM = 32
N_BASE = 20_000
N_QUERY = 200
N_BLOBS = 40
TOP_K = 10
KMEANS_ITERS = 20


def make_data(rng):
    # 군집 크기가 고르지 않은 혼합 분포. 실제 임베딩도 주제별 밀도가 다르다.
    centers = rng.normal(0.0, 4.0, size=(N_BLOBS, DIM))
    weights = 1.0 / np.arange(1, N_BLOBS + 1) ** 0.8
    weights /= weights.sum()
    labels = rng.choice(N_BLOBS, size=N_BASE + N_QUERY, p=weights)
    points = centers[labels] + rng.normal(0.0, 1.5, size=(len(labels), DIM))
    return points[:N_BASE], points[N_BASE:]


def sq_dist(x, c):
    return (x * x).sum(1)[:, None] - 2.0 * x @ c.T + (c * c).sum(1)[None, :]


def kmeans(x, k, rng):
    cent = x[rng.choice(len(x), size=k, replace=False)].copy()
    for _ in range(KMEANS_ITERS):
        assign = sq_dist(x, cent).argmin(1)
        for j in range(k):
            members = x[assign == j]
            # 빈 군집은 임의의 점으로 다시 띄운다 (Faiss도 같은 처리를 한다)
            cent[j] = members.mean(0) if len(members) else x[rng.integers(len(x))]
    return cent, sq_dist(x, cent).argmin(1)


def imbalance_factor(sizes):
    # faiss/utils/utils.cpp 의 imbalance_factor 와 같은 식: k·Σn_i² / (Σn_i)²
    sizes = np.asarray(sizes, dtype=float)
    return len(sizes) * (sizes ** 2).sum() / sizes.sum() ** 2


def ground_truth(base, queries):
    return np.argsort(sq_dist(queries, base), axis=1)[:, :TOP_K]


def recall(found, truth):
    return np.mean([len(set(f) & set(t)) / TOP_K for f, t in zip(found, truth)])


def ivf_flat_search(base, cent, assign, queries, nprobe):
    lists = [np.flatnonzero(assign == j) for j in range(len(cent))]
    probes = np.argsort(sq_dist(queries, cent), axis=1)[:, :nprobe]
    results, n_dist = [], []
    for q, probe in zip(queries, probes):
        ids = np.concatenate([lists[j] for j in probe])
        d = ((base[ids] - q) ** 2).sum(1)
        results.append(ids[np.argsort(d)[:TOP_K]])
        n_dist.append(len(cent) + len(ids))  # 중심 비교 + 목록 원소 비교
    return results, float(np.mean(n_dist))


PQ_M = 8        # 부분공간 수. 32차원을 4차원씩 8조각으로 자른다
PQ_KSUB = 256   # 부분공간마다 코드북 항목 수 → 조각당 1바이트


def pq_train(x, rng):
    dsub = x.shape[1] // PQ_M
    return np.stack([kmeans(x[:, s * dsub:(s + 1) * dsub], PQ_KSUB, rng)[0]
                     for s in range(PQ_M)])


def pq_encode(x, books):
    dsub = books.shape[2]
    return np.stack([sq_dist(x[:, s * dsub:(s + 1) * dsub], books[s]).argmin(1)
                     for s in range(PQ_M)], axis=1).astype(np.uint8)


def pq_decode(codes, books):
    return np.concatenate([books[s][codes[:, s]] for s in range(PQ_M)], axis=1)


def ivf_pq_search(cent, assign, codes, books, queries, nprobe, by_residual):
    lists = [np.flatnonzero(assign == j) for j in range(len(cent))]
    probes = np.argsort(sq_dist(queries, cent), axis=1)[:, :nprobe]
    dsub = books.shape[2]
    results = []
    for q, probe in zip(queries, probes):
        ids_all, d_all = [], []
        for j in probe:
            # 잔차로 부호화했으면 질의도 그 목록 중심 기준으로 옮겨서 잰다
            r = q - cent[j] if by_residual else q
            table = np.stack([((books[s] - r[s * dsub:(s + 1) * dsub]) ** 2).sum(1)
                              for s in range(PQ_M)])          # (M, KSUB) 거리표
            ids = lists[j]
            d_all.append(table[np.arange(PQ_M), codes[ids]].sum(1))
            ids_all.append(ids)
        ids = np.concatenate(ids_all)
        results.append(ids[np.argsort(np.concatenate(d_all))[:TOP_K]])
    return results


def main():
    rng = np.random.default_rng(SEED)
    base, queries = make_data(rng)
    truth = ground_truth(base, queries)
    print(f"Python {platform.python_version()} / numpy {np.__version__} / {platform.system()}")
    print(f"데이터: 기준 벡터 N={N_BASE:,}, 차원 D={DIM}, 질의 {N_QUERY}개, 정답은 전수 비교 상위 {TOP_K}")
    print(f"전수 비교의 거리 계산 수 = N = {N_BASE:,}\n")

    nlist = 128
    cent, assign = kmeans(base, nlist, rng)
    sizes = np.bincount(assign, minlength=nlist)
    print(f"[A] 조대 양자화기 학습 — k-평균, nlist={nlist}, 반복 {KMEANS_ITERS}회")
    print(f"  역리스트 크기  최소 {sizes.min()} / 중앙 {int(np.median(sizes))} / "
          f"최대 {sizes.max()} / 평균 N/nlist = {N_BASE / nlist:.1f}")
    print(f"  큰 목록 5개    {sorted(sizes.tolist(), reverse=True)[:5]}")
    imb = imbalance_factor(sizes)
    print(f"  불균형 계수 nlist·Σn²/N² = {imb:.3f}   (모든 목록이 같은 크기면 1.000)\n")

    print(f"[B] nprobe 를 바꿀 때 — nlist={nlist} 고정")
    print("  nprobe |  식 nlist+nprobe·N/nlist |   실제 평균 |  실제/식 | 전수 대비 | recall@10")
    for nprobe in (1, 2, 4, 8, 16, 32):
        formula = nlist + nprobe * N_BASE / nlist
        found, actual = ivf_flat_search(base, cent, assign, queries, nprobe)
        print(f"  {nprobe:>6} | {formula:>24,.0f} | {actual:>10,.0f} | {actual / formula:>7.3f} |"
              f" {actual / N_BASE:>8.1%} | {recall(found, truth):.3f}")
    print(f"  nprobe=1 일 때 기대 목록 크기 Σn²/N = 불균형 계수 × N/nlist = {imb * N_BASE / nlist:,.0f}\n")

    nprobe = 8
    print(f"[C] nlist 를 바꿀 때 — nprobe={nprobe} 고정, 식의 최솟점 √(nprobe·N) = {np.sqrt(nprobe * N_BASE):.0f}")
    print("   nlist |   식 | 실제 평균 | 불균형 계수 | recall@10")
    for k in (32, 128, 512):
        c_k, a_k = (cent, assign) if k == nlist else kmeans(base, k, rng)
        found, actual = ivf_flat_search(base, c_k, a_k, queries, nprobe)
        print(f"  {k:>6} | {k + nprobe * N_BASE / k:>5,.0f} | {actual:>8,.0f} |"
              f" {imbalance_factor(np.bincount(a_k, minlength=k)):>10.3f} | {recall(found, truth):.3f}")
    print()

    print(f"[D] IVF-PQ — 원래 벡터를 부호화할 때와 잔차를 부호화할 때 (nlist={nlist})")
    print(f"  벡터 1개: float32 {DIM * 4}바이트 → PQ 코드 {PQ_M}바이트 (M={PQ_M}, 부분공간 {DIM // PQ_M}차원, k*={PQ_KSUB})")
    residual = base - cent[assign]
    print(f"  평균 제곱 노름      원래 벡터 {np.mean((base ** 2).sum(1)):8.2f}"
          f" | 잔차 {np.mean((residual ** 2).sum(1)):8.2f}")
    books_raw = pq_train(base, rng)
    codes_raw = pq_encode(base, books_raw)
    books_res = pq_train(residual, rng)
    codes_res = pq_encode(residual, books_res)
    mse_raw = np.mean(((base - pq_decode(codes_raw, books_raw)) ** 2).sum(1))
    mse_res = np.mean(((residual - pq_decode(codes_res, books_res)) ** 2).sum(1))
    print(f"  복원 제곱오차       원래 벡터 {mse_raw:8.2f} | 잔차 {mse_res:8.2f}")
    print("  nprobe | IVFFlat | IVF-PQ 원래 벡터 | IVF-PQ 잔차   (recall@10)")
    for nprobe in (4, 16, 32):
        flat, _ = ivf_flat_search(base, cent, assign, queries, nprobe)
        raw = ivf_pq_search(cent, assign, codes_raw, books_raw, queries, nprobe, False)
        res = ivf_pq_search(cent, assign, codes_res, books_res, queries, nprobe, True)
        print(f"  {nprobe:>6} |   {recall(flat, truth):.3f} |            {recall(raw, truth):.3f} |"
              f"        {recall(res, truth):.3f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
