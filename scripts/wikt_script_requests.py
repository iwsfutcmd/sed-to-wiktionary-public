"""Terms in Semitic languages that Wiktionary lists as needing their native script, and which of them our converters can supply.
usage: wikt_script_requests.py [LANGUAGE ...]      (network) -> data/wiktionary/script_requests.json

Every page in "Category:Requests for native script for <Language> terms" is read; each template that names a term of that language with no
script (term empty or "-", a tr=/ts= given) is one request. Templates and the position of their language code and term:
  {{desc|CODE|TERM}} {{l|CODE|TERM}} {{m|CODE|TERM}} {{cog|CODE|TERM}} ...         CODE at 1, TERM at 2
  {{inh|SRC|CODE|TERM}} {{der|..}} {{bor|..}} ...                                    CODE at 2, TERM at 3
The conversion itself is done by suggest(), which refuses anything uncertain (see its docstring)."""
import json, re, sys, urllib.parse, urllib.request, unicodedata as U
from paths import WIKT
import wikt_conflicts as K

OUT = WIKT / "script_requests.json"
UA = K.UA
FIRST = {"desc", "desctree", "l", "l-lite", "m", "m-lite", "mention", "link", "cog", "cognate", "noncog", "ncog", "nc", "m+", "l+", "alt", "alter", "syn", "ant"}
SECOND = {"inh", "inh+", "inh-lite", "der", "der+", "der-lite", "bor", "bor+", "lbor", "slbor", "obor", "cal", "calque", "pcal", "psm", "uder", "ubor"}
LANGUAGES = ["Akkadian", "Aramaic", "Arabic", "Assyrian Neo-Aramaic", "Sabaean", "Classical Syriac", "Eblaite", "Silt'e", "Classical Mandaic", "Ge'ez",
             "Hebrew", "Mandaic", "Ugaritic", "Amharic", "Tigrinya", "Turoyo", "Zay", "Gafat", "Harari", "Phoenician", "Tigre", "Jewish Babylonian Aramaic",
             "Kistane", "Minaean", "Qatabanian", "Sebat Bet Gurage", "Argobba", "Biblical Aramaic", "Imperial Aramaic", "Mesqan", "Wolane", "Inor",
             "Mehri", "Shehri", "Soqotri", "Harsusi", "Western Neo-Aramaic", "Lishana Deni", "Mlahsö", "Chaldean Neo-Aramaic", "Hulaulá", "Amorite", "Safaitic"]

def api(**q):
    d = urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php?" + urllib.parse.urlencode(dict(format="json", formatversion=2, **q)), headers=UA), timeout=60)
    return json.load(d)

def members(language):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle=f"Category:Requests for native script for {language} terms", cmlimit=500, **cont)
        out += [p["title"] for p in d["query"]["categorymembers"]]
        if "continue" not in d:
            return out
        cont = d["continue"]

def templates(text):
    """-> [(start, end, name, positional args, named args)] for every {{...}} that contains no nested template."""
    for m in re.finditer(r"\{\{([^{}|]+)((?:\|[^{}]*)?)\}\}", text):
        parts = m.group(2).split("|")[1:]
        pos, named = [], {}
        for p in parts:
            k = re.match(r"\s*([a-z0-9]+)\s*=(.*)$", p, re.S)
            if k and not k.group(1).isdigit():
                named[k.group(1)] = k.group(2).strip()
            else:
                pos.append(p.strip())
        yield m.start(), m.end(), m.group(1).strip(), pos, named

def requests(text, code):
    """Template uses of `code` with no script but a transliteration: [(start, end, name, term index, tr, gloss)]."""
    out = []
    for a, b, name, pos, named in templates(text):
        if name in FIRST:
            ci, ti = 0, 1
        elif name in SECOND:
            ci, ti = 1, 2
        else:
            continue
        if len(pos) <= ci or pos[ci] != code:
            continue
        term = pos[ti] if len(pos) > ti else ""
        tr = named.get("tr") or named.get("ts") or ""
        if term.strip() not in ("", "-") or not tr:
            continue
        out.append(dict(start=a, end=b, template=text[a:b], name=name, tr=tr, ts=bool(named.get("ts") and not named.get("tr")),
                        gloss=named.get("t") or named.get("gloss") or (pos[ti + 2] if len(pos) > ti + 2 else "")))
    return out

from tr2script import abjad, ethiopic, cuneiform

# Wiktionary writes these in Latin (checked: no "nonstandard script" category), so the transliteration simply becomes the term
# Not Modern South Arabian (Mehri, Shehri, Soqotri, Harsusi): their requests often carry old transcriptions in another scheme and are left for
# someone who knows the language (Catonif, 2026-10-30). Not Turoyo: Wiktionary expects Syriac script (Fay Freak undid a Latin Turoyo term).
LATIN = {"akk", "amw"}
# consonantal scripts: a transliteration with no vowels maps letter for letter (Aramaic in the square script, its default on Wiktionary)
CONSONANTAL = {"xsa", "inm", "xqt", "xhd", "sem-srb", "phn", "uga"}       # not Aramaic: which script (square? Imperial?) needs a source
# Scripts where the transliteration maps to the script without guessing, so a fill may go ahead when nothing confirms it, as long as nothing
# contradicts it either (the sound-law check must not fail): the user reviewed and kept such fills (2026-10-31). Ethiopic only in Wiktionary's
# own transliteration scheme (suggest() checks that); Eblaite only from unindexed, undisputed signs (cuneiform.convert refuses the rest).
LOSSLESS = {"xsa", "inm", "xqt", "xhd", "sem-srb", "myz", "xeb", "gez", "am", "ti", "tig", "har", "stv", "zwa", "gft", "gru", "sgw", "agj", "mvz", "wle"}
ETHIOPIC = {"gez", "am", "ti", "tig", "har", "stv", "zwa", "gft", "gru", "sgw", "agj", "mvz", "wle"}
VOWELS = re.compile(r"[aeiouāēīōūăĕŏəäɛɔâêîôûáéíóú]", re.I)

def suggest(code, tr, ts=False):
    """-> (new term, how) or (None, why not). Refuses: several forms, syllabic spellings where a word is wanted, letters outside the tables,
    Ethiopic transliterations not in Wiktionary's own scheme (no ä/ə to show it), Arabic (many requests are garbled loan sources)."""
    t = U.normalize("NFC", tr.strip())
    if not t or re.search(r"[,;/()\[\]?]|\s", t):
        return None, "several forms or a note in the transliteration"
    if code in LATIN:
        if "-" in t.strip("-") and code == "akk":
            return None, "a syllabic spelling, not the word"
        return t, "Latin script is the standard for this language: the transliteration becomes the term"
    if code in CONSONANTAL:
        if VOWELS.search(t):
            return None, "vocalised: the spelling (matres lectionis) is not certain"
        sc = abjad.convert(code, t)
        return (sc, "consonantal transliteration, letter for letter") if sc else (None, "a letter the table does not have")
    if code == "xeb":
        if not re.fullmatch(r"[\w\u0300-\u036f₀-₉]+(?:-[\w\u0300-\u036f₀-₉]+)+", t):
            return None, "not a syllabic spelling"
        sc = cuneiform.convert(t)
        return (sc, "syllabic spelling, sign by sign (eBL sign list)") if sc else (None, "a sign the list does not have")
    if code == "myz":
        sc = mandaic.convert("myz", t)
        return (sc, "Mandaic writes its vowels: converted letter for letter") if sc else (None, "not convertible")
    if code in ETHIOPIC:
        if not re.search(r"[äə]", t):
            return None, "not clearly in Wiktionary's Ethiopic transliteration scheme (no ä/ə)"
        sc = ethiopic.convert("am", t)
        return (sc, "Wiktionary's own Ethiopic transliteration, inverted") if sc else (None, "not convertible")
    return None, "no safe converter for this language yet"

from tr2script import arabic, mandaic
import semitic_phon
LOOKUP = {"arc", "tmr", "jpa", "syc", "aii", "tru", "he", "hbo", "ar"} | ETHIOPIC
ABJAD_TABLE = {"arc": "arc", "tmr": "tmr", "jpa": "jpa", "he": "he", "hbo": "hbo", "syc": "syc", "aii": "syc", "tru": "syc"}
LONG = {"ī": ["y", ""], "ē": ["y", ""], "ū": ["w", ""], "ō": ["w", ""], "ā": [""], "ă": [""], "ĕ": [""], "ŏ": [""]}

def candidates(code, tr):
    """Possible written forms of a vocalised transliteration: long vowels with or without a mater, a final -ā as aleph or he, an initial
    vowel with aleph. Arabic: the converter's vocalised form, stripped. Ethiopic: both transliteration schemes."""
    t = U.normalize("NFC", tr.strip()).replace("'", "ʾ").replace("’", "ʾ")
    if code == "ar":
        v = arabic.convert(t)
        return {strip_harakat(v): v} if v else {}
    if code in ETHIOPIC:
        out = {}
        for prof in ("am", "gez"):
            c = ethiopic.convert(prof, t) if prof == "gez" else ethiopic.convert(code if code in ethiopic.PROFILES else "am", t)
            if c: out[c] = c
        return out
    if code not in ABJAD_TABLE or re.search(r"[-\s]", t):
        return {}
    forms = [""]
    s = t
    if s and s[0] in "aeiouāēīōūə":
        s = "ʾ" + s
    for i, ch in enumerate(s):
        last = i == len(s) - 1
        if ch in "āa" and last:
            opts = ["ʾ", "h"]
        elif ch in LONG:
            opts = LONG[ch]
        elif ch in "aeiouəɛɔ":
            opts = [""]
        else:
            opts = [ch]
        forms = [f + o for f in forms for o in opts][:64]
    out = {}
    for f in forms:
        f = re.sub(r"(.)\1", r"\1", f)                                   # gemination is not written
        c = abjad.convert(ABJAD_TABLE[code], f)
        if c:
            out[c] = c
    return out

def strip_harakat(s):
    return "".join(ch for ch in U.normalize("NFC", s) if not (0x64B <= ord(ch) <= 0x652 or ord(ch) in (0x670, 0x640)))

def rewrite(template, name, new_term):
    """The template with its term filled in: an empty or "-" term slot gets the script, or one is inserted where none was given."""
    body = template[2:-2]
    parts = body.split("|")
    ci = 1 if name in FIRST else 2
    pos_idx = [i for i, p in enumerate(parts) if i > 0 and not re.match(r"\s*[a-z0-9]+\s*=", p) or (i > 0 and re.match(r"\s*\d+\s*=", p))]
    term_slot = pos_idx[ci] if len(pos_idx) > ci else None
    if term_slot is not None and parts[term_slot].strip() in ("", "-"):
        parts[term_slot] = new_term
    else:
        at = pos_idx[ci - 1] + 1 if len(pos_idx) >= ci else len(parts)
        parts.insert(at, new_term)
    return "{{" + "|".join(parts) + "}}"

def sed_index():
    """SEDonline's cited words by Wiktionary code: [(code, form)] (the source check)."""
    import csv, wikt_draft as WD
    from paths import DATA
    out = {}
    for w in csv.DictReader(open(DATA / "sedonline" / "sedonline_words.tsv", encoding="utf-8"), delimiter="\t"):
        if w["lang"] in WD.LANG:
            out.setdefault(WD.LANG[w["lang"]][0], []).append(w["form"])
    return out

def comparanda(r):
    """The other Semitic terms on the template's own line (its cognates, ancestor or descendants), as (code, form)."""
    text = K.cached(r["page"]) or ""
    line = next((l for l in text.split("\n") if r["template"] in l), "")
    out = []
    for a, b, name, pos, named in templates(line):
        if line[a:b] == r["template"]:
            continue
        ci = 0 if name in FIRST else 1 if name in SECOND else None
        if ci is None or len(pos) <= ci or name in ("noncog", "ncog", "nc"):
            continue                                                   # not cognates by the editor's own account
        code, term = pos[ci], (pos[ci + 1] if len(pos) > ci + 1 else "")
        if code == r["code"]:
            continue                                                   # the same language: context, not a cognate (𐩡𐩬: ln, lnm beside glbm)
        form = term if term.strip() not in ("", "-") else (named.get("tr") or named.get("ts") or "")
        if form and code in semitic_phon.FAMILY:
            out.append((code, form))
    return out

def sanity(r, term, src):
    """-> (True/False/None, why). True if a source has the form (SEDonline, same language, same consonants) or the form fits the regular sound
    correspondences with the cognates on its line (semitic_phon.py; e.g. Ugaritic bgy beside Arabic بغى fails: *ġ is ġ in Ugaritic)."""
    code = r["code"]
    mine = semitic_phon.letters(code, term)
    for f in src.get(code, []):
        if semitic_phon.letters(code, f) == mine and mine:
            return True, f"in SEDonline as {f}"
    return semitic_phon.check(code, term, comparanda(r))

def page_exists(titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = api(action="query", titles="|".join(titles[i:i + 50]))
        for p in d["query"]["pages"]:
            out[U.normalize("NFC", p["title"])] = not p.get("missing")
    return out

def drop_tr(template):
    return re.sub(r"\|\s*tr\s*=[^|}]*", "", template, count=1)

def main(argv):
    langs = argv or LANGUAGES
    rows = []
    for lang in langs:
        try:
            pages = members(lang)
        except Exception as e:
            print(f"  {lang}: {e}"); continue
        codes = [c for c, v in K.LANGS.items() if v[0] == lang] or [lang]
        K.fetch(pages, refresh=True, log=lambda *a: None)
        n = 0
        for p in pages:
            text = K.cached(p) or ""
            for code in codes:
                for r in requests(text, code):
                    rows.append(dict(language=lang, code=code, page=p, **{k: v for k, v in r.items() if k not in ("start", "end")}))
                    n += 1
        print(f"{lang:28} {len(pages):4} pages, {n:4} requests found" + ("" if n or not pages else f"  (code? {codes})"))
    akk = sorted({suggest("akk", r["tr"])[0] for r in rows if r["code"] == "akk"} - {None})
    exists = page_exists(akk + [t + "m" for t in akk if t[-1:] in "aeiuāēīū"])
    src = sed_index()
    for r in rows:
        term, how = suggest(r["code"], r["tr"], r["ts"])
        if term:
            verdict, why = sanity(r, term, src)
            if verdict is None and r["code"] in LOSSLESS:
                verdict, why = True, "a lossless script (the user's call, 2026-10-31); no cognate contradicts it"
            if verdict is not True:
                term, how = None, ("fails the sanity check: " if verdict is False else "no source or cognate to check it against: ") + why
        if term and re.search(r"\|\s*(?:tr|ts|alt)\d\s*=", r["template"]):
            term, how = None, "a second term (tr2=/ts2=) in the same template: one fill would leave the request open"
        alt = None
        if term and r["code"] == "akk" and not exists.get(term) and exists.get(term + "m"):
            term, alt, how = term + "m", term, how + "; linked to Wiktionary's lemma with mimation, shown as written"
        if term and r["code"] != "ar":
            new = rewrite(r["template"], r["name"], term)
            if r["code"] in LATIN:
                new = drop_tr(new)
                new = re.sub(r"\|\s*ts\s*=\s*" + re.escape(alt or term) + r"\s*(?=[|}])", "", new, count=1)    # ts= the same as the term: redundant
                if alt:
                    new = new[:-2] + f"|alt={alt}}}}}"
            r.update(new=new, how=how)
        else:
            r.update(why=how if not term else "Arabic left for a person")
    print(f"second pass, spellings Wiktionary already has: {lookup_pass(rows)} more")
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = [r for r in rows if "new" in r]
    print(f"{len(rows)} requests; {len(ok)} with a safe script/term, {len(rows) - len(ok)} left for a person; see {OUT.relative_to(WIKT.parent.parent)}")



def page_edits(rows):
    """-> {page: [(old template, new template)]}, each distinct template once (a template repeated on a page is replaced everywhere)."""
    out = {}
    for r in rows:
        if "new" in r:
            pairs = out.setdefault(r["page"], [])
            if (r["template"], r["new"]) not in pairs:
                pairs.append((r["template"], r["new"]))
    return out

def apply_pairs(text, pairs):
    """Twin of applyReplacements() in scripts/respell_core.js: every occurrence of each old template becomes the new one.
    -> (text, number of templates found)"""
    found = 0
    for old, new in pairs:
        if old in text:
            found += 1
            text = text.replace(old, new)
    return text, found


def lookup_pass(rows):
    """Second pass for rows left for a person: a spelling that Wiktionary already has an entry for, in that language, that fits the gloss
    (or, for Arabic, whose headword is the converter's vocalised form). Exactly one candidate must qualify."""
    todo = [r for r in rows if "new" not in r and r["code"] in LOOKUP and not re.search(r"\|\s*(?:tr|ts|alt)\d\s*=", r["template"])]
    cand = {id(r): candidates(r["code"], r["tr"]) for r in todo}
    titles = sorted({t for c in cand.values() for t in c})
    K.fetch(titles, log=lambda *a: None)
    n = 0
    for r in todo:
        hits = []
        for title, voc in cand[id(r)].items():
            sec = K.language_section(K.cached(title) or "", r["code"])
            if not sec:
                continue
            gloss_ok = bool(K.words(r["gloss"]) & K.words(" ".join(K.definitions(sec)))) if r["gloss"] else False
            head_ok = r["code"] == "ar" and voc != title and voc in U.normalize("NFC", sec)
            if gloss_ok or head_ok:
                hits.append((title, "gloss" if gloss_ok else "headword"))
        if len(hits) == 1:
            title, why = hits[0]
            r.pop("why", None)
            new = rewrite(r["template"], r["name"], title)
            if r["code"] == "ar":                                  # Arabic: the vocalised headword, and no tr= (Wiktionary transliterates it; Catonif)
                voc = cand[id(r)][title]
                new = drop_tr(rewrite(r["template"], r["name"], voc))
            r.update(new=new, how=f"the spelling of the existing {r['language']} entry {title} (matched by {why})")
            n += 1
    return n

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
