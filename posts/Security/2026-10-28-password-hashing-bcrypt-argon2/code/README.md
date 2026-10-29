# 비밀번호 해시 처리량 측정

같은 비밀번호를 SHA-256 · PBKDF2 · bcrypt · argon2id 로 각각 해시해, 1초에 몇 번
시도할 수 있는지를 잰다. 공격자가 유출된 해시를 무차별 대입할 때의 속도가 그대로 이 값이다.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python hash_throughput.py
```

## 바꿔볼 값

| 값 | 기본 | 바꾸면 |
|---|---|---|
| `bcrypt.gensalt(rounds=)` | `8` / `10` / `12` | 1 올릴 때마다 반복이 2배가 된다. 측정 시간도 2배 |
| `argon_light` 의 `memory_cost` | `8 * 1024` (8MiB) | 메모리를 줄일수록 빨라진다. 즉 공격자도 빨라진다 |
| `pbkdf2_hmac` 의 반복 횟수 | `600_000` | OWASP 가 PBKDF2-HMAC-SHA256 에 권고하는 값 |
| `SLOW_ROUNDS` | `20` | 느린 알고리즘의 측정 횟수. 늘리면 오차는 줄고 시간은 늘어난다 |

## 파일

| 파일 | 무엇 |
|---|---|
| `hash_throughput.py` | 측정 본체 |
| `requirements.txt` | 버전을 고정한 의존성 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |
