# RAG 검색 품질 지표 계산

Recall@k · Precision@k · MRR · nDCG@k 를 같은 정답 집합과 같은 두 검색 결과에
대고 계산한다. 외부 의존성 없이 표준 라이브러리만 쓴다.

## 실행

```bash
python retrieval_metrics.py
```

## 파일

| 파일 | 하는 일 |
|---|---|
| `retrieval_metrics.py` | 네 지표를 구현하고, Q1 의 nDCG@5 를 항마다 펼쳐 손 계산과 대조한다 |
| `output.txt` | 실제 실행 기록. `blog.py run-example` 이 만든다 |

`EXPECTED` 에 손으로 계산해 둔 nDCG@5 값이 들어 있다. 구현을 고치면 이 값과
어긋나는지부터 본다.

## 바꿔 볼 값

| 대상 | 바꾸면 |
|---|---|
| `RELEVANCE` 의 등급 | 등급을 전부 1 로 맞추면 nDCG 가 이진 지표에 가까워진다 |
| `RANKINGS` 의 순서 | 정답을 뒤로 밀수록 Recall@5 는 그대로인데 nDCG@5 와 MRR 만 떨어진다 |
| `dcg_at_k` 의 이득 식 | `2**grade - 1` 을 `grade` 로 바꾸면 선형 이득이 되고 등급 차가 덜 벌어진다 |
