# 예제 코드 — HTTP Keep-Alive와 TCP 연결 수

`http.server` 로 루프백(127.0.0.1)에 서버를 띄우고, 요청 N개를 보내는 동안 서버가 accept 한 TCP 연결 수를
센다. 서버의 `protocol_version`, 요청의 `Connection: close`, 응답의 `Content-Length` 를 하나씩 바꿔
연결 수와 TIME_WAIT 소켓이 어느 쪽에 남는지 비교한다. TIME_WAIT 는 Windows `netstat -an -p TCP` 로 센다.
파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python keep_alive_count.py
```

## 바꿔볼 값

- `REQUEST_COUNT` 를 1000 으로 올리면 1·3·4번의 TIME_WAIT 수가 요청 수를 따라가는지 본다.
- 5번의 `timeout=5` 를 줄이면 클라이언트 에러가 얼마 만에 나는지 본다.
- 6번의 `TIMING_REQUEST_COUNT` 를 바꿔 두 방식의 시간 차이가 요청 수에 비례하는지 본다.
