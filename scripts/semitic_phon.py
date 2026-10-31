"""Does a Semitic form fit its cognates under the regular sound correspondences?   (a sanity check before giving a term its script)

Every consonant of a form is mapped to the Proto-Semitic consonants it can continue (Huehnergard's correspondences; letters of a script that
merge several sounds map to all of them: Hebrew ש is *š, *ś or *ṯ; Aramaic ע is *ʕ, *ġ or, later, *ṣ́). Two forms agree if, once the weak
consonants (ʔ h w y, which come and go with vowels and affixes) are set aside, their strong consonants line up one to one with a common
Proto-Semitic value at every position. A trailing feminine -t on one side is allowed.

  check("uga", "bgy", [("ar", "بغى"), ("he", "בעה")]) -> (False, ...)   Ugaritic g is only *g; Arabic غ and Hebrew ע point to *ġ
  check("uga", "bġy", [("ar", "بغى")])                -> (True, ...)

Forms may be in their script or in a transliteration; scripts are read back through the converters' own tables."""
import re, unicodedata as U
from tr2script import abjad

PS = "ʔ b g d h w z ḥ ṭ y k l m n s ʕ p ṣ q r š t ṯ ḏ ḫ ġ ṯ̣ ś ṣ́".split()
WEAK = {"ʔ", "h", "w", "y"}

def _m(**kw):
    return {k: set(v.split()) for k, v in kw.items()}

# letter (as transliterated) -> Proto-Semitic consonants it may continue, per language family
COMMON = _m(b="b", g="g", d="d", h="h", w="w", z="z", y="y", k="k", l="l", m="m", n="n", r="r", t="t", q="q", p="p")
REFLEX = {
    "ar": {**COMMON, **_m(ʔ="ʔ", ḥ="ḥ", ṭ="ṭ", s="s š", ʕ="ʕ", ṣ="ṣ", f="p", š="ś", ṯ="ṯ", ḏ="ḏ", ḫ="ḫ", ġ="ġ", ẓ="ṯ̣", ḏ̣="ṯ̣", ḍ="ṣ́", j="g", ǧ="g", p="p")},
    "he": {**COMMON, **_m(ʔ="ʔ", z="z ḏ", ḥ="ḥ ḫ", ṭ="ṭ", s="s", ʕ="ʕ ġ", ṣ="ṣ ṣ́ ṯ̣", š="š ṯ ś", ś="ś", f="p")},
    "arc": {**COMMON, **_m(ʔ="ʔ", z="z", d="d ḏ", ḥ="ḥ ḫ", ṭ="ṭ ṯ̣", s="s ś", ʕ="ʕ ġ ṣ́", ṣ="ṣ", q="q ṣ́", š="š", t="t ṯ", f="p")},
    "uga": {**COMMON, **_m(ʔ="ʔ", d="d ḏ", ḥ="ḥ", ṭ="ṭ", s="s", ʕ="ʕ", ṣ="ṣ ṣ́", š="š ś", ṯ="ṯ", ḏ="ḏ", ḫ="ḫ", ġ="ġ", ẓ="ṯ̣", ṯ̣="ṯ̣")},
    "akk": {**COMMON, **_m(ʔ="ʔ ḥ ʕ ġ h", z="z ḏ", ṭ="ṭ", s="s", ṣ="ṣ ṣ́ ṯ̣", š="š ś ṯ", ḫ="ḫ", e="ʔ ḥ ʕ ġ h")},
    "eth": {**COMMON, **_m(ʔ="ʔ", z="z ḏ", ḥ="ḥ", ṭ="ṭ", s="s š ṯ", ʕ="ʕ ġ", ṣ="ṣ ṯ̣", ś="ś", ḍ="ṣ́", ṣ́="ṣ́", f="p", ḫ="ḫ", x="ḫ", q="q", č̣="ṭ ṣ", č="k", ǧ="g d", ñ="n", ž="z")},
    "osa": {**COMMON, **_m(ʔ="ʔ", ḥ="ḥ", ṭ="ṭ", s="š s ś", ʕ="ʕ", ṣ="ṣ", f="p", š="ś s", ś="s ś", ṯ="ṯ", ḏ="ḏ", ḫ="ḫ", ġ="ġ", ẓ="ṯ̣", ḍ="ṣ́")},
}
FAMILY = {"ar": "ar", "he": "he", "hbo": "he", "phn": "he", "obm": "he", "xpu": "he", "arc": "arc", "arc-old": "arc", "arc-imp": "arc",
          "arc-pal": "arc", "arc-nab": "arc", "arc-bib": "arc", "jpa": "arc", "tmr": "arc", "sam": "arc", "syc": "arc", "myz": "arc",
          "uga": "uga", "akk": "akk", "xeb": "akk", "xsa": "osa", "inm": "osa", "xqt": "osa", "xhd": "osa", "sem-srb": "osa",
          **{c: "eth" for c in "gez am ti tig har stv zwa gft gru sgw agj mvz wle".split()}}

# script letters back to the transliteration letters above
_BACK = {}
for table in ("he", "syc", "phn", "uga", "osa", "armi", "palm", "nbat", "sam"):
    for lat, ch in abjad.PAIRS.get(table, []):
        _BACK.setdefault(ch, lat)
for fin, base in {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}.items():
    _BACK[fin] = _BACK.get(base, "")
_BACK.update({"ء": "ʔ", "أ": "ʔ", "إ": "ʔ", "آ": "ʔ", "ؤ": "ʔ", "ئ": "ʔ", "ا": "", "ب": "b", "ت": "t", "ة": "t", "ث": "ṯ", "ج": "j", "ح": "ḥ",
              "خ": "ḫ", "د": "d", "ذ": "ḏ", "ر": "r", "ز": "z", "س": "s", "ش": "š", "ص": "ṣ", "ض": "ḍ", "ط": "ṭ", "ظ": "ẓ", "ع": "ʕ", "غ": "ġ",
              "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "و": "w", "ي": "y", "ى": "y"})
_TRSRC = {"ˀ": "ʔ", "ʾ": "ʔ", "ʼ": "ʔ", "'": "ʔ", "ˁ": "ʕ", "ʿ": "ʕ", "ḳ": "q", "θ": "ṯ", "ð": "ḏ", "γ": "ġ", "ŝ": "ś", "ẑ": "ś", "ṣ̂": "ṣ́",
          "ẓ̂": "ṣ́", "ḇ": "b", "ḡ": "g", "ḵ": "k", "p̄": "f", "ṯ̣": "ṯ̣", "ḏ̣": "ḏ̣"}

def letters(code, form):
    """The consonants of a form, as transliteration letters (script read back; vowels, marks, hyphens dropped)."""
    s = U.normalize("NFC", form.strip().lstrip("*"))
    if re.search(r"[ሀ-᎟]", s):                     # Ethiopic: the consonant of each syllable
        from tr2script import ethiopic
        inv, _ = ethiopic._inverse()
        back = {ch: re.sub("[äuiaeəo]$", "", lat) for lat, ch in inv.items()}
        s = "".join(back.get(ch, "") for ch in s)
    elif re.search(r"[֐-׿؀-ۿ܀-ݏࠀ-࠿\U00010380-\U0001039f\U00010900-\U0001091f\U00010840-\U000108af\U00010a60-\U00010a7f]", s):
        s = "".join(_BACK.get(ch, "") for ch in s if not U.combining(ch) and not (0x64B <= ord(ch) <= 0x65F))
    for a, b in _TRSRC.items():
        s = s.replace(a, b)
    s = U.normalize("NFD", s)
    out = []                                                 # letters: a base character with its combining marks
    for ch in s:
        if U.combining(ch) and out:
            out[-1] += ch
        else:
            out.append(ch)
    vowels = set("aeiouəɛɔäæ")
    out = [U.normalize("NFC", g) for g in out if g[0].lower() not in vowels and g[0] not in "-.·()[] ʷ'" and not g[0].isspace() and not g[0].isdigit()]
    return [c for j, c in enumerate(out) if j == 0 or c != out[j - 1]]          # gemination

def ps_sets(code, form):
    """-> [set of Proto-Semitic consonants] for each consonant, or None if a letter is unknown for the language."""
    fam = FAMILY.get(code)
    if not fam:
        return None
    table = REFLEX[fam]
    out = []
    for c in letters(code, form):
        if c not in table:
            return None
        out.append(table[c])
    return out

def _strong(sets):
    return [s for s in sets if not s <= WEAK]

def _variants(sets):
    """The strong consonants, and the same without the affixes that are not part of the root: a final feminine -t, an Akkadian final -m
    (mimation), a reflexive t- after a weak prefix consonant (Aramaic ʔit-, Hebrew hit-: ʔitpallaš has the root p-l-š)."""
    s = _strong(sets)
    out = [s]
    if len(sets) > 1 and sets[0] <= WEAK and "t" in sets[1]:
        out.append(_strong(sets[2:]))
    for v in list(out):
        if len(v) > 1 and "t" in v[-1]:
            out.append(v[:-1])
        if len(v) > 2 and v[-1] == {"m"}:
            out.append(v[:-1])
    return out

def agree(a, b):
    """Two forms agree if, for some way of setting their affixes aside, their strong consonants line up one to one with a common value."""
    return any(len(x) == len(y) and x and all(p & q for p, q in zip(x, y)) for x in _variants(a) for y in _variants(b))

def check(code, form, comparanda):
    """-> (True/False/None, why). None: nothing comparable (no cognates in a language the table knows), so no verdict."""
    me = ps_sets(code, form)
    if me is None:
        return None, f"a letter of {form!r} has no correspondence in the table"
    tried, ok = [], []
    for c2, f2 in comparanda:
        other = ps_sets(c2, f2)
        if other is None or not _strong(other):
            continue
        tried.append(f"{c2} {f2}")
        if agree(me, other):
            ok.append(f"{c2} {f2}")
    if not tried:
        return None, "no cognate on the line to compare with"
    if ok:
        return True, "fits the regular correspondences with " + ", ".join(ok)
    return False, "does not fit the regular correspondences with " + ", ".join(tried)
