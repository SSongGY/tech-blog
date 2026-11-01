"""Box-Jenkins 모형화 절차(식별-추정-진단)를 표준 라이브러리만으로 따라간다.

statsmodels 없이 도는 것이 목적이므로 난수 생성부터 카이제곱 꼬리확률까지 직접
계산한다. 난수는 선형합동법으로 만들어 어느 기계에서 돌려도 같은 표본경로가 나온다.
"""

import math

PHI = 0.7        # 자료를 만든 AR 계수
THETA = 0.4      # 자료를 만든 MA 계수
N = 300          # 관측 길이
SEED = 20261030
AR_ORDER = 8     # Hannan-Rissanen 1단계에서 쓰는 긴 AR 의 차수
MAX_ORDER = 2    # 차수 탐색 범위 (p, q 각각 0..MAX_ORDER)


# ---------------------------------------------------------------- 난수

def uniforms(count, seed):
    """Numerical Recipes 의 선형합동 계수를 쓴다. 재현만 되면 되는 용도다."""
    state = seed
    out = []
    for _ in range(count):
        state = (1664525 * state + 1013904223) % (2 ** 32)
        out.append((state + 0.5) / (2 ** 32))
    return out


def normals(count, seed):
    """Box-Muller 변환으로 표준정규 난수를 만든다."""
    raw = uniforms(2 * ((count + 1) // 2), seed)
    out = []
    for i in range(0, len(raw), 2):
        radius = math.sqrt(-2.0 * math.log(raw[i]))
        angle = 2.0 * math.pi * raw[i + 1]
        out.append(radius * math.cos(angle))
        out.append(radius * math.sin(angle))
    return out[:count]


# ---------------------------------------------------------------- 자료 생성

def simulate_arima_111(n, phi, theta, seed, burn=200):
    """ARMA(1,1) 을 만든 뒤 누적합을 취해 ARIMA(1,1,1) 로 만든다."""
    shocks = normals(n + burn + 1, seed)
    arma = [0.0]
    for t in range(1, n + burn + 1):
        arma.append(phi * arma[t - 1] + shocks[t] + theta * shocks[t - 1])
    arma = arma[burn + 1:]

    level = [100.0]
    for value in arma:
        level.append(level[-1] + value)
    return level[1:], arma


def difference(series, times=1):
    out = list(series)
    for _ in range(times):
        out = [out[i] - out[i - 1] for i in range(1, len(out))]
    return out


# ---------------------------------------------------------------- 기술통계

def mean(series):
    return sum(series) / len(series)


def variance(series):
    m = mean(series)
    return sum((v - m) ** 2 for v in series) / len(series)


def acf(series, max_lag):
    """표본 자기상관함수. 분모를 n 으로 고정한 표준 추정량을 쓴다."""
    m = mean(series)
    denom = sum((v - m) ** 2 for v in series)
    out = []
    for lag in range(1, max_lag + 1):
        num = sum((series[t] - m) * (series[t - lag] - m)
                  for t in range(lag, len(series)))
        out.append(num / denom)
    return out


def pacf(series, max_lag):
    """Durbin-Levinson 재귀로 편자기상관을 구한다."""
    r = acf(series, max_lag)
    phis = [[0.0] * (max_lag + 1) for _ in range(max_lag + 1)]
    out = [r[0]]
    phis[1][1] = r[0]
    for k in range(2, max_lag + 1):
        num = r[k - 1] - sum(phis[k - 1][j] * r[k - j - 1] for j in range(1, k))
        den = 1.0 - sum(phis[k - 1][j] * r[j - 1] for j in range(1, k))
        phis[k][k] = num / den
        for j in range(1, k):
            phis[k][j] = phis[k - 1][j] - phis[k][k] * phis[k - 1][k - j]
        out.append(phis[k][k])
    return out


# ---------------------------------------------------------------- 최소제곱

def solve(matrix, rhs):
    """부분 피벗을 쓰는 가우스 소거. 설계행렬이 작아 이것으로 충분하다."""
    n = len(matrix)
    aug = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for row in range(col + 1, n):
            factor = aug[row][col] / aug[col][col]
            for k in range(col, n + 1):
                aug[row][k] -= factor * aug[col][k]
    sol = [0.0] * n
    for col in reversed(range(n)):
        total = aug[col][n] - sum(aug[col][k] * sol[k] for k in range(col + 1, n))
        sol[col] = total / aug[col][col]
    return sol


def ols(design, target):
    k = len(design[0])
    xtx = [[sum(row[i] * row[j] for row in design) for j in range(k)]
           for i in range(k)]
    xty = [sum(design[t][i] * target[t] for t in range(len(target)))
           for i in range(k)]
    return solve(xtx, xty)


# ---------------------------------------------------------------- ARMA 적합

def long_ar_residuals(series, order):
    """Hannan-Rissanen 1단계. 긴 AR 의 잔차를 충격항 대용으로 쓴다."""
    design, target = [], []
    for t in range(order, len(series)):
        design.append([1.0] + [series[t - j] for j in range(1, order + 1)])
        target.append(series[t])
    beta = ols(design, target)
    proxy = [0.0] * len(series)
    for i, t in enumerate(range(order, len(series))):
        proxy[t] = target[i] - sum(beta[k] * design[i][k] for k in range(len(beta)))
    return proxy


def recursive_residuals(series, const, phis, thetas, start):
    """적합된 계수로 e_t 를 되짚어 계산한다. start 이전 충격은 0 으로 둔다."""
    errs = [0.0] * len(series)
    for t in range(start, len(series)):
        pred = const
        for j, phi in enumerate(phis, start=1):
            pred += phi * series[t - j]
        for j, theta in enumerate(thetas, start=1):
            pred += theta * errs[t - j]
        errs[t] = series[t] - pred
    return errs


def regress_arma(series, p, q, proxy, start):
    """시차 관측과 충격 대용항에 회귀한다. 표본 구간은 start 로 고정한다."""
    design, target = [], []
    for t in range(start, len(series)):
        row = [1.0]
        row += [series[t - j] for j in range(1, p + 1)]
        row += [proxy[t - j] for j in range(1, q + 1)]
        design.append(row)
        target.append(series[t])
    beta = ols(design, target)
    return beta[0], beta[1:1 + p], beta[1 + p:]


def root_magnitudes(coeffs):
    """1 + c1·z + c2·z² = 0 의 근의 크기. 전부 1 보다 커야 정상성·가역성이 선다."""
    c1 = coeffs[0] if len(coeffs) > 0 else 0.0
    c2 = coeffs[1] if len(coeffs) > 1 else 0.0
    if abs(c2) < 1e-12:
        return [float("inf")] if abs(c1) < 1e-12 else [1.0 / abs(c1)]
    disc = c1 * c1 - 4.0 * c2
    if disc >= 0.0:
        root = math.sqrt(disc)
        return [abs((-c1 + root) / (2.0 * c2)), abs((-c1 - root) / (2.0 * c2))]
    magnitude = math.sqrt(1.0 / abs(c2))      # 켤레근의 곱이 1/c2 다
    return [magnitude, magnitude]


def fit_arma(series, p, q, proxy, start, refine=3):
    """Hannan-Rissanen 2단계 뒤, 잔차를 되짚어 다시 회귀하기를 반복한다."""
    const, phis, thetas = regress_arma(series, p, q, proxy, start)
    errs = recursive_residuals(series, const, phis, thetas, start)
    for _ in range(refine):
        const, phis, thetas = regress_arma(series, p, q, errs, start)
        errs = recursive_residuals(series, const, phis, thetas, start)

    resid = errs[start:]
    n = len(resid)
    sigma2 = sum(e * e for e in resid) / n
    k = p + q + 1
    ar_min = min(root_magnitudes([-v for v in phis])) if phis else float("inf")
    ma_min = min(root_magnitudes(thetas)) if thetas else float("inf")
    return {"const": const, "phis": phis, "thetas": thetas, "resid": resid,
            "sigma2": sigma2, "n": n, "p": p, "q": q,
            "ar_root": ar_min, "ma_root": ma_min,
            "ok": ar_min > 1.0 and ma_min > 1.0,
            "aic": n * math.log(sigma2) + 2 * k,
            "bic": n * math.log(sigma2) + k * math.log(n)}


# ---------------------------------------------------------------- 카이제곱 꼬리

def gamma_upper_regularized(a, x):
    """Q(a,x). 급수와 연분수를 갈라 쓰는 표준적인 구현이다."""
    if x < a + 1.0:
        term = 1.0 / a
        total = term
        n = a
        for _ in range(500):
            n += 1.0
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a))

    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h * math.exp(-x + a * math.log(x) - math.lgamma(a))


def chi2_sf(x, df):
    """카이제곱 상위 꼬리확률."""
    return gamma_upper_regularized(df / 2.0, x / 2.0)


def ljung_box(resid, lags, fitted_params):
    """Q = n(n+2) sum r_k^2/(n-k), 자유도는 시차 수에서 추정 모수를 뺀다."""
    n = len(resid)
    r = acf(resid, lags)
    q = n * (n + 2) * sum(r[k - 1] ** 2 / (n - k) for k in range(1, lags + 1))
    df = lags - fitted_params
    return q, df, chi2_sf(q, df)


# ---------------------------------------------------------------- 출력

def band(n):
    return 2.0 / math.sqrt(n)


def mark(value, limit):
    return "유의" if abs(value) > limit else "."


def print_environment():
    import platform
    import sys
    print("환경")
    print(f"  파이썬  {platform.python_version()} ({sys.platform})")
    print("  외부 패키지 없음 — 표준 라이브러리 math 만 쓴다")
    print()


def main():
    print_environment()

    level, _ = simulate_arima_111(N, PHI, THETA, SEED)
    diff1 = difference(level)
    diff2 = difference(level, 2)

    print("0. 자료")
    print(f"  생성 모형   ARIMA(1,1,1), phi={PHI}, theta={THETA}, n={N}")
    print(f"  시작값      y[0]={level[0]:.3f}   끝값 y[{N - 1}]={level[-1]:.3f}")
    print(f"  원계열      평균 {mean(level):9.3f}   분산 {variance(level):9.3f}")
    print(f"  1차 차분    평균 {mean(diff1):9.3f}   분산 {variance(diff1):9.3f}")
    print()

    # ---------------------------------------------------- 1단계: 식별
    print("1. 식별")
    print("  (1) 구간별 평균·분산 — 정상성이면 구간을 갈라도 비슷해야 한다")
    for name, series in (("원계열 y", level), ("1차 차분 ∇y", diff1)):
        half = len(series) // 2
        first, second = series[:half], series[half:]
        print(f"    {name:12s} 전반부({half}) 평균 {mean(first):9.3f} 분산 {variance(first):9.3f}")
        print(f"    {'':12s} 후반부({len(second)}) 평균 {mean(second):9.3f} 분산 {variance(second):9.3f}")
        print(f"    {'':12s} 평균 차이 {abs(mean(first) - mean(second)):.3f}")
    print()

    limit_level = band(len(level))
    limit_diff = band(len(diff1))
    acf_level = acf(level, 10)
    acf_diff = acf(diff1, 10)
    pacf_diff = pacf(diff1, 10)
    print("  (2) ACF·PACF")
    print(f"    유의대역 ±2/√n = ±{limit_level:.4f}(원계열) / ±{limit_diff:.4f}(차분)")
    print()
    print("     시차   ACF(y)  판정      ACF(∇y)  판정     PACF(∇y)  판정")
    for lag in range(1, 11):
        print(f"     {lag:3d}  {acf_level[lag - 1]:8.4f}  {mark(acf_level[lag - 1], limit_level):4s}"
              f"  {acf_diff[lag - 1]:9.4f}  {mark(acf_diff[lag - 1], limit_diff):4s}"
              f"  {pacf_diff[lag - 1]:9.4f}  {mark(pacf_diff[lag - 1], limit_diff):4s}")
    print()
    print("    원계열 ACF 가 1 에 가까운 값에서 천천히 줄기만 하면 차분 신호다.")
    print()

    print("  (3) 과대차분 점검 — 한 번 더 빼 보고 MA 근을 본다")
    print("    ∇y 는 ARMA(1,1) 이므로 ∇²y 는 MA 쪽 차수가 하나 늘어 ARMA(1,2) 가 된다")
    print("    (근이 단위원에 붙으면 잔차 되짚기가 발산하므로 여기서는 2단계 회귀만 쓴다)")
    for times, series, order in ((1, diff1, (1, 1)), (2, diff2, (1, 2))):
        proxy = long_ar_residuals(series, AR_ORDER)
        fit = fit_arma(series, order[0], order[1], proxy, AR_ORDER, refine=0)
        thetas = "  ".join(f"theta{j}={v:+.4f}" for j, v in enumerate(fit["thetas"], 1))
        print(f"    차분 {times}회  ARMA{order}  분산 {variance(series):8.4f}"
              f"  {thetas}  최소 MA 근 |z| = {fit['ma_root']:.4f}")
    print("    한 번 더 빼면 MA 근이 1 바로 위까지 내려온다. 차분으로 넣은 (1-B) 인자가")
    print("    MA 쪽에 그대로 남아 이론상 근이 정확히 1 이 되기 때문이고, 가역성이")
    print("    이 경계에서 깨진다. 이것이 과대차분의 표식이다.")
    print()

    print("  (4) MA(1) 로는 이 ACF 를 못 맞춘다 — 이론 상한 확인")
    print("    MA(1) 의 이론 ACF(1) = theta/(1+theta²) 이고 최댓값은 theta=1 에서 0.5 다")
    for theta in (0.2, 0.5, 0.8, 1.0, 1.5, 3.0):
        print(f"      theta={theta:4.1f}  ->  rho1 = {theta / (1 + theta * theta):+.4f}")
    print(f"    관측된 ACF(1) = {acf_diff[0]:+.4f} 는 이 상한을 넘으므로 q=1 만으로는 설명되지 않는다.")
    print()

    # ---------------------------------------------------- 2단계: 추정
    print("2. 추정 — 차수별 적합과 정보기준")
    proxy = long_ar_residuals(diff1, AR_ORDER)
    results = {}
    print(f"    표본 구간을 t >= {AR_ORDER} 로 고정해 모든 차수가 같은 n 을 쓴다")
    print()
    print("      p   q      n      sigma^2          AIC          BIC   모수   AR근   MA근  가역")
    for p in range(MAX_ORDER + 1):
        for q in range(MAX_ORDER + 1):
            if p == 0 and q == 0:
                continue
            fit = fit_arma(diff1, p, q, proxy, AR_ORDER)
            results[(p, q)] = fit
            print(f"     {p:2d}  {q:2d}  {fit['n']:5d}  {fit['sigma2']:11.4g}"
                  f"  {fit['aic']:11.3f}  {fit['bic']:11.3f}   {p + q + 1:4d}"
                  f"  {fit['ar_root']:5.2f}  {fit['ma_root']:5.2f}"
                  f"   {'O' if fit['ok'] else 'X'}")

    print()
    print("    가역성(MA 근 > 1)·정상성(AR 근 > 1)을 어긴 적합은 차수 선택에서 뺀다.")
    valid = {k: v for k, v in results.items() if v["ok"]}
    best_aic = min(valid, key=lambda k: valid[k]["aic"])
    best_bic = min(valid, key=lambda k: valid[k]["bic"])
    print()
    print(f"    AIC 최소 = ARMA{best_aic[0], best_aic[1]}"
          f" → 원계열 기준 ARIMA({best_aic[0]},1,{best_aic[1]})")
    print(f"    BIC 최소 = ARMA{best_bic[0], best_bic[1]}")
    print()

    chosen = results[best_aic]
    print(f"    선택 모형의 추정값 (자료를 만든 값: phi={PHI}, theta={THETA})")
    print(f"      상수     {chosen['const']:+9.4f}")
    for j, value in enumerate(chosen["phis"], start=1):
        print(f"      phi{j}     {value:+9.4f}")
    for j, value in enumerate(chosen["thetas"], start=1):
        print(f"      theta{j}   {value:+9.4f}")
    print()

    # ---------------------------------------------------- 3단계: 진단
    print("3. 진단 — 잔차가 백색잡음인가")
    print("    카이제곱 꼬리확률 구현 검산 — 교과서 임계값을 넣어 0.05 가 나오는지 본다")
    for df, crit in ((1, 3.841), (5, 11.070), (10, 18.307), (20, 31.410)):
        print(f"      df={df:2d}  x={crit:6.3f}  →  p={chi2_sf(crit, df):.4f}")
    print()
    print("     모형        잔차 ACF(1)   Ljung-Box Q(12)   자유도      p값   판정")
    for key in ((1, 0), (2, 0), best_aic):
        fit = results[key]
        r1 = acf(fit["resid"], 1)[0]
        q, df, p = ljung_box(fit["resid"], 12, fit["p"] + fit["q"])
        verdict = "기각(구조 남음)" if p < 0.05 else "기각 못 함(백색잡음)"
        print(f"     ARMA({key[0]},{key[1]})   {r1:+11.4f}   {q:15.3f}   {df:6d}"
              f"  {p:7.4f}   {verdict}")
    print()
    print("    p값이 0.05 보다 작으면 잔차에 구조가 남았다는 뜻이므로 1단계로 되돌아간다.")
    print()

    # ---------------------------------------------------- 예측
    print("4. 예측 — 차분한 것을 되돌린다")
    p, q = best_aic
    hist = list(diff1)
    errs = recursive_residuals(diff1, chosen["const"], chosen["phis"],
                               chosen["thetas"], AR_ORDER)
    print("     시점   ∇y 예측값     y 예측값")
    cum = level[-1]
    for step in range(1, 6):
        value = chosen["const"]
        for j, phi in enumerate(chosen["phis"], start=1):
            value += phi * hist[-j]
        for j, theta in enumerate(chosen["thetas"], start=1):
            value += theta * errs[-j]
        hist.append(value)
        errs.append(0.0)       # 미래 충격의 기댓값은 0 이다
        cum += value
        print(f"     +{step:<4d} {value:+10.4f}  {cum:11.3f}")
    print()
    print(f"    마지막 관측값 y[{N - 1}] = {level[-1]:.3f} 에서 출발한다.")
    print("    충격항은 한 시점 뒤부터 사라지고 AR 항만 남아 예측이 한 값으로 수렴한다.")


if __name__ == "__main__":
    main()
