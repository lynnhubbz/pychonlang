"""Word inflection (conjugation/declension) via ConlangEngine's morphology engine.

Runs ConlangEngine's JavaScript inside Python using mini-racer.
The JS bundle is built by `build_js()` in scripts/build/main.py.
"""
import json
from pathlib import Path

from py_mini_racer import MiniRacer


class Morphology:
    def __init__(self, bundle_path: Path):
        self._js = MiniRacer()
        self._js.eval(Path(bundle_path).read_text(encoding="utf-8"))

    def paradigm(self, word: str, lang: dict, word_class: str = "") -> list[dict]:
        """Return every inflected form of `word` for the rules in `lang`.

        word_class: e.g. "noun" to only use rules for nouns. Blank = every rule.
        Each result: {"ruleName": ..., "personName": ..., "result": ...}
        """
        morph = lang.get("morphology", {})
        if not word_class:  # blank = include every class any rule mentions
            classes = {c.strip() for r in morph.get("rules", [])
                       for c in (r.get("appliesTo") or "all").split(",")}
            word_class = ",".join(sorted(classes)) or "all"
        config = {
            # pychonlang stores letters space-separated; ConlangEngine wants commas
            "vowels": ",".join(lang.get("vowels", "").split()),
            "consonants": ",".join(lang.get("consonants", "").split()),
            "grammarRules": morph.get("rules", []),
            "personRules": morph.get("persons", ""),
        }
        mode = "affix" if config["personRules"] else "compact"
        code = (
            f"JSON.stringify(CE.generateParadigm("
            f"{json.dumps(word)}, {json.dumps(config)}, {{inflectionMode: {json.dumps(mode)}, wordClass: {json.dumps(word_class)}}}))"
        )
        return json.loads(self._js.eval(code))

    def close(self) -> None:
        """Shut down the JS engine. Call this when the app closes."""
        self._js.close()
