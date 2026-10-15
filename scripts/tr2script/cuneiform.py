"""Akkadian (and other cuneiform) syllabic transliteration -> Unicode cuneiform, via the eBL sign list.

  convert("wa-ar-ka-tum") -> "𒉿𒅈𒅗𒌈"

A spelling is a hyphen-separated sequence of syllabic readings, each looked up in the Electronic Babylonian Library sign list
(https://www.ebl.lmu.de/api/signs?value=VALUE&subIndex=N). Only readings with NO index are converted: sign lists number homophones
differently, so (reading, index) is not a safe key across sources. Wiktionary spells ar₂ as 𒄱 (HI×DIŠ), eBL says ar₂ is 𒌒 (UB);
tests/test_cuneiform.py records this; DISPUTED lists unindexed readings that differ. Everything else gives None, never a guess: subscripted or accented readings (ku₁₇, rí, á),
logograms (capitals), determinatives, damaged signs, numbers. `convert(..., indexed=True)` lifts the index restriction.

Lookups are cached in data/scripts/ebl_signs.json so conversion and the tests need no network; `fill([...])` fetches missing readings.
The sign list is eBL's (https://www.ebl.lmu.de/, Electronic Babylonian Library project): check its licence before redistributing more than
the small cache kept here."""
import json, re, time, unicodedata as U, urllib.error, urllib.parse, urllib.request
from paths import DATA

CACHE = DATA / "scripts" / "ebl_signs.json"
API = "https://www.ebl.lmu.de/api/signs"
UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
ACCENT = {"́": 2, "̀": 3}             # acute, grave

# Readings where Wiktionary and eBL disagree on the sign (found by tests/test_cuneiform.py against Wiktionary's own cunsp spellings);
# the converter refuses them. reading -> what differs.
DISPUTED = {("šum", 1): "Wiktionary 𒋗 (SHU), eBL 𒋳 (TAG): period-dependent sign forms?",
            ("iš", 1): "Wiktionary 𒄑 (GIŠ), eBL 𒅖 (IŠ)",
            ("qa", 1): "Wiktionary 𒂵 (GA), eBL 𒋡 (SILA₃)"}

_cache = None
def _load():
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    return _cache

def reading(syl):
    """'ku₁₇' -> ('ku', 17); 'rí' -> ('ri', 2); 'ka' -> ('ka', 1); None for anything that is not a plain syllabic reading."""
    s = U.normalize("NFD", syl.strip())
    idx = 1
    for mark, n in ACCENT.items():
        if mark in s:
            s = s.replace(mark, ""); idx = n
    s = U.normalize("NFC", s).translate(SUB)
    m = re.fullmatch(r"([a-wyzšṣṭḫʾ]+?)(\d+)?", s)      # lower case only (capitals are logograms or determinatives); no x (damaged sign)
    if not m or not m.group(1):
        return None
    if m.group(2):
        idx = int(m.group(2))
    return m.group(1), idx

def lookup(value, idx, online=False):
    """-> the cuneiform sign, or None. Uses the cache; fetches only when online=True."""
    key = f"{value}|{idx}"
    c = _load()
    if key in c:
        return c[key]
    if not online:
        return None
    try:
        q = urllib.parse.urlencode({"value": value, "subIndex": idx})
        r = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=UA), timeout=30))
    except (urllib.error.URLError, TimeoutError):
        return None                                      # not cached: an unreachable server is not evidence of "no such sign"
    signs = [s for s in r if s.get("unicode")]
    c[key] = "".join(chr(u) for u in signs[0]["unicode"]) if len(signs) == 1 else None
    return c[key]

def convert(spelling, online=False, indexed=False):
    out = []
    for syl in spelling.split("-"):
        rd = reading(syl)
        sign = lookup(*rd, online=online) if rd and (indexed or rd[1] == 1) and rd not in DISPUTED else None
        if sign is None:
            return None
        out.append(sign)
    return "".join(out)

def fill(spellings, delay=0.15):
    """Fetch every reading used in `spellings` that is not cached yet, then save the cache. Returns the number fetched."""
    todo = sorted({reading(s) for sp in spellings for s in sp.split("-") if reading(s)} - {tuple(k.split("|")[:1]) + (int(k.split("|")[1]),) for k in _load()})
    n = 0
    for value, idx in todo:
        lookup(value, idx, online=True); n += 1; time.sleep(delay)
    save()
    return n

def save():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(_load(), ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
