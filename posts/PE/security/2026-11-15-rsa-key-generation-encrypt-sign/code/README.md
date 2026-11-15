# 예제 코드 — RSA 를 작은 수로 계산하기

파이썬 표준 라이브러리만 쓴다(`pow(a, -1, m)` 은 Python 3.8 이상, `math.lcm` 은 3.9 이상).
**학습용이다.** 소수를 시드 고정 `random.Random` 으로 만들므로 실제 키에 쓰면 안 된다.
실제 키는 `secrets` 나 암호 라이브러리로 만든다.

## 실행

```bash
python rsa_by_hand.py
```

## 바꿔 볼 값

- `small_example()` 의 `e` 를 `7` 로 바꾸면 `gcd(e, λ(n))` 가 1 이 아니라서 `pow(e, -1, λ)` 가 `ValueError` 를 낸다
- `[7-B]` 의 `rng.getrandbits(128)` 을 `700` 비트로 늘리면 `m^3` 이 `n` 보다 커져 세제곱근 공격이 실패한다
- 측정 시간은 기계마다 다르다. 배율(CRT 대비, 복호/암호화)을 본다
