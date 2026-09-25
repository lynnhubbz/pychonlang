

## What it has

1. **Phonology (letter-level)** — weighted consonant/vowel groups, syllable pattern composition (`CV`, `CVC`...), 5 contextual exclusion rules, seed-based variation, punctuation remapping.
2. **Morphology (surface only)** — exact-match `vocabulary`/`roots` overrides. PLGL's affix engine exists underneath but isn't wired into your GUI/schema.
3. **Tooling** — live preview, validation, GUI editing, standalone Windows build, CI release pipeline, in-app help docs.

## What it lacks, how to add it, and rough fulfillment

| Layer | Status | What's missing | How to add |
|---|---|---|---|
| **Phonology** | ~50% | No true phonemic modeling (IPA features, place/manner/voicing) — just opaque letters | Add feature metadata to `letters` (`{symbol, ipa, manner, place, voice}`); rewrite rules to target feature classes instead of literal letters. Data-model change, medium effort. |
| **Morphology** | ~15% | No conjugation/declension, no affix UI, no agglutination/fusion typology | Wire up PLGL's existing prefix/suffix engine into a new GUI tab + schema fields (`prefixes`, `suffixes`, attachment rules). Medium effort — the underlying capability already exists in PLGL, just unexposed. |
| **Syntax** | 0% | No word order, no case marking, no agreement, no sentence structure at all — words translate 1:1 in place | Biggest gap. Needs a new pipeline stage: parse input into a rough syntactic structure (subject/verb/object at minimum), then reorder + inflect per your language's rules (SOV vs SVO, case suffixes) before per-word generation runs. Large effort — a real feature, not a tweak. |
| **Lexicon/Semantics** | ~20% | Flat word-pair overrides only; no meaning tracking, no derivation, no semantic fields | Extend `vocabulary` into a richer structure (`{word, meaning, part_of_speech, derived_from}`); add a searchable dictionary view. Medium effort, mostly GUI + schema. |
| **Orthography/ writing system/ Logograms / Logographs** | ~10% | Output is just Latin/Unicode text through PLGL; no logograms, no invented scripts, no distinct spelling-vs-pronunciation | Custom scripts: PUA codepoints + bundled fonts (already discussed). Logograms: separate non-phonetic generation path you'd write yourself. Large effort for true logography, smaller for custom-script Latin substitution. |
| **Pragmatics** | 0% | No register, politeness, discourse markers | Rarely automated even in pro tools. Skip unless you specifically want it — low value for the effort. |
| **Diachronics (sound change)** | 0% | No "proto-language evolves into daughter language" mechanism | New standalone module: apply a sequence of regular sound-change rules to an existing language, output a derived one. Medium-large effort, independent of everything else — could be built without touching syntax/morphology at all. |

## Honest overall picture

Your app is a **phonology generator with a lexicon patch layer** — genuinely solid at the one thing it does (how a language sounds), close to zero coverage on grammar (syntax especially), light on true phonetic accuracy and morphology, and no writing-system layer beyond passing through Unicode.

**If you want to prioritize one next feature for real conlang depth**, in order of "most conlang-legitimacy per effort spent":
1. **Morphology/affixes** — cheapest big win, PLGL already has the engine
2. **Syntax (word order + basic case marking)** — hardest, but the single biggest thing separating "letter generator" from "language"
3. **Phonetic/IPA modeling** — matters most if you care about scientific accuracy specifically, less about feature completeness

Want to pick one and actually start building it, or is this more a scoping/roadmap check for now?