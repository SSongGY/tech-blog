"""HTTP 요청 N개를 보내는 동안 TCP 연결이 몇 개 맺어지는지 서버 쪽에서 센다.

socketserver 는 연결 하나를 받을 때마다 핸들러 객체를 하나 만든다.
그래서 핸들러의 setup() 이 불린 횟수 = 서버가 accept 한 TCP 연결 수다.
같은 클라이언트 코드라도 서버 설정·요청 헤더·응답 헤더 하나로 연결 수가 N 배가 된다.
"""

import http.client
import platform
import socket
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer

REQUEST_COUNT = 200
# 새 연결을 너무 많이 만들면 TIME_WAIT 가 임시 포트를 다 차지해 WinError 10048 이 난다.
# 이 예제는 한 번에 새 연결 약 5천 개 안쪽으로 묶는다
TIMING_REQUEST_COUNT = 500
TIMING_REPEAT = 3
BODY = b"ok\n"


class ConnectionStats:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.connections = 0
        self.requests = 0
        self.client_ports: set[int] = set()
        # 요청에 실려 온 Connection 헤더 값과 그 횟수
        self.connection_headers: dict[str, int] = {}


def make_server(protocol_version: str, send_length: bool,
                server_class: type[HTTPServer] = ThreadingHTTPServer) -> tuple[HTTPServer, ConnectionStats]:
    stats = ConnectionStats()

    class CountingHandler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            super().setup()
            with stats.lock:
                stats.connections += 1
                stats.client_ports.add(self.client_address[1])

        def do_GET(self) -> None:
            header_value = self.headers.get("Connection", "(없음)")
            with stats.lock:
                stats.requests += 1
                stats.connection_headers[header_value] = stats.connection_headers.get(header_value, 0) + 1
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            if send_length:
                self.send_header("Content-Length", str(len(BODY)))
            self.end_headers()
            self.wfile.write(BODY)

        def log_message(self, *args) -> None:
            pass

    CountingHandler.protocol_version = protocol_version
    server = server_class(("127.0.0.1", 0), CountingHandler)
    server.daemon_threads = True
    # 클라이언트가 먼저 끊은 연결의 예외 트레이스백이 출력에 섞이지 않게 한다
    server.handle_error = lambda request, client_address: None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, stats


def reuse_one_connection(port: int, count: int, extra_headers: dict[str, str] | None = None) -> None:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        for _ in range(count):
            conn.request("GET", "/", headers=extra_headers or {})
            response = conn.getresponse()
            response.read()
    finally:
        conn.close()


def urlopen_each(port: int, count: int) -> None:
    for _ in range(count):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
            response.read()


def count_all_time_wait() -> int:
    result = subprocess.run(["netstat", "-an", "-p", "TCP"], capture_output=True, text=True,
                            encoding="cp949", errors="replace")
    return sum(1 for line in result.stdout.splitlines() if "TIME_WAIT" in line.split())


def show_dynamic_port_range() -> None:
    result = subprocess.run(["netsh", "int", "ipv4", "show", "dynamicport", "tcp"],
                            capture_output=True, text=True, encoding="cp949", errors="replace")
    # 출력은 "시작 포트 : 49152" / "포트 수 : 16384" 두 줄이다. 숫자만 뽑는다
    numbers = [line.split(":")[-1].strip() for line in result.stdout.splitlines() if ":" in line]
    print(f"TCP 임시 포트 범위 (netsh): 시작 {numbers[0]}, 개수 {numbers[1]}")


def count_time_wait(port: int) -> tuple[int, int]:
    """서버 포트를 쓰는 TIME_WAIT 소켓을 서버 쪽·클라이언트 쪽으로 나눠 센다."""
    result = subprocess.run(["netstat", "-an", "-p", "TCP"], capture_output=True, text=True,
                            encoding="cp949", errors="replace")
    server_side = client_side = 0
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[3] != "TIME_WAIT":
            continue
        local_address, foreign_address = parts[1], parts[2]
        if local_address.endswith(f":{port}"):
            server_side += 1
        elif foreign_address.endswith(f":{port}"):
            client_side += 1
    return server_side, client_side


def run_case(title: str, protocol_version: str, send_length: bool, client) -> None:
    server, stats = make_server(protocol_version, send_length)
    port = server.server_address[1]
    error = None
    try:
        client(port)
    except Exception as exc:  # 응답 끝을 알 수 없는 경우를 그대로 보이려고 잡는다
        error = f"{type(exc).__name__}: {exc}"
    server_tw, client_tw = count_time_wait(port)
    server.shutdown()
    server.server_close()
    print(f"\n-- {title}")
    print(f"   서버 protocol_version={protocol_version}, Content-Length {'보냄' if send_length else '안 보냄'}")
    print(f"   서버가 받은 요청      : {stats.requests}")
    print(f"   서버가 accept 한 연결 : {stats.connections}")
    print(f"   클라이언트 포트 개수  : {len(stats.client_ports)}")
    print(f"   요청의 Connection 헤더: {stats.connection_headers}")
    print(f"   TIME_WAIT (서버 포트 쪽 / 클라이언트 포트 쪽) : {server_tw} / {client_tw}")
    if error:
        print(f"   클라이언트 에러       : {error}")


def show_close_response() -> None:
    """요청에 Connection: close 를 실었을 때 서버 응답 헤더와 http.client 의 판단을 본다."""
    server, _ = make_server("HTTP/1.1", send_length=True)
    port = server.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("GET", "/", headers={"Connection": "close"})
        response = conn.getresponse()
        response.read()
        print("\n-- 3-1. Connection: close 요청 한 번의 응답")
        print(f"   응답 상태줄 버전      : HTTP/{response.version / 10:.1f}")
        print(f"   응답 헤더 이름        : {[name for name, _ in response.getheaders()]}")
        print(f"   응답 Connection 헤더  : {response.getheader('Connection')}")
        print(f"   response.will_close   : {response.will_close}")
    finally:
        conn.close()
        server.shutdown()
        server.server_close()


def time_raw_connect(count: int) -> float:
    """HTTP 없이 TCP 연결을 맺고 끊기만 count 번 — 핸드셰이크와 정리 비용만 남긴다."""
    listener = socket.create_server(("127.0.0.1", 0))
    port = listener.getsockname()[1]

    def accept_loop() -> None:
        for _ in range(count):
            peer, _ = listener.accept()
            peer.close()

    acceptor = threading.Thread(target=accept_loop, daemon=True)
    acceptor.start()
    started = time.perf_counter()
    for _ in range(count):
        with socket.create_connection(("127.0.0.1", port)):
            pass
    acceptor.join()
    elapsed_ms = (time.perf_counter() - started) * 1000
    listener.close()
    return elapsed_ms


def time_case(protocol_version: str,
              server_class: type[HTTPServer] = ThreadingHTTPServer) -> list[float]:
    elapsed_ms = []
    for _ in range(TIMING_REPEAT):
        server, _ = make_server(protocol_version, send_length=True, server_class=server_class)
        port = server.server_address[1]
        started = time.perf_counter()
        reuse_one_connection(port, TIMING_REQUEST_COUNT)
        elapsed_ms.append((time.perf_counter() - started) * 1000)
        server.shutdown()
        server.server_close()
    return elapsed_ms


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()} {platform.release()}")
    print(f"BaseHTTPRequestHandler.protocol_version 기본값: {BaseHTTPRequestHandler.protocol_version}")
    print(f"요청 수 N = {REQUEST_COUNT}")
    show_dynamic_port_range()
    print(f"시작 시점 이 PC 전체의 TIME_WAIT 소켓: {count_all_time_wait()}")

    run_case("1. 서버 기본값(HTTP/1.0) + 연결 하나를 재사용하려는 클라이언트",
             "HTTP/1.0", True, lambda port: reuse_one_connection(port, REQUEST_COUNT))
    run_case("2. 서버 HTTP/1.1 + 연결 재사용 클라이언트",
             "HTTP/1.1", True, lambda port: reuse_one_connection(port, REQUEST_COUNT))
    run_case("3. 서버 HTTP/1.1 + 요청마다 Connection: close",
             "HTTP/1.1", True,
             lambda port: reuse_one_connection(port, REQUEST_COUNT, {"Connection": "close"}))
    show_close_response()
    run_case("4. 서버 HTTP/1.1 + urllib.request.urlopen 을 요청마다",
             "HTTP/1.1", True, lambda port: urlopen_each(port, REQUEST_COUNT))
    run_case("5. 서버 HTTP/1.1 인데 Content-Length 를 안 보내면 (요청 2개, 타임아웃 5초)",
             "HTTP/1.1", False, lambda port: reuse_one_connection(port, 2))

    print(f"\n-- 6. 요청 {TIMING_REQUEST_COUNT}개에 걸린 시간, {TIMING_REPEAT}회 반복 (루프백)")
    for protocol_version, label in (("HTTP/1.0", "연결을 매번 새로"), ("HTTP/1.1", "연결 하나 재사용")):
        elapsed_ms = time_case(protocol_version)
        joined = ", ".join(f"{value:.0f}" for value in elapsed_ms)
        print(f"   {label:<12} 중앙값 {statistics.median(elapsed_ms):6.0f} ms  [{joined}]")

    print(f"\n-- 7. HTTP 없이 TCP 연결만 {TIMING_REQUEST_COUNT}번 맺고 끊기, {TIMING_REPEAT}회 반복")
    raw_ms = [time_raw_connect(TIMING_REQUEST_COUNT) for _ in range(TIMING_REPEAT)]
    joined = ", ".join(f"{value:.0f}" for value in raw_ms)
    print(f"   연결만               중앙값 {statistics.median(raw_ms):6.0f} ms  [{joined}]")

    # ThreadingHTTPServer 는 연결마다 스레드를 하나 만든다. 스레드 없는 서버로 같은 일을 시킨다
    print(f"\n-- 8. 6번을 스레드 없는 HTTPServer 로, {TIMING_REPEAT}회 반복")
    for protocol_version, label in (("HTTP/1.0", "연결을 매번 새로"), ("HTTP/1.1", "연결 하나 재사용")):
        elapsed_ms = time_case(protocol_version, server_class=HTTPServer)
        joined = ", ".join(f"{value:.0f}" for value in elapsed_ms)
        print(f"   {label:<12} 중앙값 {statistics.median(elapsed_ms):6.0f} ms  [{joined}]")

    print(f"\n끝난 시점 이 PC 전체의 TIME_WAIT 소켓: {count_all_time_wait()}")


if __name__ == "__main__":
    main()
