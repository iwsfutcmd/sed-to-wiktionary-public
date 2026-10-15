"""Which Proto-Semitic pages does Wiktionary already link to but not have, that the SED can fill in?   usage: wikt_wanted.py [--ps-only]

Special:WantedPages is capped at 5,000 results (down to 55 links), so no Semitic reconstruction appears in it. Instead, for every SED entry
without a matching Wiktionary page, plausible titles are generated and asked about in batches of 50 (prop=linkshere, which also works for
pages that do not exist):
  nominals   the stem with optional (-at) and a/u alternations expanded, in Wiktionary's mixed spellings (ḳ/q, ṯ̣/θ̣/ṱ, ṯ/θ, ḏ/δ)
  verbs      the root, and the vocalised perfect stems CaCaC- CaCiC- CaCuC- (Wiktionary titles verbs by stem: pataḥ-, našaḳ-)
A title that is missing and has incoming links is a *wanted* page. Results are cached in build/wanted_scan.json (resumable); output:
  data/wiktionary/wanted_semitic.tsv         title, number of linking pages, some of them, matching SED entry
Patient with the API: honours Retry-After, 3 s between batches."""
import csv, itertools, json, re, sys, time, unicodedata as U, urllib.error, urllib.parse, urllib.request
from paths import BUILD, DATA, WIKT
from sedonline_compare import read, fold

UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
PFX = {"PS": "Reconstruction:Proto-Semitic/", "PWS": "Reconstruction:Proto-West Semitic/"}
SCAN = BUILD / "wanted_scan.json"

# SED notation -> the Wiktionary spelling(s) that occur in titles
BASE = [("ŝ", "ś"), ("ṣ̂", "ṣ́"), ("ˀ", "ʔ"), ("ˁ", "ʕ"), ("γ", "ġ")]
CHOICES = [("ḳ", "q"), ("ṯ̣", "θ̣"), ("ṯ", "θ"), ("ḏ", "δ"), ("ṣ́", "ṣ̂"), ("ś", "ŝ")]    # each may appear either way in titles or links
VOWELS = "aiuāīūēō"

def base(s):
    s = U.normalize("NFC", s)
    for a, b in BASE:
        s = s.replace(U.normalize("NFC", a), b)
    return s.replace("ŝ", "ś")

def spellings(form, cap=48):
    out = {U.normalize("NFC", form)}
    out |= {re.sub(r"([^-]+)-at-$", r"\1(at-)", form)} - {form}                  # Wiktionary links feminine stems as ṯ̣aby(at-)
    for a, b in CHOICES:
        out |= {x.replace(a, b) for x in out if a in x}
        if len(out) > cap:
            break
    return sorted(out)

def expand(proto):
    """'*ʕaṯm(-at)-, *ʕVrw(-at)-' -> stems; '(-at)' and other (...) are optional, 'a/u' alternates."""
    forms = []
    for f in re.split(r"\s*(?:,|//|\bor\b)\s*", proto):
        f = f.strip().lstrip("*").strip()
        if f:
            forms.append(f)
    out = []
    for f in forms:
        vs = [f]
        for _ in range(3):
            nv = []
            for v in vs:
                m = re.search(r"\(([^()]*)\)", v)
                if m and m.group(1) != "V":
                    nv += [v[:m.start()] + v[m.end():], v[:m.start()] + m.group(1) + v[m.end():]]
                else:
                    nv.append(v)
            vs = nv
        vs2 = []
        for v in vs:
            m = re.search(r"(.)/(.)", v)
            vs2 += [v[:m.start()] + m.group(1) + v[m.end():], v[:m.start()] + m.group(2) + v[m.end():]] if m else [v]
        out += [x.replace("(V)", "V") for x in vs2]
    return list(dict.fromkeys(x for x in out if x))

def radicals(root):
    letters = []
    for ch in U.normalize("NFD", root):
        if U.combining(ch) and letters:
            letters[-1] += ch
        else:
            letters.append(ch)
    return [U.normalize("NFC", l) for l in letters]

def candidates(proto, verbal):
    out = []
    for f in expand(proto):
        f = base(f)
        if verbal:
            rad = radicals(f.rstrip("-"))
            if len(rad) == 3:
                c1, c2, c3 = rad
                out += [f.rstrip("-"), f.rstrip("-") + "-"] + [f"{c1}a{c2}{v}{c3}-" for v in "aiu"]
            else:
                out += [f]
        else:
            out.append(f)
    return list(dict.fromkeys(s for f in out for s in spellings(f)))

# ---------------- scan ----------------
def scan(titles, patience=900, log=print):
    """titles -> {title: [linking pages]} (cached). Missing pages with links are the wanted ones."""
    cache = json.loads(SCAN.read_text(encoding="utf-8")) if SCAN.exists() else {}
    todo = [t for t in dict.fromkeys(titles) if t not in cache]
    waited = 0
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = urllib.parse.urlencode(dict(format="json", formatversion=2, action="query", prop="linkshere", lhprop="title", lhlimit=500,
                                           lhnamespace="0|118", titles="|".join(batch))).encode()
        while True:
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=30))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or waited > patience:
                    log(f"  stopped: HTTP {e.code} after {waited:.0f}s; run again to resume"); SCAN.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                    return cache
                w = min(float(e.headers.get("Retry-After") or 20), 60); log(f"  429, waiting {w:.0f}s"); time.sleep(w); waited += w
        by = {U.normalize("NFC", p["title"]): p for p in r["query"]["pages"]}
        for t in batch:
            p = by.get(U.normalize("NFC", t))
            cache[t] = None if p is None else ({"missing": bool(p.get("missing")), "links": [l["title"] for l in p.get("linkshere", [])]})
        SCAN.parent.mkdir(exist_ok=True); SCAN.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        log(f"  scanned {min(i + 50, len(todo))}/{len(todo)}")
        time.sleep(3)
    return cache

def main(argv):
    gaps = {(r["vol"], r["section"], r["no"]): r for r in read(DATA / "sed_wiktionary_gaps.tsv")}
    sed = read(DATA / "sed_vol1_vol2_reconstructions.tsv")
    agree = {r["key"]: r for r in read(DATA / "sedonline" / "sed_print_vs_site_agreement.tsv")}
    want = []                                           # (title, key, protoform, gloss)
    for r in sed:
        g = gaps[(r["vol"], r["section"], r["no"])]
        if g["status"] == "covered":
            continue
        key = f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}"
        for c in candidates(r["protoform"], r["section"] == "verbal"):
            for lvl in (["PS"] if "--ps-only" in argv else ["PS", "PWS"]):
                want.append((PFX[lvl] + c, key, r["protoform"], r["gloss"]))
    titles = [w[0] for w in want]
    print(len(titles), "candidate titles for", len({w[1] for w in want}), "SED entries")
    cache = scan(titles)
    rows = {}
    for title, key, proto, gloss in want:
        c = cache.get(title)
        if c and c["missing"] and c["links"]:
            rows.setdefault(title, dict(title=title, n_links=len(c["links"]), linked_from="; ".join(c["links"][:8]), sed_key=key,
                                        protoform=proto, gloss=gloss, agree=agree.get(key, {}).get("agree", "")))
    out = sorted(rows.values(), key=lambda d: -d["n_links"])
    with open(WIKT / "wanted_semitic.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["title", "n_links", "linked_from", "sed_key", "protoform", "gloss", "agree"], delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(out)
    print(len(out), "wanted pages (missing, with incoming links) match a SED entry; data/wiktionary/wanted_semitic.tsv")
    for d in out[:25]:
        print(f"  {d['n_links']:3} {d['title'].replace('Reconstruction:', ''):42} {d['sed_key']:7} {d['protoform'][:22]:22} {d['gloss'][:28]}")

if __name__ == "__main__":
    main(sys.argv[1:])
