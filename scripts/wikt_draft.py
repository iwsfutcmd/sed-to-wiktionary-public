"""Generate draft Wiktionary Proto-Semitic reconstruction pages from SEDonline (all cited words, not a selection).
usage: wikt_draft.py REC_ID [REC_ID ...]    -> wiktionary_drafts/Proto-Semitic_<title>.wiki (+ prints script/verification notes)

Script forms, in order of trust: (1) curated spellings below, each checked against a live Wiktionary entry (see --verify);
(2) Akkadian cuneiform copied from the {{cunsp}} block of the Wiktionary lemma page (network, cached under build/);
(3) Ethiopic generated from the transliteration (syllabary is regular; flagged); (4) none -> `-` plus tr= ("[script needed]")."""
import csv, json, re, sys, time, urllib.request, urllib.parse, urllib.error, unicodedata as U
from collections import defaultdict
from paths import DATA, BUILD, ROOT
from sedonline_compare import read

UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
CACHE = BUILD / "wikt_pages"
OUT = ROOT / "wiktionary_drafts"

EAST = ("East Semitic",); NW = ("West Semitic", "Central Semitic", "Northwest Semitic")
CAN = NW + ("Canaanite",); CS = ("West Semitic", "Central Semitic"); OSA = CS + ("Old South Arabian",)
ETH = ("West Semitic", "Ethiopian Semitic"); GUR = ETH + ("Gurage",); MSA = ("West Semitic", "Modern South Arabian")
# SEDonline language -> (Wiktionary code, tree path, label before the entry)
LANG = {"Akkadian": ("akk", EAST, ""), "Ebla": ("xeb", EAST, ""), "Arabic": ("ar", CS, ""),
        "Old Aramaic": ("arc", NW, "Old "), "Official Aramaic": ("arc", NW, "Official "), "Biblical Aramaic": ("arc", NW, "Biblical "),
        "Palmyrean": ("arc", NW, "Palmyrene "), "Jewish Palestinian Aramaic": ("jpa", NW, ""), "Jewish Babylonian Aramaic": ("tmr", NW, ""),
        "Samaritan": ("sam", NW, ""), "Syriac": ("syc", NW, ""), "Mandaic": ("myz", NW, ""), "Turoyo": ("tru", NW, ""), "Maalula": ("amw", NW, ""),
        "Hebrew": ("hbo", CAN, ""), "Phoenician": ("phn", CAN, ""), "Ugaritic": ("uga", NW, ""),
        "Sabaic": ("xsa", OSA, ""), "Hadramitic": ("sem-srb", OSA, "Hadramitic "), "Geez": ("gez", ETH, ""), "Tigre": ("tig", ETH, ""),
        "Tigrinya": ("ti", ETH, ""), "Amharic": ("am", ETH, ""), "Argobba": ("agj", ETH, ""), "Harari": ("har", ETH, ""), "Gafat": ("gft", ETH, ""),
        "Selti": ("stv", GUR, ""), "Wolane": ("wle", GUR, ""), "Zway": ("zwa", GUR, ""), "Soddo": ("gru", GUR, ""), "Gogot": ("gru", GUR, ""),
        "Chaha": ("sgw", GUR, ""), "Ezha": ("sgw", GUR, ""), "Endegen": ("sgw", GUR, ""), "Ennemor": ("sgw", GUR, ""), "Gyeto": ("sgw", GUR, ""),
        "Muher": ("sgw", GUR, ""), "Masqan": ("mvz", GUR, ""), "Mehri": ("gdq", MSA, ""), "Jibbali": ("shv", MSA, ""), "Harsusi": ("hss", MSA, ""),
        "Soqotri": ("sqt", MSA, ""), "Bathari": ("bhm", MSA, "")}
ORDER = list(LANG)                      # output order within a node
ETHIOPIC = {"am", "ti", "agj", "har", "gft", "stv", "wle", "zwa", "gru", "sgw", "mvz"}   # not tig/gez: their sources' a/ä do not follow the regular convention
LATIN = {"tru", "amw"}                  # written in Latin script on Wiktionary: the form itself is the entry
DIALECT = {"Chaha": "Chaha", "Ezha": "Ezha", "Endegen": "Endegen", "Ennemor": "Ennemor", "Gyeto": "Gyeto", "Muher": "Muher", "Gogot": "Gogot", "Soddo": "Soddo", "Masqan": None}

# (lang code, SEDonline form) -> script. Every one is verified against a live Wiktionary entry by --verify.
CURATED = {
 ("uga", "yrk"): "𐎊𐎗𐎋", ("uga", "ṯ̣by"): "𐎑𐎁𐎊", ("uga", "ˀmr"): "𐎛𐎎𐎗", ("uga", "mrṣ"): "𐎎𐎗𐎕",
 ("hbo", "yārēk"): "יָרֵךְ", ("hbo", "ṣəbī"): "צְבִי", ("hbo", "ˀimmēr"): "אִמֵּר", ("hbo", "mrṣ"): "מרץ",
 ("phn", "ˀmr"): "𐤀𐤌𐤓", ("ar", "warik-"): "وَرِك", ("ar", "ḏ̣aby-"): "ظَبْي", ("ar", "mrḍ"): "مَرِضَ", ("ar", "baqq-"): "بَقّ",
 ("xsa", "wrk"): "𐩥𐩧𐩫", ("xsa", "ṣby"): "𐩮𐩨𐩺", ("xsa", "mrḍ"): "𐩣𐩧𐩳", ("sem-srb", "ṣby"): "𐩮𐩨𐩺",
 ("jpa", "yrk"): "ירך", ("tmr", "yirkā"): "ירכא", ("arc", "ṣby"): "צבי", ("arc", "ṭby"): "טבי", ("jpa", "ṭby"): "טבי", ("tmr", "ṭabyā"): "טביא",
 ("arc", "ˀmr"): "אמר", ("jpa", "ˀymrh"): "אימרה", ("tmr", "ˀimmrā"): "אימרא", ("arc", "mrḳ"): "מרק", ("arc", "mrˁ"): "מרע", ("jpa", "mrˁ"): "מרע",
 ("syc", "ˁrṭ"): "ܥܪܛ", ("ar", "ḍrṭ"): "ضَرَطَ", ("syc", "ṭabyā"): "ܛܒܝܐ", ("syc", "ˀemmrā"): "ܐܡܪܐ", ("syc", "mǝraˁ"): "ܡܪܥ", ("syc", "bāḳā"): "ܒܩܐ",
}
ETH_BASE = {"h": 0x1200, "l": 0x1208, "ḥ": 0x1210, "m": 0x1218, "ś": 0x1220, "r": 0x1228, "s": 0x1230, "š": 0x1238, "q": 0x1240, "ḳ": 0x1240,
            "b": 0x1260, "t": 0x1270, "č": 0x1278, "n": 0x1290, "ñ": 0x1298, "ʔ": 0x12A0, "ˀ": 0x12A0, "k": 0x12A8, "w": 0x12C8, "ʕ": 0x12D0, "ˁ": 0x12D0,
            "z": 0x12D8, "ž": 0x12E0, "y": 0x12E8, "d": 0x12F0, "ǧ": 0x1300, "g": 0x1308, "ṭ": 0x1320, "č̣": 0x1328, "ṗ": 0x1330, "ṣ": 0x1338,
            "ṣ̂": 0x1340, "f": 0x1348, "p": 0x1350}
ORD = {"ä": 0, "u": 1, "i": 2, "a": 3, "e": 4, "ə": 5, "o": 6}
def ethiopic(tr):
    """Regular syllabary: consonant + vowel (ä u i a e ə o, no vowel = ə). Returns None if anything is not covered
    (labialised, ejective variants, tone, unknown letters), so that nothing is guessed."""
    s = U.normalize("NFC", tr)
    if re.search(r"[\s,;/()ʷ˜̃-]", U.normalize("NFD", s)):
        return None
    out, i = [], 0
    toks = sorted(ETH_BASE, key=len, reverse=True)
    while i < len(s):
        for t in toks:
            if s.startswith(t, i):
                i += len(t)
                v = 5
                if i < len(s) and s[i] in ORD:
                    v = ORD[s[i]]; i += 1
                    if i < len(s) and s[i] == "ː":
                        i += 1
                out.append(chr(ETH_BASE[t] + v)); break
        else:
            return None
    return "".join(out)

def api(**q):
    data = urllib.parse.urlencode(dict(format="json", formatversion=2, **q)).encode()
    for i in range(7):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=90))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(float(e.headers.get("Retry-After") or 0) or 2 ** (i + 2))
def page(title):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (urllib.parse.quote(title, safe="") + ".txt")
    if f.exists(): return f.read_text(encoding="utf-8") or None
    r = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles=title)["query"]["pages"][0]
    c = r["revisions"][0]["slots"]["main"]["content"] if "revisions" in r else ""
    f.write_text(c, encoding="utf-8"); return c or None
AKK_LEMMA = {"warkatu": "warkatum", "warki": "warki", "marāṣu": "marāṣum", "immeru": "immerum", "ṣabītu": "ṣabītum", "baqqu": "baqqum", "baḳḳu": "baqqum", "ṣarātu": "ṣarātum"}
def akkadian(form):
    """-> (lemma, phonetic cuneiform spelling from the page's {{cunsp}}, or None)"""
    lemma = AKK_LEMMA.get(form, form)
    c = page(lemma)
    sec = c[c.find("==Akkadian=="):] if c and "==Akkadian==" in c else ""
    m = re.search(r"\|phon=([^<\n|]+)", sec)
    return lemma, (m.group(1) if m else None)

def tr_of(f):
    return U.normalize("NFC", f).replace("ˀ", "ʔ").replace("ˁ", "ʕ")
TRANSLATE = {"the sacrup or rump of a butchered animal": "the sacrum or rump of a butchered animal", "Hüfte": "hip", "Wanzen (bugs)": "bugs", "Mücke (mosquito)": "mosquito", "guérir": "to heal"}
def one(code, form, notes, first, gloss, lang):
    """One {{desc}} (first variant) or {{l}} (further variants) with the best script available."""
    head = "desc" if first else "l"
    t = f"|t={gloss}" if (gloss and first) else ""
    if code == "akk":
        lemma, cun = akkadian(form)
        if not cun: notes.append(f"Akkadian {lemma}: no cuneiform (no Wiktionary lemma page)")
        return f"{{{{{head}|akk|{lemma}" + (f"|alt={cun}" if cun else "") + f"|tr={lemma}{t}}}}}"
    sc = CURATED.get((code, form))
    if sc is None and code in ETHIOPIC:
        sc = ethiopic(form)
        if sc: notes.append(f"{lang} {form}: Ethiopic {sc} GENERATED from the transliteration")
    if code in LATIN:
        return f"{{{{{head}|{code}|{tr_of(form)}{t}}}}}"
    if sc is None:
        return f"{{{{{head}|{code}|-|tr={tr_of(form)}{t}}}}}"
    return f"{{{{{head}|{code}|{sc}|tr={tr_of(form)}{t}}}}}"
def entry(code, form, gloss, lang, notes):
    gloss = TRANSLATE.get(gloss, gloss)
    if gloss.startswith("="):                               # a note about a spelling, not a meaning
        gloss = ""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)$", form)           # 'yarḵāṯēh (suff.)' -> form + note
    if m and re.search(r"suff|det|pl|fem|masc", m.group(2)):
        form = m.group(1); gloss = (gloss + f" ({m.group(2)})").strip()
    if "/" in form:                                         # slash alternations: keep the printed string, no guessing
        return f"{{{{desc|{code}|-|tr={tr_of(form)}" + (f"|t={gloss}" if gloss else "") + "}}}}"
    variants = [v.strip() for v in form.split(",") if v.strip()]
    if code == "xeb":                                       # Eblaite variants are alternative spellings of one word
        variants = variants[:1]
    return ", ".join(one(code, v, notes, i == 0, gloss, lang) for i, v in enumerate(variants))

PAGES = {   # title -> SEDonline reconstruction id and page content
 "warik-": dict(rec="758", vol="I", entry="*warik(-at)-", pos="{{sem-noun|m|g2=f}}", infl=True,
                defs=["[[hip]], [[hipbone]]", "[[haunch]], upper [[thigh]]"], cat="{{C|sem-pro|Anatomy}}",
                etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' with an optional feminine suffix {{m|sem-pro|*-at-}}: {{m|sem-pro|*warik(-at)-}}."),
 "ṯ̣aby-": dict(rec="624", vol="II", entry="*ṯ̣aby(-at)-", pos="{{sem-noun|m|g2=f}}", infl=True, defs=["[[gazelle]]"], cat="{{C|sem-pro|Mammals}}",
               etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' with an optional feminine suffix {{m|sem-pro|*-at-}}: {{m|sem-pro|*ṯ̣aby(-at)-}}."),
 "mrṣ́": dict(rec="894", vol="I", entry="*mrṣ̂", pos="{{head|sem-pro|verb}}", infl=False, defs=["to be [[sick]], [[ill]]"], cat="", etym=""),
 "ṣ́rṭ": dict(rec="1023", vol="I", entry="*ṣ̂rṭ", pos="{{head|sem-pro|verb}}", infl=False, defs=["to [[fart]], to break [[wind]] audibly"], cat="", etym=""),
 "baqq-": dict(rec="667", vol="II", entry="*baḳḳ-", pos="{{sem-noun|m}}", infl=True, defs=["[[gnat]]"], cat="{{C|sem-pro|Insects}}", etym=""),
}
def tree_lines(words, notes):
    lines, shown = [], set()
    for w in sorted(words, key=lambda w: ORDER.index(w["lang"])):
        code, path, label = LANG[w["lang"]]
        g = re.sub(r"\s+", " ", w["gloss"]).strip().replace("|", "/")
        e = entry(code, w["form"], g, w["lang"], notes)
        if DIALECT.get(w["lang"]):
            e = re.sub(r"\}\}", "|q=" + DIALECT[w["lang"]] + "}}", e, count=1)
        for d in range(len(path)):
            if path[:d + 1] not in shown:
                shown.add(path[:d + 1]); lines.append("*" * (d + 1) + " " + path[d] + ":")
        lines.append("*" * (len(path) + 1) + " " + label + e)
    return lines
def build(title, cfg):
    words = [w for w in read(DATA / "sedonline" / "sedonline_words.tsv") if w["rec_id"] == cfg["rec"]]
    miss = sorted({w["lang"] for w in words} - set(LANG))
    if miss: raise SystemExit(f"{title}: unmapped languages {miss}")
    notes = []
    d = ["{{reconstructed}}", "==Proto-Semitic==", ""]
    if cfg["etym"]: d += ["===Etymology===", cfg["etym"], ""]
    d += ["===" + ("Verb" if "verb" in cfg["pos"] else "Noun") + "===", cfg["pos"], ""] + ["# " + x for x in cfg["defs"]] + [""]
    if cfg["infl"]: d += ["====Inflection====", "{{sem-decl-noun}}", ""]
    d += ["====Descendants===="] + tree_lines(words, notes) + ["",
          "===References===", "* {{R:sem-pro:SED|volume=%s|id=%s|entry=%s}}" % (cfg["vol"], cfg["rec"], cfg["entry"])]
    if cfg["cat"]: d += ["", cfg["cat"]]
    OUT.mkdir(exist_ok=True)
    (OUT / f"Proto-Semitic_{title}.wiki").write_text("\n".join(d) + "\n", encoding="utf-8")
    print(f"{title}: {len(words)} words; notes:", *notes, sep="\n   ")

UGA = ["𐎀ʔ", "𐎁b", "𐎂g", "𐎃ḫ", "𐎄d", "𐎅h", "𐎆w", "𐎇z", "𐎈ḥ", "𐎉ṭ", "𐎊y", "𐎋k", "𐎌š", "𐎍l", "𐎎m", "𐎏ḏ", "𐎐n", "𐎑ẓ", "𐎒s",
       "𐎓ʕ", "𐎔p", "𐎕ṣ", "𐎖q", "𐎗r", "𐎘ṯ", "𐎙ġ", "𐎚t", "𐎛ʔ", "𐎜ʔ", "𐎝ś"]
OSA_L = ["𐩠h", "𐩡l", "𐩢ḥ", "𐩣m", "𐩤q", "𐩥w", "𐩦š", "𐩧r", "𐩨b", "𐩩t", "𐩪s", "𐩫k", "𐩬n", "𐩭ḫ", "𐩮ṣ", "𐩯ś", "𐩰f", "𐩱ʔ", "𐩲ʕ", "𐩳ḍ",
         "𐩴g", "𐩵d", "𐩶ġ", "𐩷ṭ", "𐩸z", "𐩹ḏ", "𐩺y", "𐩻ṯ", "𐩼ẓ"]
LETTERS = {  # script letter -> consonant it writes (matres lectionis ʔ h w y are ignored by the check)
 **dict(zip("אבגדהוזחטיכךלמםנןסעפףצץקרשת", ["ʔ", "b", "g", "d", "h", "w", "z", "ḥ", "ṭ", "y", "k", "k", "l", "m", "m", "n", "n", "s", "ʕ", "p", "p", "ṣ", "ṣ", "q", "r", "š", "t"])),
 **dict(zip("ܐܒܓܕܗܘܙܚܛܝܟܠܡܢܣܥܦܨܩܪܫܬ", ["ʔ", "b", "g", "d", "h", "w", "z", "ḥ", "ṭ", "y", "k", "l", "m", "n", "s", "ʕ", "p", "ṣ", "q", "r", "š", "t"])),
 **{x[0]: x[1:] for x in UGA}, **{x[0]: x[1:] for x in OSA_L},
 **dict(zip("𐤀𐤁𐤂𐤃𐤄𐤅𐤆𐤇𐤈𐤉𐤊𐤋𐤌𐤍𐤎𐤏𐤐𐤑𐤒𐤓𐤔𐤕", ["ʔ", "b", "g", "d", "h", "w", "z", "ḥ", "ṭ", "y", "k", "l", "m", "n", "s", "ʕ", "p", "ṣ", "q", "r", "š", "t"]))}
def _fold(c):
    c = re.sub("[ʔhwy]", "", c)
    return re.sub(r"(.)\1", r"\1", c)               # gemination is not written in these scripts
def consonants_of(tr):
    d = U.normalize("NFC", tr.lower()).replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ḳ", "q").replace("ṯ̣", "ẓ").replace("ḏ̣", "ẓ")
    d = U.normalize("NFC", re.sub("[aeiouāēīōūəǝ\u0304\u0306\u0302\u0301ʷ-]", "", U.normalize("NFD", d)))
    return _fold(d)
def consistent(code, form, sc):
    if code == "ar":
        return None
    got = _fold("".join(LETTERS.get(c, "?") for c in U.normalize("NFC", sc) if not (0x591 <= ord(c) <= 0x5C7 or 0x730 <= ord(c) <= 0x74A)))
    want = consonants_of(form)
    return got == want, got, want

def verify():
    """Every curated spelling must be an existing Wiktionary entry in the right language (title = spelling without vowel marks)."""
    sect = {"uga": "Ugaritic", "hbo": "Hebrew", "phn": "Phoenician", "ar": "Arabic", "xsa": "Sabaean", "sem-srb": "Old South Arabian", "jpa": "Jewish Palestinian Aramaic",
            "tmr": "Jewish Babylonian Aramaic", "arc": "Aramaic", "syc": "Classical Syriac"}
    strip = lambda t: "".join(c for c in U.normalize("NFC", t) if not (0x591 <= ord(c) <= 0x5C7 or 0x64B <= ord(c) <= 0x652 or ord(c) in (0x670, 0x651) or 0x730 <= ord(c) <= 0x74A))
    bad = 0
    for (code, form), sc in sorted(CURATED.items()):
        t = strip(sc); c = page(t)
        s = sect[code]; ok = bool(c) and (f"=={s}==" in c or (code == "hbo" and "==Biblical Hebrew==" in c) or (code == "arc" and "==Aramaic==" in c))
        # Wiktionary has no entries for some pure transliteration-derived forms: report, do not hide
        cs = consistent(code, form, sc)
        print(("ok     " if ok else "NO PAGE"), code, form, sc, "->", t, "" if cs is None else ("| consonants match" if cs[0] else f"| CONSONANT MISMATCH {cs[1]} vs {cs[2]}"))
        bad += not ok
    print(bad, "of", len(CURATED), "curated spellings have no matching Wiktionary entry")

if __name__ == "__main__":
    if "--verify" in sys.argv: verify()
    else:
        for t, cfg in PAGES.items():
            if len(sys.argv) == 1 or t in sys.argv[1:]: build(t, cfg)
