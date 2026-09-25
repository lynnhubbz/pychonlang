import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow

from src.desktop.local_server import LocalWebServer


ROOT = Path(__file__).resolve().parents[2]


def get_web_root() -> Path:
    bundled_dist = Path(sys.executable).resolve().parent / "web"
    if (bundled_dist / "index.html").is_file():
        return bundled_dist

    development_dist = ROOT / "src" / "ConlangEngine" / "dist"
    if (development_dist / "index.html").is_file():
        return development_dist

    raise FileNotFoundError(
        "Could not find the ConlangEngine dist folder. "
        "Run 'python scripts/build_web.py' first."
    )


class MainWindow(QMainWindow):
    def __init__(self, server_url: str):
        super().__init__()
        self.setWindowTitle("ConlangEngine Offline")
        self.resize(1440, 900)

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self._handle_download)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(server_url))
        self.setCentralWidget(self.browser)

    def _handle_download(self, download) -> None:
        suggested_name = download.suggestedFileName() or "ConlangEngine_export"
        downloads_dir = Path.home() / "Downloads"
        default_path = downloads_dir / suggested_name
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save ConlangEngine export",
            str(default_path),
            "All Files (*)",
        )

        if not file_path:
            download.cancel()
            return

        destination = Path(file_path)
        download.setDownloadDirectory(str(destination.parent))
        download.setDownloadFileName(destination.name)
        download.accept()


def main() -> None:
    storage_path = Path.home() / ".conlang-engine" / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    QWebEngineProfile.defaultProfile().setPersistentStoragePath(str(storage_path))

    server = LocalWebServer(get_web_root())
    server_url = server.start()
    window = MainWindow(server_url)
    window.show()

    try:
        sys.exit(app.exec())
    finally:
        server.stop()


if __name__ == "__main__":
    main()
