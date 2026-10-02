"""curl 예제가 두드릴 로컬 API 서버. 127.0.0.1:18080 에서만 듣는다.

느린 응답·리다이렉트·500·간헐적 503 처럼 실제 API 디버깅에서 만나는 상황을
엔드포인트마다 하나씩 만들어 둔다. 표준 라이브러리만 쓴다.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 18080
ECHO_HEADERS = [
    "Host", "User-Agent", "Accept", "Content-Type", "Content-Length",
    "Authorization", "Cookie", "X-Trace-Id",
]


class ApiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "demo-api/1.0"
    sys_version = ""
    flaky_calls = 0

    def log_message(self, format, *args):
        pass  # 예제 출력에 접근 로그가 섞이지 않게 한다

    def reply(self, status: int, body: bytes, content_type="application/json", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def reply_json(self, status: int, data: dict, extra=None):
        self.reply(status, json.dumps(data, ensure_ascii=False).encode(), extra=extra)

    def echo(self, body: str):
        headers = {h: self.headers[h] for h in ECHO_HEADERS if h in self.headers}
        self.reply_json(200, {"method": self.command, "path": self.path,
                              "headers": headers, "body": body})

    def route(self):
        # 본문을 먼저 다 읽는다. 남겨 두면 같은 연결의 다음 요청 앞에 붙는다
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode(errors="replace")
        path = self.path.split("?")[0]
        if path == "/echo-raw":
            raw = f"Content-Type: {self.headers['Content-Type']}\n\n{body}"
            self.reply(200, raw.encode(), "text/plain")
        elif path == "/health":
            self.reply(200, b"ok\n", "text/plain")
        elif path == "/users/42":
            self.reply_json(200, {"id": 42, "name": "kim"}, {"X-Request-Id": "req-0001"})
        elif path == "/slow-first-byte":
            time.sleep(0.4)  # 서버가 처리하느라 첫 바이트가 늦는 경우
            self.reply(200, b"done\n", "text/plain")
        elif path == "/slow-body":
            chunks = [b"part-%d\n" % i for i in range(4)]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(sum(map(len, chunks))))
            self.end_headers()
            for chunk in chunks:  # 헤더는 바로 보내고 본문을 천천히 흘린다
                self.wfile.write(chunk)
                self.wfile.flush()
                time.sleep(0.2)
        elif path == "/old-users/42":
            self.reply(301, b"", "text/plain", {"Location": "/users/42"})
        elif path == "/login":
            self.reply(302, b"", "text/plain", {"Location": "/echo"})
        elif path == "/loop":
            self.reply(302, b"", "text/plain", {"Location": "/loop"})
        elif path == "/error":
            self.reply_json(500, {"error": "database unavailable"})
        elif path == "/flaky":
            ApiHandler.flaky_calls += 1
            if ApiHandler.flaky_calls <= 2:
                self.reply_json(503, {"error": "try again", "call": ApiHandler.flaky_calls})
            else:
                self.reply_json(200, {"ok": True, "call": ApiHandler.flaky_calls})
        elif path == "/session":
            self.reply_json(200, {"login": "ok"}, {"Set-Cookie": "session=abc123; Path=/"})
        elif path == "/shutdown":
            self.reply(200, b"bye\n", "text/plain")
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.echo(body)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = route


class QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass  # -m 으로 끊은 연결의 예외 출력에 로컬 경로가 찍히므로 숨긴다


if __name__ == "__main__":
    QuietServer((HOST, PORT), ApiHandler).serve_forever()
