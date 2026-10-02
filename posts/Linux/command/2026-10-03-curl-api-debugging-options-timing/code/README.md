# 예제 코드 — curl로 API 디버깅

`api_server.py`가 127.0.0.1:18080에 작은 API 서버를 띄우고, `curl_options.sh`가 자주 쓰는 curl 옵션을
갈래별로 그 서버에 대고 돌린다. 느린 첫 바이트·느린 본문·리다이렉트·500·간헐적 503을 엔드포인트마다
하나씩 만들어 두었다. HTTPS 예제는 `openssl s_server`로 127.0.0.1:18443에 자체 서명 인증서 서버를
잠깐 띄운다(키는 `probe_pki/`에 생기고 gitignore 된다). 외부 네트워크에는 나가지 않는다.

필요한 것: bash, curl(7.82.0 이상 — `--json`), Python 3, openssl.

## 실행

```bash
bash curl_options.sh
```

## 바꿔볼 값

- `api_server.py`의 `/slow-first-byte` 대기 시간(0.4초)을 바꾸고 `starttransfer`가 따라 움직이는지 본다.
- `-m 0.5`를 `-m 1`로 늘려 `/slow-body`(본문을 0.2초 간격으로 4번 보낸다)를 끝까지 받는지 본다.
- `/flaky`는 처음 두 번 503을 준다. `--retry 1`로 줄여 마지막 응답과 종료 코드를 본다.
- 이 기록은 Windows의 curl(Schannel 백엔드)에서 나왔다. 다른 TLS 백엔드에서는 인증서 오류 메시지 문구가 다를 수 있다.
