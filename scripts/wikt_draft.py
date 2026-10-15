"""Generate draft Wiktionary Proto-Semitic reconstruction pages from SEDonline (all cited words, not a selection).
usage: wikt_draft.py REC_ID [REC_ID ...]    -> wiktionary_drafts/Proto-Semitic_<title>.wiki (+ prints script/verification notes)

Script forms, in order: (1) Akkadian cuneiform copied from the {{cunsp}} block of the Wiktionary lemma page (network, cached under
build/); (2) CURATED vocalised spellings (Arabic, pointed Hebrew, Ugaritic ʾi) that no converter can derive; (3) tr2script.ethiopic and
tr2script.abjad (tests/test_tr2script.py); (4) languages cited in Latin on Wiktionary (Mehri, Jibbali, Harsusi, Bathari, Soqotri,
Eblaite, Western Neo-Aramaic): the source form is the term; (5) otherwise `-` plus tr= ("[script needed]")."""
import csv, json, re, sys, time, urllib.request, urllib.parse, urllib.error, unicodedata as U
from collections import defaultdict
from pathlib import Path
from paths import DATA, BUILD, ROOT
from sedonline_compare import read
from tr2script import abjad, arabic, ethiopic

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
AUTO_TR = {"ar", "uga"}             # Wiktionary transliterates these itself (Module:ar-translit, uga-translit): no tr=
LATIN_TERM = {"amw", "gdq", "shv", "hss", "bhm", "sqt", "xeb"}   # cited in Latin script (the source form is the term)
DIALECT = {"Chaha": "Chaha", "Ezha": "Ezha", "Endegen": "Endegen", "Ennemor": "Ennemor", "Gyeto": "Gyeto", "Muher": "Muher", "Gogot": "Gogot", "Soddo": "Soddo", "Masqan": None}

# (lang code, SEDonline form) -> script, for spellings no converter can derive (vowelled or lexical). --verify checks them on Wiktionary.
CURATED = {
 ("uga", "ˀmr"): "𐎛𐎎𐎗",                    # Wiktionary writes ʾi (𐎛), the consonants alone give 𐎀
 ("hbo", "yārēk"): "יָרֵךְ", ("hbo", "ṣəbī"): "צְבִי", ("hbo", "ˀimmēr"): "אִמֵּר", ("tru", "bōḳo"): "ܒܩܐ",      # Turoyo is written in Syriac script on Wiktionary (entry ܒܩܐ)

 ("ar", "mrḍ"): "مَرِضَ", ("ar", "ḍrṭ"): "ضَرَطَ", ("ar", "nyk"): "نَاكَ", ("ar", "ḫrs"): "خَرَّسَ",    # bare roots: the verb forms are chosen by hand
 ("hbo", "šəˀēr"): "שְׁאֵר", ("uga", "šˀir"): "𐎌𐎛𐎗",          # both as on Wiktionary's Akkadian šīrum page
}
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
AKK_LEMMA = {"warkatu": "warkatum", "warki": "warki", "marāṣu": "marāṣum", "immeru": "immerum", "ṣabītu": "ṣabītum", "baqqu": "baqqum", "baḳḳu": "baqqum", "ṣarātu": "ṣarātum", "nâku": "nâkum", "ḫarāšu": "ḫarāšum", "šīru": "šīrum", "šēmu": "šēmum"}
# no lemma page: (lemma, cuneiform, its transliteration). The cuneiform is as cited on Wiktionary's Arabic بق and Classical Syriac ܒܩܐ;
# tests/test_cuneiform.py checks that the transliteration really gives it (eBL sign list).
AKK_OVERRIDE = {"baḳḳu": ("baqqu", "𒁀𒀝𒄣", "ba-aq-qu")}
def akkadian(form):
    """-> (lemma, phonetic cuneiform spelling from the page's {{cunsp}}, or None)"""
    if form in AKK_OVERRIDE:
        return AKK_OVERRIDE[form][:2]
    lemma = AKK_LEMMA.get(form, form)
    c = page(lemma)
    sec = c[c.find("==Akkadian=="):] if c and "==Akkadian==" in c else ""
    m = re.search(r"\|phon=([^<\n|]+)", sec)
    return lemma, (m.group(1) if m else None)

def tr_of(f):
    return U.normalize("NFC", f).replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ḳ", "q").replace("ǝ", "ə")      # descendants: Wiktionary's tr uses q (PS titles keep ḳ)
TRANSLATE = {"im Kindbett liegen": "to be in childbed", "partorire (to give birth)": "to give birth", "accouché": "woman who has given birth", "the sacrup or rump of a butchered animal": "the sacrum or rump of a butchered animal", "Hüfte": "hip", "Wanzen (bugs)": "bugs", "Mücke (mosquito)": "mosquito", "guérir": "to heal"}
def script_for(code, form):
    """-> (script, how) with how in curated / ethiopic / abjad, or (None, None)."""
    if (code, form) in CURATED:
        return CURATED[(code, form)], "curated"
    sc = ethiopic.convert(code, form) if code in ethiopic.PROFILES else None
    if sc: return sc, "ethiopic"
    sc = arabic.convert(form) if code == "ar" else None
    if sc: return sc, "arabic"
    sc = abjad.convert(code, form)
    return (sc, "abjad") if sc else (None, None)
def one(code, form, notes, first, gloss, lang):
    """One {{desc}} (first variant) or {{l}} (further variants) with the best script available."""
    head = "desc" if first else "l"
    t = f"|t={gloss}" if (gloss and first) else ""
    if code == "akk":
        lemma, cun = akkadian(form)
        if not cun: notes.append(f"Akkadian {lemma}: no cuneiform (no Wiktionary lemma page)")
        return f"{{{{{head}|akk|{lemma}" + (f"|alt={cun}" if cun else "") + f"|tr={lemma}{t}}}}}"
    if code in LATIN_TERM:
        return f"{{{{{head}|{code}|{tr_of(form)}{t}}}}}"
    sc, how = script_for(code, form)
    if sc and how != "curated":
        notes.append(f"{lang} {form}: {sc} ({how})")
    if sc is None:
        return f"{{{{{head}|{code}|-|tr={tr_of(form)}{t}}}}}"
    if code in AUTO_TR:
        return f"{{{{{head}|{code}|{sc}{t}}}}}"
    return f"{{{{{head}|{code}|{sc}|tr={tr_of(form)}{t}}}}}"
def entry(code, form, gloss, lang, notes):
    gloss = TRANSLATE.get(gloss, gloss)
    if len(gloss) > 90 and ";" in gloss:                       # long dictionary quotations: keep the first clause
        gloss = gloss.split(";")[0].strip()
    gloss = re.sub(r"^(I{1,3}|IV|V|VI{1,3}|IX|X)\.\s+", lambda m: f"(form {m.group(1)}) ", gloss)
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
 "θ̣aby-": dict(rec="624", vol="II", entry="*ṯ̣aby(-at)-", pos="{{sem-noun|m|g2=f}}", infl=True, defs=["[[gazelle]]"], cat="{{C|sem-pro|Mammals}}",
               etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' with an optional feminine suffix {{m|sem-pro|*-at-}}: {{m|sem-pro|*θ̣aby(-at)-}}."),
 "maraṣ́-": dict(rec="894", vol="I", entry="*mrṣ̂", pos="{{head|sem-pro|verb}}", infl=False,
                 conj="{{sem-pro-conj/*paʕala-*yipʕal|m|r|ṣ́|vn=marṣ́}}",        # SED: Akkadian marāṣu (a/a)
 defs=["to be [[sick]], [[ill]]"], cat="", etym=""),
 "ṣ́araṭ-": dict(rec="1023", vol="I", entry="*ṣ̂rṭ",
                 # where the printed SED differs from SEDonline the draft follows the print (read at 650 dpi; data/sedonline/form_check.tsv)
                 override={("Harsusi", "ẑərōṭ"): dict(form="ẑerōṭ", reason="print: ẑerōṭ (e, not ə)"),
                           ("Soqotri", "ẓ̂éraṭ"): dict(form="ẑerót", reason="print: ẑerót (ẑ without dot, plain t; LS 365)"),
                           ("Syriac", "ˁurṭē, ˁurṭāyā"): dict(gloss="flatulence", reason="print: 'crepitus ventris', site: 'stomach growling'")}, pos="{{head|sem-pro|verb}}", infl=False, defs=["to [[fart]], to break [[wind]] audibly"], cat="", etym=""),
 "nayak-": dict(rec="995", vol="I", entry="*nyk", pos="{{head|sem-pro|verb}}", infl=False,
                conj="{{sem-pro-conj/*payala-*yipīl|n|y|k|vn=nayk}}",           # hollow root (medial y)
 defs=["to have [[sexual intercourse]]"], cat="", etym=""),
 "ḫaraš-": dict(rec="960", vol="I", entry="*ḫrš", exclude={("Amharic", "arräsä"): "Wiktionary's Amharic አረሰ is 'to plough', from *ḥaraṯ- (tests/test_conflicts.py)"}, pos="{{head|sem-pro|verb}}", infl=False, defs=["to be in [[childbed]], to be in [[confinement]]"], cat="", etym=""),
 "šiʔr-": dict(rec="691", vol="I", entry="*šiʔr-", pos="{{sem-noun|m}}", infl=True, defs=["[[flesh]]"], cat="{{C|sem-pro|Anatomy}}", etym=""),
 "śaḥm-": dict(rec="698", vol="I", entry="*ŝaḥm-", pos="{{sem-noun|m}}", infl=True, defs=["[[fat]]"], cat="", etym=""),
 "baḳḳ-": dict(rec="667", vol="II", entry="*baḳḳ-", pos="{{sem-noun|m}}", infl=True, defs=["[[gnat]]"], cat="{{C|sem-pro|Insects}}", etym=""),
}
def tree_lines(words, notes, exclude=(), override=None):
    lines, shown = [], set()
    for w in sorted(words, key=lambda w: ORDER.index(w["lang"])):
        if (w["lang"], w["form"]) in exclude:
            continue
        if override and (w["lang"], w["form"]) in override:
            w = {**w, **{k: v for k, v in override[(w["lang"], w["form"])].items() if k in ("form", "gloss")}}
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
def build(title, cfg, out=None):
    words = [w for w in read(DATA / "sedonline" / "sedonline_words.tsv") if w["rec_id"] == cfg["rec"]]
    miss = sorted({w["lang"] for w in words} - set(LANG))
    if miss: raise SystemExit(f"{title}: unmapped languages {miss}")
    notes = []
    d = ["{{reconstructed}}", "==Proto-Semitic==", ""]
    if cfg["etym"]: d += ["===Etymology===", cfg["etym"], ""]
    d += ["===" + ("Verb" if "verb" in cfg["pos"] else "Noun") + "===", cfg["pos"], ""] + ["# " + x for x in cfg["defs"]] + [""]
    if cfg["infl"]: d += ["====Inflection====", "{{sem-decl-noun}}", ""]
    if cfg.get("conj"): d += ["====Conjugation====", cfg["conj"], ""]
    d += ["====Descendants===="] + tree_lines(words, notes, cfg.get("exclude", {}), cfg.get("override")) + ["",
          "===References===", "* {{R:sem-pro:SED|volume=%s|id=%s|entry=%s}}" % (cfg["vol"], cfg["rec"], cfg["entry"])]
    if cfg["cat"]: d += ["", cfg["cat"]]
    dest = Path(out) if out else OUT
    dest.mkdir(exist_ok=True)
    (dest / f"Proto-Semitic_{title}.wiki").write_text("\n".join(d) + "\n", encoding="utf-8")
    if not out:
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
    """For every word on every page: the script form used, how it was made, and whether a Wiktionary entry exists for it
    (title = the spelling without vowel marks). Consonants are checked against the transliteration for the abjads."""
    sect = {"uga": "Ugaritic", "hbo": "Hebrew", "phn": "Phoenician", "ar": "Arabic", "xsa": "Sabaean", "sem-srb": "Old South Arabian", "jpa": "Jewish Palestinian Aramaic",
            "tmr": "Jewish Babylonian Aramaic", "arc": "Aramaic", "syc": "Classical Syriac", "sam": "Samaritan Aramaic", "am": "Amharic", "ti": "Tigrinya", "tig": "Tigre"}
    strip = lambda t: "".join(c for c in U.normalize("NFC", t) if not (0x591 <= ord(c) <= 0x5C7 or 0x64B <= ord(c) <= 0x652 or ord(c) in (0x670, 0x651) or 0x730 <= ord(c) <= 0x74A))
    seen, rows = set(), []
    for title, cfg in PAGES.items():
        for w in read(DATA / "sedonline" / "sedonline_words.tsv"):
            if w["rec_id"] != cfg["rec"] or w["lang"] not in LANG: continue
            code = LANG[w["lang"]][0]
            if code in LATIN_TERM or code == "akk" or "," in w["form"] or "/" in w["form"]: continue
            f = re.sub(r"\s*\((suff|det)[^)]*\)$", "", w["form"])
            sc, how = script_for(code, f)
            if not sc or (code, f) in seen: continue
            seen.add((code, f)); rows.append((code, f, sc, how))
    n_no = 0
    for code, f, sc, how in sorted(rows):
        t = strip(sc); c = page(t); s_ = sect.get(code)
        ok = bool(c) and bool(s_) and (f"=={s_}==" in c or (code == "hbo" and "==Biblical Hebrew==" in c) or (code == "arc" and "==Aramaic==" in c))
        cs = consistent(code, f, sc) if how == "curated" else None
        print(("ok     " if ok else "no page"), f"{code:8}", f"{f:14}", sc, f"({how})", "" if cs is None or cs[0] else f"| CONSONANT MISMATCH {cs}")
        n_no += not ok
    print(f"{len(rows)} script forms; {n_no} have no Wiktionary entry of that language (red links)")

def check_done(only=None):
    """Rebuild every page that is in wiktionary_drafts/done/ and compare it with the saved copy. The saved copy is never touched: a changed
    page is written to wiktionary_drafts/updates/ and a diff is printed, so you can decide what to change on the live page.
    Returns the titles that changed."""
    import difflib, tempfile
    UPD = OUT / "updates"
    changed = []
    for title, cfg in PAGES.items():
        saved = OUT / "done" / f"Proto-Semitic_{title}.wiki"
        if not saved.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            build(title, cfg, out=tmp)
            new = (Path(tmp) / saved.name).read_text(encoding="utf-8")
        old = saved.read_text(encoding="utf-8")
        stale = UPD / saved.name
        if new == old:
            print(f"done/{title}: unchanged")
            stale.unlink(missing_ok=True)
            continue
        changed.append(title)
        UPD.mkdir(exist_ok=True)
        stale.write_text(new, encoding="utf-8")
        print(f"done/{title}: CHANGED, new version in wiktionary_drafts/updates/{saved.name}")
        print("".join("    " + l for l in difflib.unified_diff(old.splitlines(True), new.splitlines(True), "saved", "regenerated", n=0)
                      if not l.startswith(("---", "+++"))))
    return changed

if __name__ == "__main__":
    if "--check-done" in sys.argv:
        sys.exit(1 if check_done() else 0)
    for t, cfg in PAGES.items():
        if (OUT / "done" / f"Proto-Semitic_{t}.wiki").exists():
            continue                                   # saved to Wiktionary: never overwritten; see check_done()
        if len(sys.argv) == 1 or t in sys.argv[1:]:
            build(t, cfg)
    changed = check_done()
    if changed:
        print(f"\n{len(changed)} page(s) already on Wiktionary would change: {', '.join(changed)} (wiktionary_drafts/updates/)")
