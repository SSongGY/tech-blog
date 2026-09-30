# FIFO · GPS · WFQ 스케줄링 검산

답안에 적은 WFQ 동작을 직접 계산해 확인한다. 외부 의존성은 없다.

- `[1]` Parekh & Gallager(1993) Table I 의 도착 패턴으로 GPS·WFQ 출발 시각을 구해
  논문 값과 맞는지, WFQ 가 GPS 보다 늦는 폭이 정리 1의 상한(Lmax/r) 안인지
- `[2]` 한 세션이 버스트를 쏟아 넣을 때 다른 세션의 지연이 FIFO 와 WFQ 에서 어떻게 갈리는지
- `[3]` 가중치 3:1 이 실제 서비스 비율로 나오는지

시간과 가상 시간은 `fractions.Fraction` 으로 계산해 동률 판정이 부동소수 오차에 흔들리지 않게 했다.

## 실행

```bash
python wfq_sim.py
```
