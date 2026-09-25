using System.Text.Json;
using PLGL;

namespace PLGLBridge
{
    /// <summary>A PLGL language built entirely from a JSON definition (edited by the GUI).</summary>
    public class JsonLanguage : Language
    {
        public JsonLanguage(string json)
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;

            META_Name = Str(r, "name", "Unnamed");
            META_Author = Str(r, "author", "");
            META_Description = Str(r, "description", "");

            // ---- Options ----
            Options.SeedOffset = Int(r, "seed", 0);
            Options.MemorizeWords = true;
            Options.AllowAutomaticCasing = Bool(r, "auto_casing", true);
            Options.AllowRandomCase = false;
            Options.CountSyllables = Options.EnglishSyllableCount;
            double skMin = Dbl(r, "syllable_skew_min", 0.8), skMax = Dbl(r, "syllable_skew_max", 1.2);
            Options.SyllableSkewMin = _ => skMin;
            Options.SyllableSkewMax = _ => skMax;
            Options.LetterPathing = Str(r, "letter_pathing", "EndWord") == "Inclusion"
                ? LanguageOptions.PathSelection.Inclusion : LanguageOptions.PathSelection.EndWord;

            // ---- Fixed processing pipeline (same as the PLGL examples) ----
            AddFilter("Delimiter", " \t\n");
            AddFilter("Compound", "");
            AddFilter("Letters", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ");
            AddFilter("Numbers", "1234567890");
            AddFilter("Punctuation", ".,?!;:'\"-#$%()/");
            AddFilter("Escape", "[]");

            OnDeconstruct += (lg, c) => lg.DECONSTRUCT_MergeBlocks(c, "PUNCTUATION", "LETTERS", "LETTERS", "'", "LETTERS");
            OnDeconstruct += (lg, c) => lg.DECONSTRUCT_MergeBlocks(c, "PUNCTUATION", "NUMBERS", "NUMBERS", ".", "NUMBERS");
            OnDeconstruct += (lg, c) => lg.DECONSTRUCT_MergeBlocks(c, "PUNCTUATION", "NUMBERS", "NUMBERS", ",", "NUMBERS");
            OnDeconstruct += (lg, c) => lg.DECONSTRUCT_ChangeFilter(c, "PUNCTUATION", "LETTERS", "LETTERS", "-", "COMPOUND");
            OnDeconstruct += (lg, c) => lg.DECONSTRUCT_MergeBlocks(c, "LETTERS", "ESCAPE", "ESCAPE", "ESCAPE");

            OnConstruct += (lg, w) => lg.CONSTRUCT_KeepAsIs(w, "UNDEFINED");
            OnConstruct += (lg, w) => lg.CONSTRUCT_KeepAsIs(w, "DELIMITER");
            OnConstruct += (lg, w) => lg.CONSTRUCT_KeepAsIs(w, "NUMBERS");
            OnConstruct += (lg, w) => lg.CONSTRUCT_KeepAsIs(w, "COMPOUND");
            OnConstruct += (lg, w) => lg.CONSTRUCT_Generate(w, "LETTERS");
            OnConstruct += (lg, w) => lg.CONSTRUCT_Within(w, "ESCAPE", 1, 2); // [Name] stays as Name
            OnConstruct += (lg, w) => Punctuation.Process(lg, w, "PUNCTUATION");

            // Punctuation: map every mark (unmapped ones pass through unchanged)
            var punct = new Dictionary<string, string>();
            foreach (var p in ".,?!;:'\"-#$%()/") punct[p.ToString()] = p.ToString();
            if (r.TryGetProperty("punctuation", out var pm))
                foreach (var kv in pm.EnumerateObject()) punct[kv.Name] = kv.Value.GetString() ?? "";
            foreach (var kv in punct) { var v = kv.Value; Punctuation.Add(kv.Key, _ => v); }

            // ---- Alphabet ----
            foreach (var c in Chars(r, "consonants")) Alphabet.AddConsonant(c, (char.ToLower(c), char.ToUpper(c)));
            foreach (var c in Chars(r, "vowels")) Alphabet.AddVowel(c, (char.ToLower(c), char.ToUpper(c)));

            // ---- Letter groups & syllables ----
            if (r.TryGetProperty("groups", out var groups))
                foreach (var g in groups.EnumerateArray())
                {
                    var letters = g.GetProperty("letters").EnumerateObject()
                        .Select(l => (l.Name[0], l.Value.GetDouble())).ToArray();
                    Structure.AddGroup(g.GetProperty("key").GetString()[0], Str(g, "name", ""), letters);
                }
            if (r.TryGetProperty("syllables", out var syl))
                foreach (var s in syl.EnumerateArray())
                    Structure.AddSyllable(s.GetProperty("pattern").GetString(), Dbl(s, "weight", 1.0));

            // ---- Rules ----
            if (r.TryGetProperty("rules", out var rules))
                foreach (var rule in rules.EnumerateArray()) AddRule(rule);

            // ---- Lexicon ----
            if (r.TryGetProperty("vocabulary", out var voc))
                foreach (var kv in voc.EnumerateObject()) Lexicon.AddVocabulary(kv.Name, kv.Value.GetString());
            if (r.TryGetProperty("roots", out var roots))
                foreach (var kv in roots.EnumerateObject()) Lexicon.AddRoot(kv.Name, kv.Value.GetString());
        }

        private void AddRule(JsonElement rule)
        {
            string type = Str(rule, "type", "");
            char[] excl = Str(rule, "exclude", "").Replace(" ", "").ToCharArray();
            string after = Str(rule, "after", "").Trim();
            string group = Str(rule, "group", "").Trim();
            string syllable = Str(rule, "syllable", "").Trim();

            switch (type)
            {
                case "exclude_after": // after letter X, don't pick these letters (optionally only in group G)
                    if (after.Length == 0 || excl.Length == 0) return;
                    char a = after[0];
                    OnLetterSelection += (lg, sel, word, s, last, cur, max) =>
                        lg.SELECT_Exclude(cur != 0 && last != null && last.Letter.Key == a &&
                            (group.Length == 0 || lg.SELECT_Template(s, cur)?.Key == group[0]), excl);
                    break;

                case "only_syllable_start": // these letters may only open a syllable
                    if (excl.Length == 0) return;
                    OnLetterSelection += (lg, sel, word, s, last, cur, max) => lg.SELECT_Exclude(cur != 0, excl);
                    break;

                case "never_in_one_syllable_word":
                    if (excl.Length == 0) return;
                    OnLetterSelection += (lg, sel, word, s, last, cur, max) => lg.SELECT_Exclude(word.Syllables.Count == 1, excl);
                    break;

                case "syllable_only_last": // syllable pattern only at word end
                    if (syllable.Length == 0) return;
                    OnSyllableSelection += (lg, sel, word, last, cur, max) => lg.SELECT_Exclude(cur < max - 1 || max == 1, syllable);
                    break;

                case "syllable_only_first": // syllable pattern only at word start
                    if (syllable.Length == 0) return;
                    OnSyllableSelection += (lg, sel, word, last, cur, max) => lg.SELECT_Exclude(cur != 0, syllable);
                    break;
            }
        }

        // ---- JSON helpers ----
        static string Str(JsonElement e, string k, string d) =>
            e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : d;
        static int Int(JsonElement e, string k, int d) =>
            e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetInt32() : d;
        static double Dbl(JsonElement e, string k, double d) =>
            e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : d;
        static bool Bool(JsonElement e, string k, bool d) =>
            e.TryGetProperty(k, out var v) && (v.ValueKind == JsonValueKind.True || v.ValueKind == JsonValueKind.False) ? v.GetBoolean() : d;
        static IEnumerable<char> Chars(JsonElement e, string k) =>
            Str(e, k, "").Where(c => !char.IsWhiteSpace(c) && c != ',').Distinct();
    }

    /// <summary>Thin entry point for Python.</summary>
    public static class Bridge
    {
        public static string Generate(string json, string text)
        {
            var lg = new LanguageGenerator { Language = new JsonLanguage(json) };
            var lines = text.Replace("\r\n", "\n").Split('\n');
            return string.Join("\n", lines.Select(l => l.Trim().Length == 0 ? l : lg.GenerateClean(l)));
        }
    }
}
