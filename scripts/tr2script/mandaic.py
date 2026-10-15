"""Mandaic: Macuch/Drower-style transliteration (as quoted in SED) -> Mandaic script.

Wiktionary's Module:Mand-translit reads the script letter by letter (ࡀ a, ࡉ i, ࡅ u, ࡏ ʿ, ࡇ ẖ, ࡘ ʕ, ࡖ ḏ-, ࡗ kḏ, gemination mark U+085B = underdot),
so the vowel letters are part of the transliteration: Mandaic writes its vowels in full, a/i/u being the letters ࡀ ࡉ ࡅ, and the source spells what
the script shows. The converter is therefore one letter to one letter:
  a ā -> ࡀ    i y -> ࡉ    u w -> ࡅ    ˁ ʿ ʕ -> ࡏ    š ṭ ṣ ḳ(q) etc. as in the table
Refused (None): forms that cannot be a unique spelling:
  ḥ ġ ˀ ḏ ʔ      etymological letters the script merges or does not write (ḥ -> ࡄ/ࡇ/ࡏ ..., ˀ -> ࡀ or nothing)
  doubled consonants   (gemination: written with the mark U+085B or not at all)
  bare roots           (no a/i/u at all, 3+ consonants: a root, not a word)
  ',' ' ' '(' '-' and other punctuation: variants and affixes are converted one at a time by the caller
Validated against Wiktionary by tests/test_tr2script.py (the Mandaic entries that exist on Wiktionary)."""
import re, unicodedata as U

MAP = {"a": "ࡀ", "ā": "ࡀ", "b": "ࡁ", "g": "ࡂ", "d": "ࡃ", "h": "ࡄ", "u": "ࡅ", "w": "ࡅ", "z": "ࡆ", "ṭ": "ࡈ", "i": "ࡉ", "y": "ࡉ",
       "k": "ࡊ", "l": "ࡋ", "m": "ࡌ", "n": "ࡍ", "s": "ࡎ", "ˁ": "ࡏ", "ʿ": "ࡏ", "ʕ": "ࡏ", "p": "ࡐ", "ṣ": "ࡑ", "ḳ": "ࡒ", "q": "ࡒ", "r": "ࡓ",
       "š": "ࡔ", "t": "ࡕ"}
VOWELS = "aāiyuw"

def convert(lang, translit):
    if lang != "myz":
        return None
    s = U.normalize("NFC", translit)
    if not s or any(ch not in MAP for ch in s):
        return None
    if re.search(r"([^aāiyuw])\1", s):                                  # doubled consonant
        return None
    if not re.search("[aāiu]", s) and len(s) >= 3:                      # bare root
        return None
    return "".join(MAP[ch] for ch in s)

# Wiktionary's Module:Mand-translit, letters only (snapshot of the table in that module); the page's tr is computed from the script by this
TT = {"ࡁ": "b", "ࡂ": "g", "ࡃ": "d", "ࡄ": "h", "ࡆ": "z", "ࡈ": "ṭ", "ࡊ": "k", "ࡋ": "l", "ࡌ": "m", "ࡍ": "n", "ࡎ": "s", "ࡐ": "p", "ࡑ": "ṣ", "ࡒ": "q",
      "ࡓ": "r", "ࡔ": "š", "ࡕ": "t", "ࡖ": "ḏ-", "ࡗ": "kḏ", "ࡘ": "ʕ", "ࡀ": "a", "ࡅ": "u", "ࡉ": "i", "ࡏ": "ʿ", "ࡇ": "ẖ"}
def translit(script):
    """What Wiktionary's module shows for this Mandaic spelling (no gemination/affrication marks handled: convert() never writes them)."""
    return "".join(TT.get(ch, ch) for ch in script)
