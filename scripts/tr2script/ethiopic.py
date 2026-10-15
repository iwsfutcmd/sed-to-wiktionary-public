"""Latin transliteration -> Ethiopic script, as the exact inverse of Wiktionary's Module:Ethi-translit.

Scheme (Wiktionary's): seven orders  ä u i a e ə o ; a consonant with no vowel written is the sixth order (ə);
ʾ ʿ for ʔ ʕ; ṣ́ for ፀ, ṣ for ጸ, ḳ ፣ x̣ ቐ, ḫ ኀ, ǧ ጀ, č̣ ጨ, p̣ ጰ, ŋ ጘ; labialised consonants as C+ʷ+a.
Gemination is not written (Amharic, Tigrinya and Gurage orthography do not mark it), so a doubled letter is written once.
A word-initial vowel is an unwritten ʾ in the sources: for the Amharic-type profiles (INITIAL_A) it is read as ʾ+vowel with a = ʾä
(Amharic አጥንት = SED aṭənt); for Tigrinya and Tigre, which write ʾä and ʾa differently, it is not converted.

Language profiles say how a source's transliteration maps onto that scheme:
  am, ti, tig, agj, har, gft, stv, wle, zwa, gru, sgw, mvz   the source writes ä for the first order and a for the fourth
                                                           (as SEDonline does for Amharic, Tigrinya, Tigre and the Gurage group)
  ti additionally takes ḵ (Kane's transcription of ኸ) as x.
Not provided: Ge'ez. Its source (Leslau's CDG, as quoted in SED) writes a for the first order, so the conversion depends on the
word and cannot be done from the transliteration alone.

usage: ethiopic.convert("am", "wärč") -> "ወርች";  ethiopic.refresh() re-fetches Wiktionary's table."""
import json, re, unicodedata as U
from functools import lru_cache
from paths import DATA

TABLE = DATA / "scripts" / "ethi_translit.json"
VOWELS = "äuiaeəo"
PROFILES = {c: {} for c in "am tig agj har gft stv wle zwa gru sgw mvz".split()}
PROFILES["ti"] = {"ḵ": "x"}
# profiles whose source writes a word-initial vowel for an unwritten ʾ, with a standing for ʾä (cf. Wiktionary's Amharic አጥንት = SED aṭənt)
LONG_A = {"am", "agj", "gft", "stv", "wle", "zwa", "gru", "sgw", "mvz", "har"}
INITIAL_A = {"am", "agj", "gft", "stv", "wle", "zwa", "gru", "sgw", "mvz"}
# source spellings -> Wiktionary's symbols
COMMON = {"ˀ": "ʾ", "ʔ": "ʾ", "ʼ": "ʾ", "ˁ": "ʿ", "ʕ": "ʿ", "ʻ": "ʿ", "ṣ̂": "ṣ́", "ɨ": "ə", "ǝ": "ə"}

@lru_cache(None)
def _inverse():
    syll = json.loads(TABLE.read_text(encoding="utf-8"))["table"]
    inv = {}
    for ch, lat in syll.items():
        inv[U.normalize("NFC", lat)] = ch
    # consonant (with any labialisation) -> its Latin base letters, for tokenising
    cons = sorted({re.sub("[" + VOWELS + "]$", "", k) for k in inv}, key=len, reverse=True)
    return inv, cons

def convert(lang, translit):
    if lang not in PROFILES:
        return None
    inv, cons = _inverse()
    s = U.normalize("NFC", translit)
    for a, b in {**COMMON, **PROFILES[lang]}.items():
        s = s.replace(a, b)
    s = U.normalize("NFC", s)
    if lang in LONG_A:                                              # a long ā in these sources is the fourth order, as a is
        s = s.replace("ā", "a")
    if s and s[0] in VOWELS and lang in INITIAL_A:                   # initial vowel = ʾ + vowel; a stands for ä
        s = "ʾ" + ("ä" if s[0] == "a" else s[0]) + s[1:]
    out, i = [], 0
    while i < len(s):
        for c in cons:
            if s.startswith(c, i):
                j = i + len(c)
                while s.startswith(c, j):             # doubled consonant = gemination, which the orthography does not write
                    j += len(c)
                if j < len(s) and s[j] in VOWELS:
                    v, j = s[j], j + 1
                else:
                    v = "ə"
                glyph = inv.get(c + v)
                if glyph is None:
                    return None
                out.append(glyph); i = j
                break
        else:
            return None                               # unknown letter, initial vowel (an unwritten ʾ), length marks, spaces ...
    return "".join(out)

def refresh():
    """Re-fetch Module:Ethi-translit from en.wiktionary.org and rewrite the snapshot."""
    import datetime, urllib.request, urllib.parse
    q = urllib.parse.urlencode(dict(action="query", prop="revisions", rvprop="content", rvslots="main", titles="Module:Ethi-translit",
                                    format="json", formatversion=2))
    req = urllib.request.Request("https://en.wiktionary.org/w/api.php?" + q, headers={"User-Agent": "sed-to-wiktionary/1.0 (research)"})
    lua = json.load(urllib.request.urlopen(req, timeout=60))["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
    tt = dict(re.findall(r'\["(.)"\]\s*=\s*"([^"]+)"', lua[lua.index("local tt = {"):lua.index("local number")]))
    syll = {k: v for k, v in tt.items() if 0x1200 <= ord(k) <= 0x139F and not 0x1360 <= ord(k) <= 0x137C}
    TABLE.write_text(json.dumps(dict(source="https://en.wiktionary.org/wiki/Module:Ethi-translit", retrieved=str(datetime.date.today()),
                                     note="char -> Latin as produced by Wiktionary's Module:Ethi-translit (syllables only)", table=syll),
                                ensure_ascii=False, indent=0), encoding="utf-8")
    _inverse.cache_clear()
    return len(syll)
