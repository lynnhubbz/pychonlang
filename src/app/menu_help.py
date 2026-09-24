from pathlib import Path
from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout


class HelpDialog(QDialog):
    def __init__(self, docs_root: Path, doc_name: str = "authoring.md", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Authoring a Language")
        self.resize(700, 600)

        browser = QTextBrowser(openExternalLinks=True)
        path = docs_root / doc_name
        browser.setMarkdown(path.read_text(encoding="utf-8")) if path.exists() \
            else browser.setPlainText(f"Missing: {path}")

        lay = QVBoxLayout(self)
        lay.addWidget(browser)