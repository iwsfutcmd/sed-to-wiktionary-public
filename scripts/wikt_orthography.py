"""Survey of the Proto-Semitic / Proto-West Semitic pages against Wiktionary:Proto-Semitic entry guidelines (WT:ASEM).   usage: wikt_orthography.py [--scan]

The guidelines' notation (NFC):  consonants  p t ṭ k ḳ ʔ  b d g  ṯ s š ś ḫ ḥ h  ṯ̣ ṣ ṣ́  ḏ z ḡ ʕ  r w y l m n   vowels  a i u ā ī ū  V V̄
Entry names are the root/stem followed by a hyphen.  Anything else is a variant: q ʾ ʿ θ θ̣ ṱ ð ṣ̂ ŝ ɣ ġ ḍ ...

For every existing title: is it standard? if not, what would the standard title be, does that title already exist (merge) or not (move), and which
pages link to it. For every standard title: do pages link to a NON-standard spelling of it (a red link, or a page that should become a redirect)?
Results of --scan (Wiktionary API, 50 titles per request, patient) are cached in build/wanted_scan.json (shared with wikt_wanted.py);
output: data/wiktionary/orthography_survey.tsv and data/wiktionary/orthography_survey.md."""
import csv, json, re, sys, unicodedata as U
from collections import defaultdict
from paths import DATA, WIKT, BUILD
from wikt_wanted import scan, SCAN

PFX = {"PS": "Reconstruction:Proto-Semitic/", "PWS": "Reconstruction:Proto-West Semitic/"}
STD = {U.normalize("NFC", g) for g in "p t ṭ k ḳ ʔ b d g ṯ s š ś ḫ ḥ h ṯ̣ ṣ ṣ́ ḏ z ḡ ʕ r w y l m n a i u ā ī ū V V̄ - ( ) ".split()}
# variant -> standard (longest first); each entry names the kind of deviation
VARIANTS = [("θ̣", "ṯ̣"), ("ṱ", "ṯ̣"), ("θ", "ṯ"), ("ð", "ḏ"), ("δ", "ḏ"), ("ṣ̂", "ṣ́"), ("ŝ", "ś"), ("ɣ", "ḡ"), ("ġ", "ḡ"), ("γ", "ḡ"),
            ("q", "ḳ"), ("ʾ", "ʔ"), ("ˀ", "ʔ"), ("ʼ", "ʔ"), ("ʿ", "ʕ"), ("ˁ", "ʕ"), ("ʻ", "ʕ"), ("ḍ", "ṣ́")]
MANUAL = {"x̣": "ḫ with emphasis?", "č": "ṯ? (Russian/Leslau č)"}        # letters with no safe automatic reading

def graphemes(s):
    out = []
    for ch in U.normalize("NFC", s):
        if U.combining(ch) and out:
            out[-1] += ch
        else:
            out.append(ch)
    return [U.normalize("NFC", g) for g in out]

def standardise(stem):
    """-> (standard stem, [deviations], manual?)"""
    s = U.normalize("NFC", stem); dev = []
    for a, b in VARIANTS:
        a, b = U.normalize("NFC", a), U.normalize("NFC", b)
        if a in s:
            dev.append(f"{a}→{b}"); s = s.replace(a, b)
    s = U.normalize("NFC", s)
    manual = [g for g in graphemes(s) if g not in STD]
    return s, dev, manual

def inverse_variants(stem, cap=8):
    """Non-standard spellings that people may link to: each family alone and all together."""
    fams = [("ḳ", "q"), ("ṯ̣", "θ̣"), ("ṯ̣", "ṱ"), ("ṯ", "θ"), ("ḏ", "ð"), ("ṣ́", "ṣ̂"), ("ś", "ŝ"), ("ḡ", "ġ"), ("ʔ", "ʾ"), ("ʕ", "ʿ")]
    s = U.normalize("NFC", stem); out = []
    def sub(x, a, b):
        a = U.normalize("NFC", a)
        if a == "ṯ" and "ṯ̣" in x:                      # do not turn the ṯ of ṯ̣ into θ + dot twice
            return x
        return x.replace(a, b)
    present = [(a, b) for a, b in fams if U.normalize("NFC", a) in s]
    for a, b in present:
        out.append(sub(s, a, b))
    allv = s
    for a, b in present:
        if b not in ("ṱ",):
            allv = sub(allv, a, b)
    out.append(allv)
    return [U.normalize("NFC", o) for o in dict.fromkeys(out) if o != s][:cap]

PAGES = BUILD / "ortho_pages.json"
def fetch_pages(titles, patience=900, log=print, keep=None):
    """Wikitext of the given titles (50 per request) -> build/ortho_pages.json {NFC title: text or null}."""
    import time, urllib.error, urllib.parse, urllib.request
    from wikt_wanted import UA
    pages, waited = dict(keep or {}), 0
    todo = [t for t in dict.fromkeys(U.normalize("NFC", t) for t in titles) if t not in pages]
    for i in range(0, len(todo), 40):
        data = urllib.parse.urlencode(dict(format="json", formatversion=2, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(todo[i:i + 40]))).encode()
        while True:
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=60)); break
            except urllib.error.HTTPError as e:
                if e.code != 429 or waited > patience:
                    raise
                w = min(float(e.headers.get("Retry-After") or 20), 60); log(f"  429, waiting {w:.0f}s"); time.sleep(w); waited += w
        for p in r["query"]["pages"]:
            pages[U.normalize("NFC", p["title"])] = p["revisions"][0]["slots"]["main"]["content"] if "revisions" in p else None
        time.sleep(3)
    PAGES.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")

def page_info(pages, title):
    """-> ('page'|'redirect'|'absent', redirect destination)"""
    c = pages.get(U.normalize("NFC", title))
    if c is None:
        return "absent", None
    m = re.match(r"\s*#REDIRECT\s*\[\[([^\]|#]+)", c, re.I)
    return ("redirect", U.normalize("NFC", m.group(1)).strip()) if m else ("page", None)

def load_titles():
    ps = json.loads((WIKT / "wik_ps.json").read_text(encoding="utf-8"))
    pw = json.loads((WIKT / "wik_pws.json").read_text(encoding="utf-8"))
    return [("PS", t.split("/", 1)[1]) for t in ps] + [("PWS", t.split("/", 1)[1]) for t in pw]

def main(argv):
    titles = load_titles()
    have = {(lv, U.normalize("NFC", st)) for lv, st in titles}
    probe = []
    for lv, st in titles:
        std, dev, man = standardise(st)
        if not dev and not man:
            probe += [PFX[lv] + v for v in inverse_variants(st)]
        else:
            probe.append(PFX[lv] + st); probe.append(PFX[lv] + std)
    if "--scan" in argv:
        if "--fresh" in argv and SCAN.exists():                       # forget earlier answers for these titles: pages are created and moved all the time
            c = json.loads(SCAN.read_text(encoding="utf-8"))
            for t in probe:
                c.pop(t, None)
            SCAN.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        scan(list(dict.fromkeys(probe)))
    if "--scan" in argv or "--pages" in argv:
        want = [PFX[lv] + st for lv, st in titles if standardise(st)[1] or standardise(st)[2]] + [PFX[lv] + standardise(st)[0] for lv, st in titles if standardise(st)[1]]
        fetch_pages(want)
        have_p = json.loads(PAGES.read_text(encoding="utf-8"))
        dests = [page_info(have_p, t)[1] for t in want]                       # where the redirects lead
        fetch_pages(want + [d for d in dests if d], keep=have_p)
    cache = json.loads(SCAN.read_text(encoding="utf-8")) if SCAN.exists() else {}
    pages = json.loads(PAGES.read_text(encoding="utf-8")) if PAGES.exists() else {}
    def linkers(title):
        c = cache.get(U.normalize("NFC", title))
        return [] if c is None else c["links"]
    rows = []
    for lv, st in titles:
        std, dev, man = standardise(st)
        full, tgt = PFX[lv] + U.normalize("NFC", st), PFX[lv] + std
        kind, dest = page_info(pages, full)
        ok = not dev and not man
        if man:
            action = "MANUAL"
        elif ok:
            action = "OK"
        elif kind == "redirect":
            dk, _ = page_info(pages, dest) if dest else ("absent", None)
            dd = dest.split("/", 1)[1] if dest and "/" in dest else dest
            action = "redirect ok" if dest and not standardise(dd)[1] and not standardise(dd)[2] and dk == "page" else "FIX REDIRECT"
        else:
            tk, tdest = page_info(pages, tgt)
            action = "MOVE" if tk == "absent" else ("MOVE OVER REDIRECT" if tk == "redirect" and tdest == full else "MERGE")
        inc = [l for l in linkers(full) if l != full]
        rows.append(dict(level=lv, title=st, action=action, kind=kind, redirect_to=(dest or "").replace(PFX[lv], ""), standard=std if not ok else "",
                         deviations=" ".join(dev + [f"?{m}" for m in man]), n_links=len(inc), linked_from="; ".join(inc[:8]),
                         no_hyphen="yes" if not st.endswith("-") and not st.startswith("-") else ""))
    # references to non-standard spellings of standard titles
    refs = []
    for lv, st in titles:
        std, dev, man = standardise(st)
        if dev or man:
            continue
        for v in inverse_variants(st):
            c = cache.get(PFX[lv] + v)
            if c and c["links"]:
                kind, dest = page_info(pages, PFX[lv] + v)
                refs.append(dict(level=lv, variant=v, standard=st, exists="no" if c["missing"] else "yes", n_links=len(c["links"]), linked_from="; ".join(c["links"][:8])))
    # every page that links to a non-standard spelling: the pages whose references would be edited
    with open(WIKT / "orthography_links.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["level", "nonstandard_title", "standard_title", "linking_page"])
        seen = set()
        for lv, st in titles:
            std, dev, man = standardise(st)
            cands = [(st, std)] if dev else [(v, st) for v in inverse_variants(st)]
            for bad, good in cands:
                for l in sorted(set(linkers(PFX[lv] + bad)) - {PFX[lv] + bad}):
                    if not (l.startswith("Reconstruction:") and standardise(l.split("/", 1)[1])[1]):       # a redirect's own nonstandard siblings are not references
                        if (lv, bad, l) not in seen:
                            seen.add((lv, bad, l)); w.writerow([lv, bad, good if not man else "", l])
    cols = ["level", "title", "action", "kind", "redirect_to", "standard", "deviations", "n_links", "linked_from", "no_hyphen"]
    with open(WIKT / "orthography_survey.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(rows)
    with open(WIKT / "orthography_refs.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["level", "variant", "standard", "exists", "n_links", "linked_from"], delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(refs)
    n = defaultdict(int)
    for r in rows:
        n[r["action"]] += 1
    print(dict(n), "| references to non-standard spellings of standard titles:", len(refs), "(red links:", sum(r["exists"] == "no" for r in refs), ")")
    return rows, refs

if __name__ == "__main__":
    main(sys.argv[1:])
