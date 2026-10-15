"""Vocalised Latin transliteration -> Arabic script.   convert("warik-") -> "وَرِك"   convert("baqq-") -> "بَقّ"

Input is a fully vocalised stem in the transliteration the SED and Wiktionary share: consonants š ṯ ḏ ḥ ḫ ṣ ḍ ṭ ẓ (or ḏ̣) ʕ ġ ǧ q ..., short
vowels a i u, long ā ī ū, doubled letters for shadda, an optional trailing hyphen (stem marker). Written as Wiktionary writes
vocalised Arabic: fatḥa/kasra/ḍamma, sukun on a consonant that closes a syllable (but not on the last letter), shadda for a double
consonant, long vowels as alif / yāʾ / wāw after the short vowel sign.

None (never a guess) when the spelling is not determined by the transliteration:
  - a bare root (nyk, ḍrṭ) or any form that does not start consonant + vowel: nothing to write the vowels from;
  - any ʔ (hamza has seat rules), a word starting with a vowel, or ending in ā / ī (alif maqṣūra, tāʾ marbūṭa, ... cannot be told apart);
  - anything with brackets, slashes, commas or letters outside the table.
Checked by tests/test_tr2script.py against spellings Wiktionary has, and (ONLINE=1) by round trip through Wiktionary's own Arabic
transliteration, as shown next to {{desc|ar|…}}."""
import re, unicodedata as U

C = {"b": "ب", "t": "ت", "ṯ": "ث", "ǧ": "ج", "ḥ": "ح", "ḫ": "خ", "d": "د", "ḏ": "ذ", "r": "ر", "z": "ز", "s": "س", "š": "ش", "ṣ": "ص", "ḍ": "ض",
     "ṭ": "ط", "ẓ": "ظ", "ʕ": "ع", "ġ": "غ", "f": "ف", "q": "ق", "k": "ك", "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "y": "ي"}
V = {"a": "َ", "i": "ِ", "u": "ُ"}                      # fatḥa, kasra, ḍamma
LONG = {"ā": ("َ", "ا"), "ī": ("ِ", "ي"), "ū": ("ُ", "و")}
SUKUN, SHADDA = "ْ", "ّ"
SRC = {"ˁ": "ʕ", "ʿ": "ʕ", "ʻ": "ʕ", "ḳ": "q", "ḏ̣": "ẓ", "ṯ̣": "ẓ", "θ": "ṯ", "δ": "ḏ", "γ": "ġ", "ğ": "ǧ", "j": "ǧ", "x": "ḫ", "ḵ": "ḫ"}

def convert(translit):
    s = U.normalize("NFC", translit.strip().lower())
    for a, b in SRC.items():
        s = s.replace(U.normalize("NFC", a), b)
    s = U.normalize("NFC", s.rstrip("-"))
    if not s or s[0] in "aiuāīū" or s[-1] in "āī" or "ʔ" in s or re.search(r"[^a-zšṯḏḥḫṣḍṭẓʕġǧāīū]", s):
        return None
    if not re.match(r"[^aiuāīū][aiuāīū]", s):                  # Arabic words do not start with a sukun: a bare root (nyk) has no spelling
        return None
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c not in C:
            return None
        i += 1
        mark = ""
        if i < n and s[i] == c:                           # doubled consonant: shadda
            mark = SHADDA; i += 1
        letter = C[c]
        if i < n and s[i] in V:
            out.append(letter + mark + V[s[i]]); i += 1
        elif i < n and s[i] in LONG:
            short, mater = LONG[s[i]]
            if c in "wy" and mater == C[c]:               # wū / yī: the consonant and the mater would merge
                return None
            out.append(letter + mark + short + mater); i += 1
        elif i == n:                                      # last letter: no sukun
            out.append(letter + mark)
        else:                                             # closes a syllable
            out.append(letter + (mark or SUKUN))
    return "".join(out)
