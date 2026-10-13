# 트랜스포머 비용 계산 — 예제

파이썬 표준 라이브러리만 쓴다. 설치할 것이 없다.

## 실행

```bash
python attention_cost.py
```

## 무엇을 계산하는가

측정이 아니라 **구조에서 바로 따라 나오는 산술**이다. 상수는 전부
Vaswani et al.(2017) `Attention Is All You Need` 의 base 모델 값을 쓴다.

| 상수 | 값 | 근거 |
|---|---|---|
| `NUM_LAYERS` | 6 | §3.1 Encoder and Decoder Stacks |
| `D_MODEL` | 512 | §3.1 |
| `NUM_HEADS` | 8 | §3.2.2 Multi-Head Attention |
| `BYTES_PER_VALUE` | 2 | 논문 값이 아니라 16비트로 둔다는 가정 |

두 가지를 길이별로 낸다.

- **어텐션 점수 칸 수** — 헤드 하나가 `n × n` 점수 행렬을 만들고, 그것이
  헤드 수 × 층 수만큼 생긴다. 길이에 **제곱**으로 늘어난다
- **KV 캐시 크기** — 층마다 K 한 벌, V 한 벌. 길이에 **비례**해 늘어난다

마지막 절은 수식으로 낸 값과 이중 루프로 하나씩 센 값이 같은지 검산한다.

## 바꿔 볼 값

| 값 | 바꾸면 |
|---|---|
| `BYTES_PER_VALUE` | 32비트(`4`)로 두면 KV 캐시가 두 배가 된다 |
| `NUM_LAYERS`, `D_MODEL` | 더 큰 모델의 값을 넣으면 캐시가 선형으로 커진다 |
| `SEQUENCE_LENGTHS` | 더 긴 길이를 넣어 제곱 증가를 눈으로 확인한다 |

## 파일

| 파일 | 무엇 |
|---|---|
| `attention_cost.py` | 본문에 실은 계산 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |
