# 예제 코드 — 정규식 백트래킹 폭발 재현과 방어

표준 `re` 모듈만으로 돌아간다. 7절의 `timeout` 예제만 선택 의존성 `regex` 를 쓰고,
없으면 그 부분을 건너뛴다.

## 실행

```bash
python redos_backtracking.py
```

선택 의존성까지 보려면 먼저 설치한다.

```bash
python -m pip install -r requirements.txt
```

## 파일

| 파일 | 무엇 |
|---|---|
| `redos_backtracking.py` | 본문에 실은 출력을 그대로 내는 스크립트 |
| `requirements.txt` | 7절이 쓰는 `regex` 의 버전 고정 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `EXPONENTIAL_START`, `EXPONENTIAL_STEPS` — 1·3절에서 길이를 어디서부터 몇 번 늘릴지.
  시작을 늦추면 첫 줄부터 초 단위로 걸린다
- `EXP_LIMIT` — 한 측정이 이 초를 넘으면 더 늘리지 않는다. 기본 2초
- 6절의 식 목록에 자기 식을 넣어 보면 고친 식이 정말 선형인지 바로 보인다
- 7절의 `"a" * 26` 을 줄이면 `join(timeout=0.1)` 이 제때 돌아오는 길이를 찾을 수 있다
