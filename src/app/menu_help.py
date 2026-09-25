from pathlib import Path
import markdown2
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication, QDialog, QTextBrowser, QVBoxLayout

from paths import app_root

ASSETS = app_root() / "assets"

# unchanged below — css_file = ASSETS / ("md-dark.css" if _is_dark_mode() else "md-light.css")

GFM_EXTRAS = ["tables", "fenced-code-blocks", "strike", "task_list",
              "header-ids", "code-friendly", "cuddled-lists"]




def _is_dark_mode() -> bool:
    pal = QApplication.palette()
    return pal.window().color().lightness() < 128


class HelpDialog(QDialog):
    def __init__(self, docs_root: Path, doc_name: str = "authoring.md", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Help — {doc_name}")
        self.resize(760, 640)

        self._path = docs_root / doc_name
        self._browser = QTextBrowser(openExternalLinks=True)
        lay = QVBoxLayout(self)
        lay.addWidget(self._browser)

        self._render()
        QApplication.instance().installEventFilter(self)

    def _render(self):
        if not self._path.exists():
            self._browser.setPlainText(f"Missing: {self._path}")
            return
        css_file = ASSETS / ("md-dark.css" if _is_dark_mode() else "md-light.css")
        css = css_file.read_text(encoding="utf-8") if css_file.exists() else ""
        body = markdown2.markdown(self._path.read_text(encoding="utf-8"), extras=GFM_EXTRAS)
        self._browser.setHtml(f"<style>{css}</style>{body}")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ApplicationPaletteChange:
            self._render()
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)