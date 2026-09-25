"""Pychonlang — build a PLGL conlang entirely from a GUI, with live preview."""
import json
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)


if __package__:
    from .. import bridge
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import bridge  

from paths import app_root

ROOT = app_root()
LANG_DIR = ROOT / "languages"

RULE_TYPES = {
    "exclude_after": "After letter [After], never pick [Letters] (only in group [Group] if set)",
    "only_syllable_start": "[Letters] may only open a syllable",
    "never_in_one_syllable_word": "[Letters] never appear in 1-syllable words",
    "syllable_only_last": "Syllable pattern [Syllable] only at word end",
    "syllable_only_first": "Syllable pattern [Syllable] only at word start",
}


# ---------------------------------------------------------------- widgets
class TableEditor(QWidget):
    """Editable table with Add/Remove buttons. columns = [(header, choices|None)]."""
    changed = Signal()

    def __init__(self, columns, help_text=""):
        super().__init__()
        self.columns = columns
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemChanged.connect(lambda *_: self.changed.emit())

        add, rem = QPushButton("+ Add row"), QPushButton("− Remove selected")
        add.clicked.connect(lambda: (self.add_row(), self.changed.emit()))
        rem.clicked.connect(self.remove_selected)
        btns = QHBoxLayout()
        btns.addWidget(add)
        btns.addWidget(rem)
        btns.addStretch()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        if help_text:
            lbl = QLabel(help_text)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)
        lay.addWidget(self.table)
        lay.addLayout(btns)

    def add_row(self, values=None):
        values = values or [""] * len(self.columns)
        self.table.blockSignals(True)
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, (_, choices) in enumerate(self.columns):
            val = str(values[c]) if c < len(values) else ""
            if choices:
                cb = QComboBox()
                cb.addItems(choices)
                if val in choices:
                    cb.setCurrentText(val)
                cb.currentTextChanged.connect(lambda *_: self.changed.emit())
                self.table.setCellWidget(r, c, cb)
            else:
                self.table.setItem(r, c, QTableWidgetItem(val))
        self.table.blockSignals(False)

    def remove_selected(self):
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)
        self.changed.emit()

    def rows(self):
        out = []
        for r in range(self.table.rowCount()):
            row = []
            for c, (_, choices) in enumerate(self.columns):
                if choices:
                    row.append(self.table.cellWidget(r, c).currentText())
                else:
                    it = self.table.item(r, c)
                    row.append(it.text().strip() if it else "")
            if any(row):
                out.append(row)
        return out

    def set_rows(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            self.add_row(row)


# ---------------------------------------------------------------- main window
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.path = None
        self.loading = False
        self.timer = QTimer(self, singleShot=True, interval=300)
        self.timer.timeout.connect(self.preview)

        # --- General tab
        self.name, self.author, self.desc = QLineEdit(), QLineEdit(), QLineEdit()
        self.seed = QSpinBox(maximum=99999)
        self.casing = QCheckBox("Match original word casing")
        self.pathing = QComboBox()
        self.pathing.addItems(["Inclusion", "EndWord"])
        self.skmin = QDoubleSpinBox(decimals=2, minimum=0.1, maximum=5, singleStep=0.1)
        self.skmax = QDoubleSpinBox(decimals=2, minimum=0.1, maximum=5, singleStep=0.1)
        gen = QWidget()
        f = QFormLayout(gen)
        f.addRow("Name", self.name)
        f.addRow("Author", self.author)
        f.addRow("Description", self.desc)
        f.addRow("Seed (reshuffles all words)", self.seed)
        f.addRow("", self.casing)
        f.addRow("Dead-end letter path", self.pathing)
        f.addRow("Word length min ×", self.skmin)
        f.addRow("Word length max ×", self.skmax)

        # --- Letters tab
        self.cons, self.vows = QLineEdit(), QLineEdit()
        let = QWidget()
        f2 = QFormLayout(let)
        f2.addRow(QLabel("One character per letter, separated by spaces. "
                         "Special letters (ŝ, ċ, ü, ŋ…) are fine."))
        f2.addRow("Consonants", self.cons)
        f2.addRow("Vowels", self.vows)

        # --- Structure tab
        self.groups = TableEditor(
            [("Key (1 char)", None), ("Name", None), ("Letters  e.g.  a:5 i:3 u:1", None)],
            "Letter groups: a key + weighted letters (higher weight = more common).")
        self.syls = TableEditor(
            [("Pattern (group keys)  e.g. CV, CVC", None), ("Weight", None)],
            "Syllable shapes built from group keys.")
        struct = QWidget()
        sl = QVBoxLayout(struct)
        sl.addWidget(self.groups, 3)
        sl.addWidget(self.syls, 2)

        # --- Rules tab
        self.rules = TableEditor(
            [("Type", list(RULE_TYPES)), ("After", None), ("Group", None),
             ("Syllable", None), ("Letters", None)],
            "Fill only the columns the rule uses:\n" +
            "\n".join(f"• {k}: {v}" for k, v in RULE_TYPES.items()))

        # --- Words tab
        self.vocab = TableEditor([("English word", None), ("Conlang word", None)],
                                 "Fixed translations (exact whole word).")
        self.roots = TableEditor([("English root", None), ("Conlang root", None)],
                                 "Fixed roots (affixed forms still follow them).")
        words = QWidget()
        wl = QVBoxLayout(words)
        wl.addWidget(self.vocab)
        wl.addWidget(self.roots)

        # --- Punctuation tab
        self.punct = TableEditor([("Mark", None), ("Becomes", None)],
                                 "Replace punctuation marks. Unlisted marks stay as-is.")

        tabs = QTabWidget()
        for w, t in [(gen, "General"), (let, "Letters"), (struct, "Structure"),
                     (self.rules, "Rules"), (words, "Words"), (self.punct, "Punctuation")]:
            tabs.addTab(w, t)

        # --- Preview side
        self.inp = QPlainTextEdit(placeholderText="Type English here… use [Name] to keep a word as-is.")
        self.out = QPlainTextEdit(readOnly=True)
        self.status = QLabel()
        self.status.setWordWrap(True)
        copy = QPushButton("Copy output")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.out.toPlainText()))
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.addWidget(QLabel("Input"))
        rl.addWidget(self.inp)
        rl.addWidget(QLabel("Output"))
        rl.addWidget(self.out)
        rl.addWidget(self.status)
        rl.addWidget(copy)

        split = QSplitter()
        split.addWidget(tabs)
        split.addWidget(right)
        split.setSizes([650, 450])
        self.setCentralWidget(split)

        # --- change tracking -> live preview
        for w in (self.name, self.author, self.desc, self.cons, self.vows):
            w.textChanged.connect(self.touch)
        for w in (self.seed, self.skmin, self.skmax):
            w.valueChanged.connect(self.touch)
        self.casing.toggled.connect(self.touch)
        self.pathing.currentTextChanged.connect(self.touch)
        for t in (self.groups, self.syls, self.rules, self.vocab, self.roots, self.punct):
            t.changed.connect(self.touch)
        self.inp.textChanged.connect(self.timer.start)

        # --- menu
        m = self.menuBar().addMenu("&File")
        for text, key, fn in [("&Open…", QKeySequence.Open, self.open),
                              ("&Save", QKeySequence.Save, self.save),
                              ("Save &As…", QKeySequence.SaveAs, self.save_as)]:
            a = QAction(text, self, shortcut=key)
            a.triggered.connect(fn)
            m.addAction(a)

        from menu_help import HelpDialog   # match your existing import style

        help_menu = self.menuBar().addMenu("&Help")
        a = QAction("&Authoring Guide", self)
        a.triggered.connect(lambda: HelpDialog(
            ROOT / "docs", parent=self
        ).exec())
        help_menu.addAction(a)

        a2 = QAction("&About PLGL", self)
        a2.triggered.connect(lambda: HelpDialog(
            ROOT / "docs", doc_name="doc-lib.md", parent=self
        ).exec())
        help_menu.addAction(a2)

        self.load(LANG_DIR / "example.json")
        self.inp.setPlainText("Hello, the field of Enna is ablaze with flowers!")
        self.resize(1150, 700)

    # ---------------- dict <-> widgets
    def to_dict(self):
        def num(s, d):
            try:
                return float(s)
            except ValueError:
                return d

        groups = []
        for key, name, letters in self.groups.rows():
            lw = {}
            for tok in letters.split():
                ch, _, w = tok.partition(":")
                if ch:
                    lw[ch[0]] = num(w, 1.0) if w else 1.0
            groups.append({"key": key[:1], "name": name, "letters": lw})
        return {
            "name": self.name.text(), "author": self.author.text(),
            "description": self.desc.text(), "seed": self.seed.value(),
            "auto_casing": self.casing.isChecked(),
            "letter_pathing": self.pathing.currentText(),
            "syllable_skew_min": self.skmin.value(), "syllable_skew_max": self.skmax.value(),
            "consonants": self.cons.text(), "vowels": self.vows.text(),
            "groups": groups,
            "syllables": [{"pattern": p, "weight": num(w, 1.0)} for p, w in self.syls.rows()],
            "rules": [{"type": t, "after": a, "group": g, "syllable": s, "exclude": x}
                      for t, a, g, s, x in self.rules.rows()],
            "vocabulary": {k: v for k, v in self.vocab.rows()},
            "roots": {k: v for k, v in self.roots.rows()},
            "punctuation": {k: v for k, v in self.punct.rows()},
        }

    def from_dict(self, d):
        self.loading = True
        self.name.setText(d.get("name", ""))
        self.author.setText(d.get("author", ""))
        self.desc.setText(d.get("description", ""))
        self.seed.setValue(int(d.get("seed", 0)))
        self.casing.setChecked(d.get("auto_casing", True))
        self.pathing.setCurrentText(d.get("letter_pathing", "Inclusion"))
        self.skmin.setValue(d.get("syllable_skew_min", 0.8))
        self.skmax.setValue(d.get("syllable_skew_max", 1.2))
        self.cons.setText(d.get("consonants", ""))
        self.vows.setText(d.get("vowels", ""))
        self.groups.set_rows([[g["key"], g.get("name", ""),
                               " ".join(f"{k}:{v:g}" for k, v in g["letters"].items())]
                              for g in d.get("groups", [])])
        self.syls.set_rows([[s["pattern"], f"{s.get('weight', 1):g}"] for s in d.get("syllables", [])])
        self.rules.set_rows([[r.get("type", ""), r.get("after", ""), r.get("group", ""),
                              r.get("syllable", ""), r.get("exclude", "")] for r in d.get("rules", [])])
        self.vocab.set_rows(list(d.get("vocabulary", {}).items()))
        self.roots.set_rows(list(d.get("roots", {}).items()))
        self.punct.set_rows(list(d.get("punctuation", {}).items()))
        self.loading = False

    # ---------------- validation + preview
    @staticmethod
    def validate(d):
        alphabet = set((d["consonants"] + d["vowels"]).replace(" ", "").replace(",", ""))
        keys = {g["key"] for g in d["groups"]}
        if not d["groups"]:
            return "Add at least one letter group (Structure tab)."
        if not d["syllables"]:
            return "Add at least one syllable pattern (Structure tab)."
        for g in d["groups"]:
            if not g["key"]:
                return "A letter group has no key."
            if not g["letters"]:
                return f"Group '{g['key']}' has no letters."
            bad = [c for c in g["letters"] if c not in alphabet]
            if bad:
                return f"Group '{g['key']}' uses {bad}, not in Consonants/Vowels (Letters tab)."
        for s in d["syllables"]:
            bad = [c for c in s["pattern"] if c not in keys]
            if bad:
                return f"Syllable '{s['pattern']}' uses unknown group key(s) {bad}."
        return None

    def touch(self, *_):
        if not self.loading:
            self.setWindowModified(True)
            self.timer.start()

    def preview(self):
        d = self.to_dict()
        err = self.validate(d)
        if err:
            self.status.setText(f"⚠ {err}")
            return
        try:
            self.out.setPlainText(bridge.generate(d, self.inp.toPlainText()))
            self.status.setText("✓ OK")
        except Exception as e:  # .NET exceptions surface here
            self.status.setText(f"⚠ Generator error: {str(e).splitlines()[0]}")

    # ---------------- files
    def load(self, path):
        with open(path, encoding="utf-8") as fh:
            self.from_dict(json.load(fh))
        self.path = Path(path)
        self.setWindowTitle(f"Pychonlang — {self.path.name}[*]")
        self.setWindowModified(False)
        self.timer.start()

    def open(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open language", str(LANG_DIR), "Language (*.json)")
        if p:
            self.load(p)

    def save(self):
        if not self.path or self.path.name == "example.json":
            return self.save_as()   # keep the example as a clean template
        self._write()

    def _write(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, ensure_ascii=False, indent=2)
        self.setWindowModified(False)

    def save_as(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save language", str(LANG_DIR), "Language (*.json)")
        if p:
            self.path = Path(p)
            self.setWindowTitle(f"Pychonlang — {self.path.name}[*]")
            self._write()

    def closeEvent(self, e):
        if self.isWindowModified():
            r = QMessageBox.question(self, "Unsaved changes", "Save before closing?",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if r == QMessageBox.Save:
                self.save()
            elif r == QMessageBox.Cancel:
                return e.ignore()
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Main()
    w.show()
    sys.exit(app.exec())
