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
from tr2script import abjad, arabic, ethiopic, mandaic, cuneiform

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
        "Samaritan": ("sam", NW, ""), "Syriac": ("syc", NW, ""), "Mandaic": ("myz", NW, ""), "Turoyo": ("tru", NW, ""), "Maalula": ("amw", NW, ""), "Assyrian Neo-Aramaic": ("aii", NW, ""),
        "Christian Palestinian Aramaic": ("arc-cpa", NW, ""), "Hebrew": ("hbo", CAN, ""), "Phoenician": ("phn", CAN, ""), "Ugaritic": ("uga", NW, ""), "Ammonite": ("sem-amm", CAN, ""),
        "Sabaic": ("xsa", OSA, ""), "Minaean": ("inm", OSA, ""), "Hadramitic": ("sem-srb", OSA, "Hadramitic "), "Geez": ("gez", ETH, ""), "Tigre": ("tig", ETH, ""),
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
 ("hbo", "géleḏ"): "גֶּלֶד",              # Wiktionary's own Hebrew lemma גלד (etymology: from *gild-)
 ("hbo", "pānīm"): "פָּנִים",                  # plural tantum; the lemma page פנים
  ("hbo", "ʕakbār"): "עַכְבָּר", ("hbo", "pāgār"): "פָּגָר",
 ("ar", "f\u01efr"): "فَجَرَ",                   # fajara, as Wiktionary's Arabic فجر
 ("hbo", "yārēk"): "יָרֵךְ", ("hbo", "ṣəbī"): "צְבִי", ("hbo", "ˀimmēr"): "אִמֵּר", ("tru", "bōḳo"): "ܒܩܐ",      # Turoyo is written in Syriac script on Wiktionary (entry ܒܩܐ)

 ("ar", "mrḍ"): "مَرِضَ", ("ar", "ḍrṭ"): "ضَرَطَ", ("ar", "nyk"): "نَاكَ", ("ar", "ḫrs"): "خَرَّسَ",    # bare roots: the verb forms are chosen by hand
 ("he", "šḳl"): "שָׁקַל", ("phn", "šḳl"): "𐤔𐤒𐤋", ("uga", "ṯḳl"): "𐎘𐎖𐎍", ("ar", "ṯql"): "ثَقُلَ",        # *ṯḳl: bare NWS roots, lemmas as on Wiktionary (שקל, ثقل)
 ("arc", "tḳl"): "תקל", ("jpa", "tḳl"): "תקל", ("tmr", "tḳl"): "תקל", ("syc", "tḳl"): "ܬܩܠ", ("arc-cpa", "tḳl"): "ܬܩܠ", ("myz", "tḳl"): "ࡕࡒࡋ",
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
AKK_LEMMA = {"šaḳālu": "šaqālu", "warkatu": "warkatum", "warki": "warki", "marāṣu": "marāṣum", "immeru": "immerum", "ṣabītu": "ṣabītum", "baqqu": "baqqum", "baḳḳu": "baqqum", "ṣarātu": "ṣarātum", "nâku": "nâkum", "ḫarāšu": "ḫarāšum", "šīru": "šīrum", "šēmu": "šēmum", "pānu": "pānum", "nâku": "niākum", "kišādu": "kišādum", "pagru": "pagrum", "akbaru": "akbarum"}
# no lemma page: (lemma, cuneiform, its transliteration). The cuneiform is as cited on Wiktionary's Arabic بق and Classical Syriac ܒܩܐ;
# tests/test_cuneiform.py checks that the transliteration really gives it (eBL sign list).
AKK_OVERRIDE = {"baḳḳu": ("baqqu", "𒁀𒀝𒄣", "ba-aq-qu"),
                "ṣabītu": ("ṣabītum", "𒈦𒁕", "MAŠ.DA"),    # the Sumerogram is the usual writing (CAD Ṣ 42 "wr. syll. and MAŠ.DÀ"); signs as drawn at assyrianlanguages.org/akkadian (entry ṣabītu 2, MAŠ.DA)
                "gildu": ("gildu", "𒋢𒄀𒅋𒁺", None)}   # cuneiform as on Wiktionary's Hebrew גלד / Syriac ܓܠܕܐ (transliteration of the spelling not given)
def akkadian(form):
    """-> (lemma, phonetic cuneiform spelling from the page's {{cunsp}}, or None)"""
    if form in AKK_OVERRIDE:
        return AKK_OVERRIDE[form][:2]
    lemma = AKK_LEMMA.get(form, form)
    c = page(lemma)
    sec = c[c.find("==Akkadian=="):] if c and "==Akkadian==" in c else ""
    m = re.search(r"\|phon=([^<\n|]+)", sec)
    if m: return lemma, m.group(1)
    n = cuneiform.normalise(lemma)                          # no spelling on Wiktionary: a normalised plene spelling (pānu -> pa-a-nu), flagged in the notes
    cun = cuneiform.convert(n) if n else None
    return lemma, cun

def AKK_ON_WIKT_CACHE():
    return {l for l in set(AKK_LEMMA.values()) | {"niākum"} if (page(l) or "").find("|phon=") >= 0}
def tr_of(f):
    return U.normalize("NFC", f).replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ḳ", "q").replace("ǝ", "ə").replace("γ", "ɣ").replace("ŝ", "ś")      # descendants: Wiktionary's tr uses q (PS titles keep ḳ)
TRANSLATE = {"im Kindbett liegen": "to be in childbed", "partorire (to give birth)": "to give birth", "accouché": "woman who has given birth", "the sacrup or rump of a butchered animal": "the sacrum or rump of a butchered animal", "Hüfte": "hip", "Wanzen (bugs)": "bugs", "Mücke (mosquito)": "mosquito", "guérir": "to heal"}
def script_for(code, form):
    """-> (script, how) with how in curated / ethiopic / abjad, or (None, None)."""
    if (code, form) in CURATED:
        return CURATED[(code, form)], "curated"
    sc = ethiopic.convert(code, form) if code in ethiopic.PROFILES else None
    if sc: return sc, "ethiopic"
    sc = arabic.convert(form) if code == "ar" else None
    if sc: return sc, "arabic"
    sc = mandaic.convert(code, form) if code == "myz" else None
    if sc: return sc, "mandaic"
    sc = abjad.convert(code, form)
    return (sc, "abjad") if sc else (None, None)
def one(code, form, notes, first, gloss, lang):
    """One {{desc}} (first variant) or {{l}} (further variants) with the best script available."""
    head = "desc" if first else "l"
    t = f"|t={gloss}" if (gloss and first) else ""
    if code == "akk":
        lemma, cun = akkadian(form)
        if not cun: notes.append(f"Akkadian {lemma}: no cuneiform (no Wiktionary lemma page, no convertible normalised spelling)")
        elif form not in AKK_OVERRIDE and lemma not in AKK_ON_WIKT_CACHE(): notes.append(f"Akkadian {lemma}: {cun} (NORMALISED spelling {cuneiform.normalise(lemma)}, not an attestation)")
        return f"{{{{{head}|akk|{lemma}" + (f"|alt={cun}" if cun else "") + f"|tr={lemma}{t}}}}}"
    if code in LATIN_TERM:
        return f"{{{{{head}|{code}|{tr_of(form)}{t}}}}}"
    sc, how = script_for(code, form)
    if sc and how != "curated":
        notes.append(f"{lang} {form}: {sc} ({how})")
    if sc is None:
        return f"{{{{{head}|{code}|-|tr={tr_of(form)}{t}}}}}"
    if code in AUTO_TR or (code == "myz" and mandaic.translit(sc) == tr_of(form).replace("ʕ", "ʿ")):        # Wiktionary's own transliteration gives the same
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
        if code in LATIN_TERM:                              # the term itself is already the transliteration: no separate tr=
            return f"{{{{desc|{code}|{tr_of(form)}" + (f"|t={gloss}" if gloss else "") + "}}"
        return f"{{{{desc|{code}|-|tr={tr_of(form)}" + (f"|t={gloss}" if gloss else "") + "}}"
    variants = [v.strip() for v in form.split(",") if v.strip()]
    if code == "xeb":                                       # Eblaite variants are alternative spellings of one word
        variants = variants[:1]
    return ", ".join(one(code, v, notes, i == 0, gloss, lang) for i, v in enumerate(variants))

PAGES = {   # title -> SEDonline reconstruction id and page content
 "warik-": dict(rec="758", vol="I", entry="*warik(-at)-", pos="{{sem-noun|m|g2=f}}", infl=True,
                defs=["[[hip]], [[hipbone]]", "[[haunch]], upper [[thigh]]"], cat="{{C|sem-pro|Anatomy}}",
                etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' with an optional feminine suffix {{m|sem-pro|*-at-}}: {{m|sem-pro|*warik(-at)-}}."),
 "ṯ̣aby-": dict(rec="624", vol="II", entry="*ṯ̣aby(-at)-", override={("Mandaic", "ṭabia"): dict(gloss="gazelle, deer", reason="print: ṭabia 'gazelle, deer' [DM 173], site: 'deer'")}, pos="{{sem-noun|m|g2=f}}", infl=True, defs=["[[gazelle]]"], cat="{{C|sem-pro|Mammals}}",
               etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' with an optional feminine suffix {{m|sem-pro|*-at-}}: {{m|sem-pro|*ṯ̣aby(-at)-}}."),
 "maraṣ́-": dict(rec="894", vol="I", entry="*mrṣ̂", pos="{{head|sem-pro|verb}}", infl=False,
                 conj="{{sem-pro-conj/*paʕala-*yipʕal|m|r|ṣ́|vn=marṣ́}}",        # SED: Akkadian marāṣu (a/a)
 defs=["to be [[sick]], [[ill]]"], cat="", etym=""),
 "ṣ́araṭ-": dict(rec="1023", vol="I", entry="*ṣ̂rṭ",
                 # where the printed SED differs from SEDonline the draft follows the print (read at 650 dpi; data/sedonline/form_check.tsv)
                 override={("Harsusi", "ẑərōṭ"): dict(form="ẑerōṭ", reason="print: ẑerōṭ (e, not ə)"),
                           ("Soqotri", "ẓ̂éraṭ"): dict(form="ẑerót", reason="print: ẑerót (ẑ without dot, plain t; LS 365)"),
                           ("Syriac", "ˁurṭē, ˁurṭāyā"): dict(gloss="flatulence", reason="print: 'crepitus ventris', site: 'stomach growling'")}, pos="{{head|sem-pro|verb}}", infl=False,
                 conj="{{sem-pro-conj/*paʕal-*yipʕul|ṣ́|r|ṭ|vn=ṣ́arṭ}}",         # SED: Akkadian ṣarātum (u/u), Arabic ḍaraṭa (u) -- u-class template added to Wiktionary since the draft was first written
                 defs=["to [[fart]], to break [[wind]] audibly"], cat="", etym=""),
 "nayak-": dict(rec="995", vol="I", entry="*nyk", pos="{{head|sem-pro|verb}}", infl=False,
                conj="{{sem-pro-conj/*payala-*yipīl|n|y|k|vn=nayk}}",           # hollow root (medial y)
                override={("Arabic", "nyk"): dict(gloss="to cohabit with a woman", reason="print: 'cohabiter avec une femme' [BK 2 1376]; site: 'to marry a woman'")},
 defs=["to have [[sexual intercourse]]"], cat="", etym=""),
 "ḫaraš-": dict(rec="960", vol="I", entry="*ḫrš", exclude={("Amharic", "arräsä"): "Wiktionary's Amharic አረሰ is 'to plough', from *ḥaraṯ- (tests/test_conflicts.py)"}, pos="{{head|sem-pro|verb}}", infl=False, defs=["to be in [[childbed]], to be in [[confinement]]"], cat="", etym="",
              extra_refs=["{{R:akk:CAD|volume=6|pages=95-96|entry=ḫarāšu A}}"]),  # sense (3), "(uncert. mng.)"; only D- and Š-stem forms cited there, no bare G-stem -- doesn't give the conjugation class either, but worth citing
 "šiʔr-": dict(rec="691", vol="I", entry="*šiʔr-", pos="{{sem-noun|m}}", infl=True, defs=["[[flesh]]"], cat="{{C|sem-pro|Anatomy}}", etym=""),
 "śaḥm-": dict(rec="698", vol="I", entry="*ŝaḥm-",
              exclude={("Arabic", "šaḥuma"): "site only: the print gives Arabic šaḥm- (BK 1 1199) alone"},
              override={("Jibbali", "ŝḥm\u1f73t"): dict(form="śḥəmét", reason="print: ŝḥəmét [JJ 250] (with ə), site ŝḥmέt")}, pos="{{sem-noun|m}}", infl=True, defs=["[[fat]]"], cat="", etym=""),
# SED I no. 78 *gi/ald- 'skin, hide'. SEDonline files it as Proto-West Semitic and differs from the print (it lacks Official Aramaic, Palmyrene,
 # Neo-Aramaic, Soqotri; it adds Turoyo and Bathari, which the print does not have), so the words are those of the PRINTED entry, read by eye
 # from tests/../build crops (data/sedonline/form_check.tsv). Left out: Middle Mandaic gelda (no code), Azerbaijan and Iranian Neo-Aramaic
 # (Garbell, Pennacchietti: no verified Wiktionary code), Turoyo galdo and Bathari gawd (site only).
 "gild-": dict(rec="704", vol="I", entry="*gi/ald-", print_sourced=True, pos="{{sem-noun|m}}", infl=True, defs=["[[skin]], [[hide]]"],
               cat="{{C|sem-pro|Anatomy}}",
               etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*gi/ald-}}. The SED notes that Akkadian {{m|akk|gildu}} is, "
                    "according to von Soden, from Aramaic, and that the only attested Hebrew form, the hapax {{m|hbo|גלדי|tr=gildī}} \"my skin\" (Job 16:15), is usually considered an Aramaic borrowing.",
               words=[dict(lang="Akkadian", form="gildu", gloss="hide", unc=True),
                      dict(lang="Hebrew", form="géleḏ", gloss="skin", unc=True),
                      dict(lang="Official Aramaic", form="gldʔ", gloss="hide, skin"),
                      dict(lang="Palmyrean", form="gldyʔ", gloss="hide, skin"),
                      dict(lang="Jewish Babylonian Aramaic", form="gildā", gloss="plate, covering, skin, leather"),
                      dict(lang="Syriac", form="geldā", gloss="skin, hide"),
                      dict(lang="Mandaic", form="gilda", gloss="testicle, leather"),
                      dict(lang="Maalula", form="γelta", gloss="skin"),
                      dict(lang="Assyrian Neo-Aramaic", form="γildä", gloss="skin, hide"),
                      dict(lang="Arabic", form="ǧild-, ǧalad-, ǧilid-", gloss="skin, leather"),
                      dict(lang="Geez", form="gald", gloss="skin, hide"),
                      dict(lang="Tigre", form="gəldät", gloss="hairless skin of animals"),
                      dict(lang="Mehri", form="gēd", gloss="skin, hide (pl. gəlēd)"),
                      dict(lang="Harsusi", form="gōd", gloss="skin, leather (pl. gelēd)"),
                      dict(lang="Jibbali", form="gɔ́d", gloss="skin (pl. gíẑéd)"),
                      dict(lang="Soqotri", form="gad", gloss="skin, leather (pl. ʔegélid)"),
                      dict(lang="Soqotri", form="gēldəh", gloss="skin", q="Qalansiyah")]),
 # SED I no. 215 *pan- 'face'. SEDonline files it as *pan(ay)- with a much wider word list (and Soqotri fíni), so the words are those of the
 # PRINTED entry, read by eye (data/sedonline/form_check.tsv). Left out: Moabite pny (no verified code/script), and the words the SED
 # calls derived (Arabic fināʔ-, Sabaic fnw, Minaean fnwt, Mehri fənfənw-, fōnəh, Harsusi fēn, fenōhen), mentioned in the etymology.
 "pan-": dict(rec="347", vol="I", entry="*pan-", print_sourced=True, pos="{{sem-noun|m}}", infl=True, defs=["[[face]]"],
              cat="{{C|sem-pro|Anatomy}}",
              etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*pan-}}. The SED regards Arabic {{m|ar|فِنَاء}} (\"yard\") "
                   "and Sabaic and Minaean ''fnw(t)'' (\"space outside a building\") as probably derived from this root, as well as the Modern South Arabian adverbs "
                   "such as Mehri {{m|gdq|fōnəh}} (\"earlier\"). Hebrew {{m|hbo|פָּנִים|tr=pānīm}} is a plural-only noun.",
              words=[dict(lang="Akkadian", form="pānu", gloss="front side, face"),
                     dict(lang="Ugaritic", form="pn", gloss="face"),
                     dict(lang="Phoenician", form="pn", gloss="face"),
                     dict(lang="Hebrew", form="pānīm", gloss="face"),
                     dict(lang="Official Aramaic", form="pnh", gloss="face"),
                     dict(lang="Jibbali", form="fέnε", gloss="face, front part"),
                     dict(lang="Soqotri", form="fáne", gloss="face")]),
 # SED I no. 147 *ki(n)šād- 'neck, top of shoulder' (print ◊ *ki(n)sād-), SED I no. 209 *pagr-, SED II no. 30 *ʕakbar-: SEDonline
 # differs from the print in the cognate sets (data/sedonline/form_check.tsv), so the words are those of the PRINTED entries, read by eye.
 "kišād-": dict(rec="707", vol="I", entry="*ki(n)šād-", print_sourced=True, pos="{{sem-noun|m}}", infl=True, defs=["[[neck]]", "top of the [[shoulder]]"],
                cat="{{C|sem-pro|Anatomy}}",
                etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*ki(n)šād-}}. The Modern South Arabian nasal is not found elsewhere. "
                     "According to Kaufman, Mandaic {{m|myz|ࡊࡔࡀࡃࡀ}} is rather \"a neck ornament\" borrowed from Akkadian.",
                override={("Geez", "kəsād"): dict(form="kəśād", reason="print: kəsād, kəŝād; ŝ is purely graphic, the Ge'ez spelling has ሠ (ክሣድ)")},
                words=[dict(lang="Akkadian", form="kišādu", gloss="neck, throat; necklace"),
                       dict(lang="Mandaic", form="kšada", gloss="throat", unc=True),
                       dict(lang="Geez", form="kəsād", gloss="neck"),
                       dict(lang="Tigrinya", form="kəsad", gloss="neck"),
                       dict(lang="Amharic", form="kəsad", gloss="collar"),
                       dict(lang="Mehri", form="kənsīd", gloss="top of the shoulder"),
                       dict(lang="Harsusi", form="kənsīd", gloss="shoulder"),
                       dict(lang="Jibbali", form="kənséd", gloss="shoulder")]),
 "pagr-": dict(rec="688", vol="I", entry="*pagr-", print_sourced=True, pos="{{sem-noun|m}}", infl=True, defs=["[[body]]", "[[corpse]]"],
               cat="{{C|sem-pro|Anatomy}}", etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*pagr-}}.",
               words=[dict(lang="Akkadian", form="pagru", gloss="body, trunk"),
                      dict(lang="Ugaritic", form="pgr", gloss="body, corpse as a funerary offering", unc=True),
                      dict(lang="Hebrew", form="pāgār", gloss="corpse"),
                      dict(lang="Old Aramaic", form="pgr", gloss="body"),
                      dict(lang="Official Aramaic", form="pgr", gloss="body"),
                      dict(lang="Palmyrean", form="pgr", gloss="body"),
                      dict(lang="Jewish Palestinian Aramaic", form="pgr", gloss="body"),
                      dict(lang="Jewish Babylonian Aramaic", form="pagrā", gloss="body"),
                      dict(lang="Syriac", form="pagrā", gloss="body, corpse"),
                      dict(lang="Mandaic", form="pagra", gloss="body"),
                      dict(lang="Arabic", form="f\u01efr", gloss="to commit adultery, fornication with a woman", unc=True)]),
 "ʕakbar-": dict(rec="504", vol="II", entry="*ʕakbar-", print_sourced=True, pos="{{sem-noun|m}}", infl=True, defs=["[[mouse]]", "[[jerboa]]"], cat="{{C|sem-pro|Rodents}}",
                 etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*ʕakbar-}}. The SED also compares several terms with metathesis, "
                      "meaning shifts or secondary emphasis, such as Syriac {{m|syc|ܥܘܩܒܪܐ|tr=ʕuḳbərā}} and the Modern South Arabian forms like Mehri {{m|gdq|ʔārḳáyb}}.",
                 words=[dict(lang="Akkadian", form="akbaru", gloss="jerboa"),
                        dict(lang="Hebrew", form="ʕakbār", gloss="mouse"),
                        dict(lang="Samaritan", form="ʕkbr", gloss="mouse"),
                        dict(lang="Jewish Palestinian Aramaic", form="ʕkbr", gloss="mouse"),
                        dict(lang="Jewish Babylonian Aramaic", form="ʕakbərā", gloss="mouse"),
                        dict(lang="Arabic", form="ʕakābir-", gloss="a kind of mouse (plural)")]),
 "baḳḳ-": dict(rec="667", vol="II", entry="*baḳḳ-", pos="{{sem-noun|m}}", infl=True, defs=["[[gnat]]"], cat="{{C|sem-pro|Insects}}", etym=""),
 "sūs-": dict(rec="675", vol="II", entry="*sā/ūs-", pos="{{sem-noun|m}}", infl=True, defs=["[[moth]]"], cat="{{C|sem-pro|Insects}}", etym="",
              # Syriac is cited by SEDonline as "sūstā, sāsā" under one combined gloss; sūstā is the unrelated word for "mare" (fem. of sūsyā
              # "horse"), bundled in as a cross-reference. Only sāsā, the real cognate, is kept here.
              words=[dict(lang="Akkadian", form="sāsu", gloss="moth"),
                     dict(lang="Ebla", form="zazum /sāsum/", gloss="moth", unc=True),
                     dict(lang="Hebrew", form="sās", gloss="clothes moth"),
                     dict(lang="Old Aramaic", form="ss", gloss="moth"),
                     dict(lang="Official Aramaic", form="ss", gloss="moth"),
                     dict(lang="Jewish Palestinian Aramaic", form="ss", gloss="moth, worm"),
                     dict(lang="Syriac", form="sāsā", gloss="kind of worm that infests the grapevine"),
                     dict(lang="Mandaic", form="sasa", gloss="moth, maggot"),
                     dict(lang="Arabic", form="sūs-", gloss="moth"),
                     dict(lang="Amharic", form="šuš(š)", gloss="moth"),
                     dict(lang="Harari", form="sūs", gloss="moth"),
                     dict(lang="Mehri", form="sust", gloss="large worm")]),
 # SED II no. 53 *bVʕVr- 'household animal; beast of burden' (rec. 590). SEDonline's word list and gloss ("bull") both differ from the
 # print (data/sedonline/sed_print_vs_site_agreement.tsv: agree=0); read by eye (pdf/vol2.pdf pp. 164-165). The print explicitly excludes
 # a whole cluster of forms without -ʕ- that SEDonline includes anyway (Akkadian bīru/būru, Mandaic bira, Amharic bäre, Harari bāra, and
 # the Gurage forms), discussing them separately as a *possibly* related but distinct root -- not something to fold into this entry.
 # Also left out: Tigre baʕer "young camel", which the print itself flags as "an obvious Arabism".
 "bVʕVr-": dict(rec="590", vol="II", entry="*bVʕVr-", print_sourced=True, pos="{{sem-noun|m}}", infl=True,
                defs=["[[household]] [[animal]]", "[[beast of burden]]"], cat="{{C|sem-pro|Mammals}}",
                etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*bVʕVr-}}. The SED notes that a cluster of semantically "
                     "similar forms lacking the {{m|sem-pro|*ʕ}} (Akkadian {{m|akk|bīru}}, Mandaic {{m|myz|ࡁࡉࡓࡀ|tr=bira}}, and several Ethiopian Semitic forms such "
                     "as Amharic {{m|am|በሬ|tr=bäre}}) may continue a separate, though probably related, root.",
                words=[dict(lang="Ammonite", form="bʕr", gloss="ox, beast of burden", unc=True),
                       dict(lang="Hebrew", form="bəʕīr", gloss="livestock, cattle"),
                       dict(lang="Jewish Babylonian Aramaic", form="bəʕīrā", gloss="grazing animal, cattle"),
                       dict(lang="Syriac", form="bəʕīrā", gloss="cattle, beast of burden"),
                       dict(lang="Assyrian Neo-Aramaic", form="bîrâ", gloss="large cattle"),
                       dict(lang="Arabic", form="baʕīr-", gloss="camel; beast of burden"),
                       dict(lang="Sabaic", form="bʕr", gloss="cattle, head of cattle; camel"),
                       dict(lang="Minaean", form="bʕr", gloss="camel; head of cattle"),
                       dict(lang="Hadramitic", form="bʕr", gloss="commercial livestock"),
                       dict(lang="Geez", form="bəʕər, bəʕərā, bəʕərāy, bəʕərāwi", gloss="ox, bull, horned cattle"),
                       dict(lang="Tigre", form="bəʕrāy", gloss="ox, bull"),
                       dict(lang="Tigrinya", form="bəʕray, bäʕray", gloss="ox, bull"),
                       dict(lang="Mehri", form="bəʕáyr", gloss="male camel"),
                       dict(lang="Mehri", form="béyr", gloss="male camel"),
                       dict(lang="Harsusi", form="beʕîr", gloss="male camel"),
                       dict(lang="Soqotri", form="beʕer", gloss="camel"),
                       dict(lang="Soqotri", form="baʕáhar", gloss="she-camel")]),
 # SED II no. 221 *ŝabb- ~ *ĉabb- 'kind of lizard' (rec. 656). SEDonline's gloss ("monitor lizard") is narrower than the print's, and it
 # drops Jewish Aramaic entirely (data/sed_print_vs_site_agreement.tsv: agree=0); read by eye (pdf/vol2.pdf p. 378). The print itself
 # explains the vaguer gloss: Hebrew and Jewish Aramaic point to a different (spiny-tailed) lizard than the monitor lizard of Arabic and
 # the Modern South Arabian languages, so "kind of lizard" is the honest common denominator, not a simplification.
 # No East Semitic member and SEDonline's own "level" field marks this PWS (sed_print_vs_site_agreement.tsv, rec 656), so it belongs
 # at Proto-West Semitic, not Proto-Semitic -- {{head|sem-wes-pro|noun}}, no Inflection section (no Template:sem-wes-decl-noun exists).
 "ṣ́abb-": dict(rec="656", vol="II", entry="*ṣ̂abb-", print_sourced=True, level="PWS", pos="{{head|sem-wes-pro|noun|g=m}}", infl=True, defs=["kind of [[lizard]]"], cat="{{C|sem-wes-pro|Reptiles}}",
               etym="Reconstructed in Militarev & Kogan's ''Semitic Etymological Dictionary'' as {{m|sem-pro|*ṣ́abb-}}. The reflexes split between a "
                    "thorn-tailed/spiny-tailed lizard (Hebrew, Jewish Aramaic) and the monitor lizard (Arabic, Modern South Arabian); the SED keeps the gloss "
                    "general for this reason. The Jewish Aramaic form is noted in the SED as possibly a Hebrew borrowing, since its {{m|sem-pro|*ṣ}} is irregular.",
               words=[dict(lang="Hebrew", form="ṣāb", gloss="thorn-tailed lizard"),
                      dict(lang="Jewish Babylonian Aramaic", form="ṣabbā", gloss="kind of lizard", unc=True),
                      dict(lang="Syriac", form="ʕabbā", gloss="kind of lizard"),
                      dict(lang="Arabic", form="ḍabb-", gloss="monitor lizard; African lizard (eaten by some peoples)"),
                      dict(lang="Mehri", form="ẑōb", gloss="male monitor lizard"),
                      dict(lang="Mehri", form="ẑəbbūt", gloss="female monitor lizard"),
                      dict(lang="Harsusi", form="ẑōb", gloss="monitor lizard"),
                      dict(lang="Harsusi", form="ẑebbēt", gloss="female monitor lizard"),
                      dict(lang="Jibbali", form="ẓ̂ɔb", gloss="monitor lizard"),
                      dict(lang="Jibbali", form="ẓ̂ēt", gloss="female monitor lizard")]),
}
# SED has no printed entry for this verb: SEDonline (rec 2030, source HALOT 1642) alone reconstructs it, so there is no volume= and the page is flagged in data/sedonline/form_check.tsv.
PAGES["ṯḳl"] = dict(rec="2030", entry="*ṯḳl", site_only=True, codes={"Hebrew": "he"},
    override={("Ebla", "ša-ga-lum /ṯaḳālum/"): dict(form="ṯaḳālum", reason="site: ša-ga-lum /ṯaḳālum/ (the cited spelling and its reading)")},
    pos="{{head|sem-pro|verb}}", infl=False, conj="{{sem-pro-conj/*paʕala-*yipʕal|ṯ|ḳ|l|vn=ṯaḳl}}",          # a/u in Akkadian šaqālu; the bare verb page, as ʔbd and ʔdm (data/wiktionary/root_vs_verb.md)
    defs=["to [[weigh]]", "to [[suspend]]"], cat="", etym="")
def tree_lines(words, notes, exclude=(), override=None, strip=(), codes=None):
    """strip: a leading path prefix to drop (e.g. ("West Semitic",) on a Proto-West Semitic page, where it is implied)."""
    lines, shown = [], set()
    for w in sorted(words, key=lambda w: ORDER.index(w["lang"])):
        if (w["lang"], w["form"]) in exclude:
            continue
        if override and (w["lang"], w["form"]) in override:
            w = {**w, **{k: v for k, v in override[(w["lang"], w["form"])].items() if k in ("form", "gloss")}}
        code, path, label = LANG[w["lang"]]
        if strip and path[:len(strip)] == strip:
            path = path[len(strip):]
        code = (codes or {}).get(w["lang"], code)                  # a page may use another Wiktionary code for a language (Hebrew: he, as WT:ASEM's tree has it)
        g = re.sub(r"\s+", " ", w["gloss"]).strip().replace("|", "/")
        e = entry(code, w["form"], g, w["lang"], notes)
        for key, val in (("q", w.get("q") or DIALECT.get(w["lang"])), ("unc", "1" if w.get("unc") else None)):
            if val:
                e = re.sub(r"\}\}", f"|{key}={val}}}}}", e, count=1)
        for d in range(len(path)):
            if path[:d + 1] not in shown:
                shown.add(path[:d + 1]); lines.append("*" * (d + 1) + " " + path[d] + ":")
        lines.append("*" * (len(path) + 1) + " " + label + e)
    return lines
def build(title, cfg, out=None):
    words = cfg["words"] if cfg.get("words") else [w for w in read(DATA / "sedonline" / "sedonline_words.tsv") if w["rec_id"] == cfg["rec"]]
    miss = sorted({w["lang"] for w in words} - set(LANG))
    if miss: raise SystemExit(f"{title}: unmapped languages {miss}")
    notes = []
    pws = cfg.get("level") == "PWS"                             # PWS: no Template:sem-wes-decl-noun / sem-wes-noun exist yet (checked live);
    lang = "Proto-West Semitic" if pws else "Proto-Semitic"      # {{head|sem-wes-pro|...}} and no declension table, following real PWS pages
    d = ["{{reconstructed}}", f"=={lang}==", ""]
    if cfg["etym"]: d += ["===Etymology===", cfg["etym"], ""]
    d += ["===" + ("Root" if "root" in cfg["pos"] else "Verb" if "verb" in cfg["pos"] else "Noun") + "===", cfg["pos"], ""] + ["# " + x for x in cfg["defs"]] + [""]
    if cfg["infl"] and not pws: d += ["====Inflection====", "{{sem-decl-noun}}", ""]
    if cfg.get("conj"): d += ["====Conjugation====", cfg["conj"], ""]
    d += ["====Descendants===="] + tree_lines(words, notes, cfg.get("exclude", {}), cfg.get("override"), strip=("West Semitic",) if pws else (), codes=cfg.get("codes")) + ["",
          "===References===", "* {{R:sem-pro:SED|" + (f"volume={cfg['vol']}|" if cfg.get("vol") else "") + f"id={cfg['rec']}|entry={cfg['entry']}}}}}"]
    for r in cfg.get("extra_refs", []): d.append("* " + r)
    if cfg["cat"]: d += ["", cfg["cat"]]
    dest = Path(out) if out else OUT
    dest.mkdir(exist_ok=True)
    fname = f"Proto-West_Semitic_{title}.wiki" if pws else f"Proto-Semitic_{title}.wiki"
    (dest / fname).write_text("\n".join(d) + "\n", encoding="utf-8")
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
