"""조건부 요청 헤더가 200 · 304 · 412 를 가르는 지점을 http.server 로 실측한다.

http.server 는 조건부 요청을 처리하지 않으므로 RFC 9110 13.2.2 의 평가 순서를
직접 구현해, 서버가 아닌 규칙이 결과를 정한다는 점을 보인다.
"""

import http.client
import threading
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, HTTPServer

BODY = "hello, conditional request".encode("utf-8")
STRONG_ETAG = '"v1-abc"'
WEAK_ETAG = 'W/"v1-abc"'
LAST_MODIFIED_EPOCH = 1_767_225_600  # 2026-01-01 00:00:00 GMT
LAST_MODIFIED = formatdate(LAST_MODIFIED_EPOCH, usegmt=True)
EARLIER = formatdate(LAST_MODIFIED_EPOCH - 3600, usegmt=True)
LATER = formatdate(LAST_MODIFIED_EPOCH + 3600, usegmt=True)


def strip_weak(tag):
    return tag[2:] if tag.startswith("W/") else tag


def weak_match(header_value, current_etag):
    """If-None-Match 용 약한 비교: W/ 접두사를 무시하고 따옴표 문자열만 본다."""
    if header_value.strip() == "*":
        return True
    candidates = [part.strip() for part in header_value.split(",")]
    return any(strip_weak(tag) == strip_weak(current_etag) for tag in candidates)


def strong_match(header_value, current_etag):
    """If-Match 용 강한 비교: 양쪽 다 약한 태그가 아니고 문자열이 같아야 한다."""
    if header_value.strip() == "*":
        return True
    if current_etag.startswith("W/"):
        return False
    candidates = [part.strip() for part in header_value.split(",")]
    return any(not tag.startswith("W/") and tag == current_etag for tag in candidates)


def make_handler(current_etag):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if_match = self.headers.get("If-Match")
            if_none_match = self.headers.get("If-None-Match")
            if_modified_since = self.headers.get("If-Modified-Since")

            if if_match is not None and not strong_match(if_match, current_etag):
                return self.finish_without_body(412)
            if if_none_match is not None:
                if weak_match(if_none_match, current_etag):
                    return self.finish_without_body(304)
            elif if_modified_since is not None:
                # 날짜는 If-None-Match 가 없을 때만 본다 (RFC 9110 13.1.3)
                since = http_date_to_epoch(if_modified_since)
                if since is not None and LAST_MODIFIED_EPOCH <= since:
                    return self.finish_without_body(304)

            self.send_response(200)
            self.send_header("ETag", current_etag)
            self.send_header("Last-Modified", LAST_MODIFIED)
            self.send_header("Content-Length", str(len(BODY)))
            self.end_headers()
            self.wfile.write(BODY)

        def finish_without_body(self, status):
            self.send_response(status)
            self.send_header("ETag", current_etag)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, format, *args):
            pass

    return Handler


def http_date_to_epoch(text):
    from email.utils import parsedate_to_datetime

    try:
        return int(parsedate_to_datetime(text).timestamp())
    except (TypeError, ValueError):
        return None


def request(port, headers):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/", headers=headers)
    res = conn.getresponse()
    body = res.read()
    conn.close()
    return res.status, len(body)


def run_cases(title, current_etag, cases):
    server = HTTPServer(("127.0.0.1", 0), make_handler(current_etag))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"\n== {title} (서버의 ETag = {current_etag})")
    print(f"{'요청 헤더':<56} 상태  본문")
    print("-" * 70)
    for label, headers in cases:
        status, size = request(port, headers)
        print(f"{label:<56} {status}   {size}B")
    server.shutdown()
    server.server_close()


def main():
    print("Last-Modified =", LAST_MODIFIED)

    run_cases("강한 ETag", STRONG_ETAG, [
        ("(조건 헤더 없음)", {}),
        ("If-None-Match: 같은 강한 태그", {"If-None-Match": STRONG_ETAG}),
        ("If-None-Match: 같은 값의 약한 태그", {"If-None-Match": WEAK_ETAG}),
        ("If-None-Match: 다른 태그", {"If-None-Match": '"v0-old"'}),
        ("If-None-Match: 여러 개 중 하나가 일치", {"If-None-Match": '"v0-old", ' + STRONG_ETAG}),
        ("If-None-Match: *", {"If-None-Match": "*"}),
        ("If-Match: 같은 강한 태그", {"If-Match": STRONG_ETAG}),
        ("If-Match: 다른 태그", {"If-Match": '"v0-old"'}),
        ("If-Match: 같은 값의 약한 태그", {"If-Match": WEAK_ETAG}),
    ])

    run_cases("약한 ETag", WEAK_ETAG, [
        ("If-None-Match: 같은 약한 태그", {"If-None-Match": WEAK_ETAG}),
        ("If-None-Match: 같은 값의 강한 태그", {"If-None-Match": STRONG_ETAG}),
        ("If-Match: 같은 약한 태그", {"If-Match": WEAK_ETAG}),
        ("If-Match: 같은 값의 강한 태그", {"If-Match": STRONG_ETAG}),
    ])

    run_cases("날짜 헤더와 우선순위", STRONG_ETAG, [
        ("If-Modified-Since: 수정 시각과 같음", {"If-Modified-Since": LAST_MODIFIED}),
        ("If-Modified-Since: 수정 시각보다 이전", {"If-Modified-Since": EARLIER}),
        ("If-Modified-Since: 수정 시각보다 이후", {"If-Modified-Since": LATER}),
        ("If-Modified-Since 이후 + If-None-Match 다름", {"If-Modified-Since": LATER, "If-None-Match": '"v0-old"'}),
        ("If-Modified-Since 이전 + If-None-Match 같음", {"If-Modified-Since": EARLIER, "If-None-Match": STRONG_ETAG}),
    ])


if __name__ == "__main__":
    main()
