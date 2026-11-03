# 예제 코드 — 대칭키와 공개키의 속도 차이 재기

OpenSSL 에 딸려 오는 `openssl speed` 만 쓴다. 따로 설치할 것이 없다.

## 실행

```bash
bash bench.sh
```

## 파일

| 파일 | 무엇 |
|---|---|
| `bench.sh` | 본문에 실은 숫자를 그대로 내는 측정 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `DURATION` — 항목마다 도는 시간(초). 기본 1초는 짧아서 흔들린다.
  3이나 10으로 올리면 값이 안정되는 대신 전체 수행이 길어진다
- `-evp` 뒤의 알고리즘 — `openssl speed -help` 로 목록을 본다.
  `aes-128-cbc` 를 넣어 보면 AES-NI 가 GCM 과 어떻게 다르게 붙는지 보인다
- `rsa2048`·`ecdsap256` 자리 — `rsa7680`, `ecdsabrp256r1` 처럼 바꿔 넣을 수 있다
