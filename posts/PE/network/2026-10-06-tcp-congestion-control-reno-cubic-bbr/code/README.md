# 예제 코드 — Reno · CUBIC · BBR 식 계산

RFC 5681(Reno), RFC 9438(CUBIC), draft-ietf-ccwg-bbr-06(BBR)에 적힌 식과 권고 상수로
창 크기를 계산한다. 망을 흉내 낸 측정이 아니라 **식의 계산**이다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python congestion_signals.py
```

## 바꿔볼 값

- `CUBIC_BETA`를 0.5(Reno와 같은 감소폭)로 바꾸면 3번에서 Reno 친화 구간이 이기는 RTT가 어떻게 바뀌는지 본다.
- 5번의 `buffer`를 `bdp * 0.25`(얕은 버퍼)로 바꾸고 6번 주기 길이와 평균 RTT를 비교한다.
- 4번에 위성 링크(50Mbps, 600ms)를 넣어 BDP가 얼마인지 본다.
