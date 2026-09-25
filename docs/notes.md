Based on everything built in this thread, here's the actual state:

**Working:**
1. Phonetic generation (consonants/vowels → weighted letter groups → syllable patterns)
2. 5 contextual rule types (exclusion-based)
3. Exact-match lexicon overrides (`vocabulary`, `roots`)
4. Punctuation remapping
5. Live preview, seed-based variation, GUI validation
6. In-app help docs (dark/light GFM rendering)
7. Standalone Windows build + release pipeline

**Gaps, roughly by effort to add:**

| Gap | Why it's missing | Effort |
|---|---|---|
| Affixes (prefixes/suffixes) | PLGL supports them; never wired into the GUI/JSON schema | Small — mostly GUI + schema work |
| Custom rule types beyond the 5 | Only a fixed switch statement in `JsonLanguage.cs` | Small per rule, but each one needs a C# edit + rebuild |
| RTL layout for the output widget | One Qt property, just never set | Trivial |
| Custom/invented glyphs (non-Unicode scripts) | Needs PUA codepoints + bundled font, no code exists yet | Medium |
| Logographic generation mode | PLGL is phonetic-only; would need an entirely separate generation path you write yourself | Large — real feature, not a tweak |
| Structured lexicon (parts of speech, grammar, searchable dictionary view) | `vocabulary`/`roots` are flat string maps only | Medium |
| Non-Windows builds | Never tested; pythonnet/CoreCLR on Linux/macOS unverified | Unknown until tried |
| TOML instead of JSON | Explicitly on your repo's Todo, not started | Medium — full C# parser rewrite |

**Worth being blunt about the bigger picture:** this is a phonology + basic morphology generator with a nice editing GUI — genuinely useful for what most conlangers actually need first (how words *sound*). Grammar (syntax, cases, tense systems), semantics, and non-phonetic writing systems are entirely separate problems PLGL was never built to solve, and none of that exists in any form yet.
