"""Does a draft contradict the Wiktionary pages its descendants link to?   usage: wikt_conflicts.py [--fetch] [draft.wiki ...]

For every descendant with a term (not '-'), the Wiktionary page of that term is read (cached in build/wikt_pages/; --fetch downloads the
missing ones, in batches, patiently) and, in the section of that language:

  CONFLICT  the etymology says the word is inherited from, or derived from, a different Proto-Semitic reconstruction
  CONFLICT  the page lists another descendant of our draft as BORROWED from it ({{desc|..|bor=1}}): e.g. Akkadian `immerum` lists the
            Hebrew, Aramaic and Phoenician "lamb" words as borrowings, so a Proto-Semitic page treating them as inherited disagrees
  WARN      the etymology says the word itself is borrowed (bor / borrowed / loanword)
  WARN      none of the page's definitions shares a content word with our gloss (wrong word? different sense?)
  INFO      the page already names our reconstruction (the link will agree), or has no page / no section for that language

analyze() is pure (text in, findings out) so the tests can run it on saved pages without a network."""
import json, re, sys, time, unicodedata as U, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from paths import BUILD, ROOT
from sedonline_compare import skeleton, fold
from wikt_langs import LANGS, sections, strip_marks

UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
CACHE = BUILD / "wikt_pages"
ENT = re.compile(r"\{\{(desc|l)\|([^|{}]+)\|([^|{}]*)((?:\|[^{}]*)?)\}\}")
ALIAS = {"hbo": "he"}                 # Biblical Hebrew entries sit under Hebrew; pages use he in {{desc}}
STOP = set("a an the of to be or and in on with for by from as at is it its that this one kind some".split())

def entries(text):
    body = text[text.index("====Descendants===="):text.index("===References===")]
    out = []
    for m in ENT.finditer(body):
        params = dict(p.split("=", 1) for p in m.group(4).split("|") if "=" in p)
        out.append((m.group(2), m.group(3), params))
    return out

def term_title(code, term, params):
    """The Wiktionary page a descendant links to: the term without vowel marks (Akkadian: the lemma), or None when there is no term."""
    if not term or term == "-" or code not in LANGS:
        return None
    return strip_marks(term).strip()

# ---------------- cache / fetch ----------------
def cache_file(title):
    return CACHE / (urllib.parse.quote(title, safe="") + ".txt")

def cached(title):
    f = cache_file(title)
    return f.read_text(encoding="utf-8") if f.exists() else None

def fetch(titles, patience=600, log=print):
    """Download the pages that are not cached yet: 50 titles per request, honouring Retry-After on HTTP 429 for up to `patience` seconds
    in total, writing the cache after every batch. Returns the number of pages still missing (0 = complete)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [t for t in dict.fromkeys(titles) if cached(t) is None]
    waited = 0
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = urllib.parse.urlencode(dict(format="json", formatversion=2, action="query", prop="revisions", rvprop="content",
                                           rvslots="main", titles="|".join(batch))).encode()
        while True:
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=30))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or waited > patience:
                    log(f"  stopped: HTTP {e.code} after waiting {waited:.0f}s; run again later")
                    return sum(cached(t) is None for t in todo)
                w = min(float(e.headers.get("Retry-After") or 20), 60); log(f"  429, waiting {w:.0f}s"); time.sleep(w); waited += w
        got = {}
        for p in r["query"]["pages"]:
            got[U.normalize("NFC", p["title"])] = p["revisions"][0]["slots"]["main"]["content"] if "revisions" in p else ""
        for t in batch:
            cache_file(t).write_text(got.get(U.normalize("NFC", t), ""), encoding="utf-8")
        log(f"  fetched {min(i + 50, len(todo))}/{len(todo)}")
        time.sleep(3)
    return 0

# ---------------- analysis ----------------
def language_section(page, code):
    for name in sections(code):
        m = re.search(r"(?m)^==" + re.escape(name) + r"==\s*$", page)
        if m:
            nxt = re.search(r"(?m)^==[^=]", page[m.end():])
            return page[m.end(): m.end() + nxt.start()] if nxt else page[m.end():]
    return None

def etymology(sec):
    m = re.search(r"(?ms)^===+Etymology[^=\n]*===+\s*\n(.*?)(?=^===+(?!Etymology)|\Z)", sec)
    return m.group(1) if m else ""

def definitions(sec):
    out = []
    for line in re.findall(r"(?m)^# (.*)$", sec):
        line = re.sub(r"\{\{(?:lb|label|gloss|gl|q|qualifier|sense)\|[^}]*\}\}", "", line)
        line = re.sub(r"\{\{[^}]*\|([^|}]+)\}\}", r"\1", line)
        line = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", line)
        out.append(re.sub(r"[^\w\s]", " ", line.lower()))
    return out

def words(s):
    return {w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOP}

def ps_references(ety):
    """Proto-Semitic forms named in an etymology: {{inh|ar|sem-pro|*x}}, {{ety|ar|:inh|sem-pro:*x}}, {{der|..|sem-pro|*x}}, {{cog|sem-pro|*x}}."""
    return [re.sub(r"<[^>]*>", "", m).strip().lstrip("*") for m in re.findall(r"sem-pro[|:]\*?([^|}]+)", ety)]

def analyze(draft_text, title, pages, source=None):
    """-> [(level, term, message)] for one draft. `pages` maps a Wiktionary title to its wikitext ('' = no such page)."""
    findings = []
    ents = entries(draft_text)
    codes = {ALIAS.get(code, code) for code, _, _ in ents}
    gloss_of = {}
    for code, term, params in ents:
        t = term_title(code, term, params)
        if t is None:
            continue
        label = f"{LANGS[code][0]} {term}"
        page = pages.get(t)
        if page is None:
            findings.append(("INFO", label, f"page {t!r} not fetched")); continue
        if not page:
            findings.append(("INFO", label, "no Wiktionary page (red link)")); continue
        sec = language_section(page, code)
        if sec is None:
            findings.append(("INFO", label, f"page exists, but has no {LANGS[code][0]} section")); continue
        ety = etymology(sec)
        refs = ps_references(ety)
        # 1. inherited / derived from another Proto-Semitic form
        for ref in refs:
            if fold(ref) == fold(title):
                findings.append(("INFO", label, f"etymology already names *{ref}"))
            elif skeleton(ref) == skeleton(title):
                findings.append(("WARN", label, f"etymology names *{ref}: same consonants, other vocalisation; the page may be expected at that title"))
            elif len(skeleton(ref)) >= 2:
                findings.append(("CONFLICT", label, f"etymology names a different Proto-Semitic form: *{ref}"))
        # 2. the page calls the word borrowed
        lead = ety.strip()[:220]                          # what the etymology OPENS with: later mentions ("not borrowed from X") are not claims
        is_borrowed = bool(re.search(r"\{\{(?:bor\+?|lbor|slbor|calque|cal|pcal)\|", lead) or re.search(r":(?:bor|lbor|slbor|cal)\b", lead)
                or re.match(r"(?i)\s*(?:borrowed|a loan|loan(?:word)?)\b", lead))
        if is_borrowed:
            findings.append(("WARN", label, "etymology says the word is borrowed: " + re.sub(r"\s+", " ", ety.strip())[:110]))
        # 3. the page lists other descendants of ours as borrowed from it
        borrowed = {m.group(1) for m in re.finditer(r"\{\{desc\|([\w-]+)\|[^{}]*?\|bor=1[^{}]*\}\}", sec)}
        both = sorted((borrowed & codes) - {ALIAS.get(code, code)})
        if both:
            findings.append(("CONFLICT", label, "page lists " + ", ".join(LANGS[c][0] for c in both) + " as BORROWED from it (bor=1)"))
        # 5. a clean descendant page that does not yet cite us at all: a candidate to add {{inh|...}} to (see wikt_backlink.py)
        if not refs and not is_borrowed and not both:
            findings.append(("CANDIDATE", label, f"{t!r} does not cite *{title} yet" + ("" if ety.strip() else " (no Etymology section)")))
        # 4. gloss overlap with the page's definitions
        ours = words(params.get("t", ""))
        theirs = words(" ".join(definitions(sec)))
        if ours and theirs and not ours & theirs:
            findings.append(("WARN", label, f"no shared word: ours {params.get('t')!r}, theirs {sorted(theirs)[:6]}"))
    return findings

def check_files(files, pages=None):
    pages = pages if pages is not None else {}
    out = {}
    for f in files:
        text = Path(f).read_text(encoding="utf-8")
        title = Path(f).name[len("Proto-Semitic_"):-len(".wiki")]
        ents = entries(text)
        for code, term, params in ents:
            t = term_title(code, term, params)
            if t is not None and t not in pages:
                c = cached(t)
                if c is not None:
                    pages[t] = c
        out[Path(f).name] = analyze(text, title, pages)
    return out

def main(argv):
    drafts = ROOT / "wiktionary_drafts"
    files = [Path(a) for a in argv if not a.startswith("--")] or sorted(drafts.glob("Proto-Semitic_*.wiki")) + sorted((drafts / "done").glob("Proto-Semitic_*.wiki"))
    if "--fetch" in argv:
        want = [term_title(c, t, p) for f in files for c, t, p in entries(f.read_text(encoding="utf-8"))]
        left = fetch([w for w in want if w])
        print("pages still missing:", left)
    res = check_files(files)
    bad = 0
    for name, fs in res.items():
        print(f"\n== {name}")
        for lvl in ("CONFLICT", "WARN", "CANDIDATE", "INFO"):
            for l, term, msg in fs:
                if l == lvl and (lvl != "INFO" or "--info" in argv):
                    print(f"  {lvl:8} {term}: {msg}")
                    bad += lvl == "CONFLICT"
        n = {k: sum(1 for l, _, _ in fs if l == k) for k in ("CONFLICT", "WARN", "CANDIDATE", "INFO")}
        print(f"  ({n['CONFLICT']} conflict, {n['WARN']} warn, {n['CANDIDATE']} candidate, {n['INFO']} info)")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
