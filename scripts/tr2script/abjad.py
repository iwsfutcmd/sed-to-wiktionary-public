"""Consonantal Latin transliteration -> script, for the abjads and alphabets the SED words are cited in.

  sam   Samaritan script (Samaritan Aramaic and Hebrew)
  he    Hebrew / Aramaic square script (also Biblical Aramaic, Jewish Aramaic): unpointed; final forms ך ם ן ף ץ
  syc   Syriac (Estrangela letters, unpointed)
  uga   Ugaritic cuneiform alphabet          phn   Phoenician          osa   Old South Arabian (Sabaic, Minaic, Qatabanic, Hadramitic)

Only the consonant skeleton is written: vowels are dropped, doubled consonants are written once (no script here marks gemination),
and a final ā is written as a mater lectionis (alef) in he, sam and syc.
When the form has vowels that these orthographies often write with a letter (ī ū ō, short u o, or a final ē) the skeleton may be
incomplete, so the result is None: better "script needed" than a wrong spelling, as Aramaic orthography does. Anything outside the scheme
(unknown letter, space, digits) gives None. Two things cannot be recovered from the consonants and are NOT attempted:
Ugaritic ʾ with its own vowel (𐎀 𐎛 𐎜) is always 𐎀, and Hebrew sin/shin dots, dagesh and vowel points are never written.

usage: abjad.convert("syc", "ṭabyā") -> "ܛܒܝܐ" """
import re, unicodedata as U

PAIRS = {
 "he":  [("ʾ", "א"), ("b", "ב"), ("g", "ג"), ("d", "ד"), ("h", "ה"), ("w", "ו"), ("z", "ז"), ("ḥ", "ח"), ("ṭ", "ט"), ("y", "י"), ("k", "כ"),
         ("l", "ל"), ("m", "מ"), ("n", "נ"), ("s", "ס"), ("ʿ", "ע"), ("p", "פ"), ("ṣ", "צ"), ("q", "ק"), ("r", "ר"), ("š", "ש"), ("ś", "ש"), ("t", "ת")],
 "syc": [("ʾ", "ܐ"), ("b", "ܒ"), ("g", "ܓ"), ("d", "ܕ"), ("h", "ܗ"), ("w", "ܘ"), ("z", "ܙ"), ("ḥ", "ܚ"), ("ṭ", "ܛ"), ("y", "ܝ"), ("k", "ܟ"),
         ("l", "ܠ"), ("m", "ܡ"), ("n", "ܢ"), ("s", "ܣ"), ("ʿ", "ܥ"), ("p", "ܦ"), ("ṣ", "ܨ"), ("q", "ܩ"), ("r", "ܪ"), ("š", "ܫ"), ("t", "ܬ")],
 "uga": [("ʾ", "𐎀"), ("b", "𐎁"), ("g", "𐎂"), ("ḫ", "𐎃"), ("d", "𐎄"), ("h", "𐎅"), ("w", "𐎆"), ("z", "𐎇"), ("ḥ", "𐎈"), ("ṭ", "𐎉"), ("y", "𐎊"),
         ("k", "𐎋"), ("š", "𐎌"), ("l", "𐎍"), ("m", "𐎎"), ("ḏ", "𐎏"), ("n", "𐎐"), ("ẓ", "𐎑"), ("s", "𐎒"), ("ʿ", "𐎓"), ("p", "𐎔"), ("ṣ", "𐎕"),
         ("q", "𐎖"), ("r", "𐎗"), ("ṯ", "𐎘"), ("ġ", "𐎙"), ("t", "𐎚"), ("ś", "𐎝")],
 "phn": [("ʾ", "𐤀"), ("b", "𐤁"), ("g", "𐤂"), ("d", "𐤃"), ("h", "𐤄"), ("w", "𐤅"), ("z", "𐤆"), ("ḥ", "𐤇"), ("ṭ", "𐤈"), ("y", "𐤉"), ("k", "𐤊"),
         ("l", "𐤋"), ("m", "𐤌"), ("n", "𐤍"), ("s", "𐤎"), ("ʿ", "𐤏"), ("p", "𐤐"), ("ṣ", "𐤑"), ("q", "𐤒"), ("r", "𐤓"), ("š", "𐤔"), ("t", "𐤕")],
 "osa": [("h", "𐩠"), ("l", "𐩡"), ("ḥ", "𐩢"), ("m", "𐩣"), ("q", "𐩤"), ("w", "𐩥"), ("š", "𐩦"), ("r", "𐩧"), ("b", "𐩨"), ("t", "𐩩"), ("s", "𐩪"),
         ("k", "𐩫"), ("n", "𐩬"), ("ḫ", "𐩭"), ("ṣ", "𐩮"), ("ś", "𐩯"), ("f", "𐩰"), ("ʾ", "𐩱"), ("ʿ", "𐩲"), ("ḍ", "𐩳"), ("g", "𐩴"), ("d", "𐩵"),
         ("ġ", "𐩶"), ("ṭ", "𐩷"), ("z", "𐩸"), ("ḏ", "𐩹"), ("y", "𐩺"), ("ṯ", "𐩻"), ("ẓ", "𐩼")]}
# Samaritan: the 22 letters in the same order as the Hebrew alphabet, U+0800 .. U+0815
PAIRS["sam"] = [(lat, chr(0x800 + i)) for i, (lat, _) in enumerate(l for l in PAIRS["he"] if l[0] != "ś")]
TABLES = {k: dict(v) for k, v in PAIRS.items()}
FINAL = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}
# Wiktionary language code -> table
CODES = {"he": "he", "sam": "sam", "hbo": "he", "arc": "he", "jpa": "he", "tmr": "he", "syc": "syc", "uga": "uga", "phn": "phn", "xsa": "osa", "sem-srb": "osa",
         "inm": "osa", "xqt": "osa", "sem-amm": "phn"}
SRC = {"ˀ": "ʾ", "ʔ": "ʾ", "ʼ": "ʾ", "ˁ": "ʿ", "ʕ": "ʿ", "ʻ": "ʿ", "ḳ": "q", "ṯ̣": "ẓ", "ḏ̣": "ẓ", "ŝ": "ś"}
VOWEL = "aeiouāēīōūəǝ"
MATRES_RISK = re.compile("[īūōuo]")      # vowels these orthographies often write with y/w: the bare skeleton may be wrong

SPIRANT = {"ḇ": "b", "ḡ": "g", "ḏ": "d", "ḵ": "k", "ṯ": "t"}

def convert(code, translit):
    t = CODES.get(code)
    if t is None:
        return None
    s = U.normalize("NFC", translit.strip().lower())
    for a, b in SRC.items():
        s = s.replace(a, b)
    if t in ("he", "sam", "syc") and (MATRES_RISK.search(s) or s.endswith("ē")):
        return None
    final_a = t in ("he", "sam", "syc") and s.endswith("ā")                                            # before marks and vowels go
    if t in ("he", "sam", "syc"):                                                                # spirantised begadkefat: same letters
        for a, b in SPIRANT.items():
            s = s.replace(a, b)
    s = U.normalize("NFC", re.sub("[\u0304\u0306\u0302\u0301]", "", U.normalize("NFD", s)))  # length / stress marks
    s = re.sub("[" + VOWEL + "]", "", s)
    s = re.sub(r"(.)\1", r"\1", s)                                                              # gemination is not written
    tab, out = TABLES[t], []
    for ch in s:
        if ch not in tab:
            return None
        out.append(tab[ch])
    if final_a:
        out.append(tab["ʾ"])
    r = "".join(out)
    if t == "he" and r and r[-1] in FINAL:
        r = r[:-1] + FINAL[r[-1]]
    return r
