# IVF와 IVF-PQ의 비용·불균형·잔차 부호화

Faiss 없이 numpy로 k-평균 조대 양자화기, 역리스트, 곱 양자화를 직접 만들어
다음을 확인한다.

- `ivf_pq_cost.py`
  - **A** 조대 양자화기 학습 결과 — 역리스트 크기 분포와 불균형 계수
    (`faiss/utils/utils.cpp`의 `imbalance_factor`와 같은 식)
  - **B** `nprobe`를 바꿀 때 Faiss 논문의 비용 식과 실제 거리 계산 수, 재현율
  - **C** `nlist`를 바꿀 때 같은 `nprobe`에서의 비용과 재현율
  - **D** 원래 벡터를 PQ로 부호화할 때와 잔차를 부호화할 때의 복원 오차·재현율

난수 시드를 고정했으므로 같은 numpy 버전에서는 같은 값이 나온다.

## 실행

```bash
python ivf_pq_cost.py
```

의존성은 numpy 하나다. 없으면 `python -m pip install -r requirements.txt`로 먼저 설치한다.
