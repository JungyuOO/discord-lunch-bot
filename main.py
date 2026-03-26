from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen


PORT = 8080
NAVER_URL = "https://www.naver.com"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


def check_outbound():
    request = Request(NAVER_URL, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=10) as response:
        status_code = response.getcode()
    print(f"startup check status={status_code}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/ready"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    check_outbound()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"listening on {PORT}")
    server.serve_forever()
