# 예제 코드 — RED와 CoDel의 판단 규칙 계산

RED의 표시 확률 식과 EWMA, CoDel의 제어 법칙과 dequeue 상태 기계를 원 논문·RFC의 식 그대로
옮겨 계산한다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python aqm_calc.py
```

## 모델

- **TCP 송신원의 반응은 없다.** 드롭해도 큐가 줄지 않는다. 판단 규칙이 언제 무엇을 버리는지만 본다.
- **RED**는 Floyd·Jacobson(1993) §7의 `p_b`, Method 2의 `p_a = p_b / (1 − count·p_b)`,
  §6.2의 EWMA를 썼다. 표시 간격 분포는 `random.Random(7)`로 고정해 돌렸다.
- **CoDel**은 RFC 8289 §5.5 dequeue 의사코드를 옮겼다. 바이트 수 검사(`MAXPACKET`)는 뺐고,
  1 ms마다 패킷 하나를 꺼내며 그 패킷의 체류 시간을 미리 정한 함수로 준다.

## 바꿔볼 값

- `standing_queue`의 빠지는 구간(401~450 ms)을 1,600 ms 넘게 늘리면 재진입 때 count가 1로 돌아간다.
- `good_queue`의 버스트를 120 ms 넘게 끌면 좋은 큐도 드롭 대상이 된다.
