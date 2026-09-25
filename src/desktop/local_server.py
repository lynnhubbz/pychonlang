from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class LocalWebServer:
    def __init__(self, web_root: Path):
        self.web_root = Path(web_root).resolve()
        if not self.web_root.is_dir():
            raise FileNotFoundError(f"Web root does not exist: {self.web_root}")

        self.httpd = None
        self.thread = None

    def start(self) -> str:
        handler = lambda *args, **kwargs: QuietRequestHandler(
            *args,
            directory=str(self.web_root),
            **kwargs,
        )

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(
            target=self.httpd.serve_forever,
            daemon=True,
        )
        self.thread.start()

        port = self.httpd.server_address[1]
        return f"http://127.0.0.1:{port}/"

    def stop(self) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None


__all__ = ["LocalWebServer"]
