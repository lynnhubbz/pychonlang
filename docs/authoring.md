# Authoring a Language

A language is one `.json` file in `languages/`. Everything below can be edited
either by hand or through the GUI — the GUI just writes this same format.

## 1. Fields

| Field | Type | Meaning |
|---|---|---|
| `name`, `author`, `description` | string | Metadata only, doesn't affect generation. |
| `seed` | int | Reshuffles every generated word. Change it to explore variations without touching your rules. |
| `auto_casing` | bool | Match the output word's case to the input word's (`Hello` → `Kira`, not `kira`). |
| `letter_pathing` | `"Inclusion"` \| `"EndWord"` | What happens when the generator hits a dead end mid-word. `Inclusion` keeps going by relaxing exclusions; `EndWord` just stops the word early. Start with `Inclusion`. |
| `syllable_skew_min` / `_max` | float | How much shorter/longer a generated word can be vs. the English original's estimated syllable count. `0.8`/`1.5` is a reasonable range. |
| `consonants`, `vowels` | string | Space-separated single characters. Anything in `groups` below must come from these two lists. |
| `groups` | array | See §2. |
| `syllables` | array | See §3. |
| `rules` | array | See §4. |
| `vocabulary` | object | Exact whole-word overrides: `{"hello": "kira"}`. Case-insensitive match. |
| `roots` | object | Same idea, but for roots that affixes attach to (affixes aren't in the GUI yet). |
| `punctuation` | object | Replace a mark: `{".": "。", "?": "？"}`. Unlisted marks pass through unchanged. |

## 2. Letter groups

A group is a named bucket of letters with weights (higher = more common):

```json
{"key": "C", "name": "Consonants", "letters": {"k": 5, "s": 4, "w": 0.5}}
```

- `key` is a single character used to reference this group from syllable patterns.
- Every letter inside `letters` must already be listed in `consonants` or `vowels`.
- Typical setup: one group for consonants, one for vowels, plus small groups for
  special cases (e.g. a group that only contains `n` for a word-final nasal).

## 3. Syllables

A syllable pattern spells out group keys in order:

```json
{"pattern": "CV", "weight": 1.0}
```

`CV` = one letter from group `C`, then one from group `V`. `CVC`, `V`, `CCV`
all work as long as every character is a defined group key. Weight controls
how often that shape gets picked relative to the others.

## 4. Rules

Rules constrain letter/syllable choices contextually. Fill only the fields a
given rule type uses — leave the rest blank.

| `type` | Uses | Effect |
|---|---|---|
| `exclude_after` | `after`, `group`, `exclude` | After letter `after`, never pick any letter in `exclude` (optionally restricted to `group`). |
| `only_syllable_start` | `exclude` | Letters in `exclude` may only appear as the first letter of a syllable. |
| `never_in_one_syllable_word` | `exclude` | Letters in `exclude` never appear in a word that only has one syllable. |
| `syllable_only_last` | `syllable` | That syllable pattern can only be the last syllable of a word. |
| `syllable_only_first` | `syllable` | That syllable pattern can only be the first syllable of a word. |

Example — Japanese-style "w" only combines with "a":

```json
{"type": "exclude_after", "after": "w", "group": "V", "exclude": "iueo"}
```

## 5. Workflow

1. Start from `languages/example.json` (or **File → Open** in the GUI).
2. Add consonants/vowels, then groups, then syllables — the status bar
   tells you immediately if a group/syllable references something undefined.
3. Type a test sentence in the input box; the output updates live.
4. Add `rules` one at a time to shape the sound — each rule change is instant
   in the preview, so it's fast to tell whether a rule did what you wanted.
5. Nudge `seed` to see alternate output for the same rules without committing
   to anything.
6. **Ctrl+S** to save as your own file — `example.json` is left as the clean
   template.

## 6. Known gaps

- No affixes (prefixes/suffixes) from the GUI yet — use `roots` for now, or
  edit `bridge-net/JsonLanguage.cs` directly if you need them.
- Only the 5 rule types above are exposed. The underlying PLGL library
  supports much more (see `src/lib/PLGL/README.md`) if you need something
  custom — it just requires a small C# addition to `JsonLanguage.cs`.
