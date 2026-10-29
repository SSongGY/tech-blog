# JWT 취소 예제

로그아웃·권한 강등 요구가 들어왔을 때 서버 세션과 JWT 가 각각 어떻게 반응하는지
다섯 절로 돌려 본다. 보완책 세 가지가 각각 무엇을 되돌려 받고 무엇을 내주는지,
검증 비용과 토큰 크기까지 측정한다.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python revocation.py
```

4절에서 RSA 2048비트 키를 그때그때 만들고 20,000회씩 검증하므로
전체가 끝나는 데 몇 초 걸린다. 3절에는 의도적인 1.2초 대기가 들어 있다.

## 파일

| 파일 | 무엇 |
|---|---|
| `revocation.py` | 본문에 실은 다섯 절을 순서대로 돌린다 |
| `requirements.txt` | PyJWT 와 cryptography 버전 고정 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록 |

## 바꿔 볼 값

- `TOKEN_TTL` — 토큰 수명. 기본 15분. 1절에서 "exp 까지 몇 초 남았다"가 따라 바뀐다
- `demo_cost` 의 `repeat` — 반복 횟수. 기본 20000.
  줄이면 HS256 과 RS256 의 차이가 측정 잡음에 묻힌다
- `demo_mitigations` 의 짧은 수명 토큰 — 1초. `time.sleep` 값도 함께 올려야 한다
- `key_size` — RSA 키 길이. 4096으로 올리면 RS256 검증 시간이 어떻게 변하는지 볼 수 있다

`HS_SECRET` 은 예제용 상수다. 실제 서비스에서는 환경변수나 비밀 관리 도구에서 읽는다.
