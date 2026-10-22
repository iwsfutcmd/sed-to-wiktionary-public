"""Survey: pages that link to a hyphenated root (ʔ-b-d) where a bare verb page (ʔbd) exists or was meant.   usage: wikt_root_verb.py [survey]

Bare and hyphenated are different entries on the live wiki (data/wiktionary/root_vs_verb.md): bare = the attested verb, hyphenated = the abstract root.
The 2026-10-19 sweep turned some bare references into hyphenated ones, so a daughter page can point at a root page that does not exist
(a red link) or at the root when it meant the verb.  This lists every reference to a hyphenated root whose bare sibling is a Wiktionary page,
with a guess at which was meant, into data/wiktionary/root_verb_links.tsv (and build/orth_fixes/root_verb.json for the checklist)."""
import json, re, sys, time, unicodedata as U
from paths import BUILD, WIKT
from wikt_fix_refs import Api, fix_text, nfc
from wikt_orthography import PFX, rootify

OUT = BUILD / "orth_fixes"

class Collect:
    """a mapping for fix_text() that records every (level, term) it is asked about and rewrites nothing"""
    def __init__(self): self.seen = []
    def get(self, key, default=None):
        self.seen.append(key); return default

def titles_under(api, prefix):
    out, cont = [], {}
    while True:
        r = api.call(action="query", list="allpages", apnamespace=118, apprefix=prefix, aplimit=500, **cont)
        out += [nfc(p["title"]) for p in r["query"]["allpages"]]
        if "continue" not in r: return out
        cont = {"apcontinue": r["continue"]["apcontinue"]}; time.sleep(1)

def is_root_title(stem):
    """ʔ-b-d: 2-5 consonant letters joined by hyphens, none at the end"""
    parts = stem.split("-")
    return 2 <= len(parts) <= 5 and all(p in CONS for p in parts)
CONS = set(rootify.__globals__["CONSONANTS"])

def survey(log=print):
    api = Api(); rows = []
    for level, pfx in PFX.items():
        name = pfx[len("Reconstruction:"):]
        have = {t[len(pfx):] for t in titles_under(api, name)}
        bare = {s for s in have if "-" not in s and rootify(s) != s}        # bare consonant-only verbs: ʔbd
        roots = {s for s in have if is_root_title(s)}
        pairs = {}                                                           # root title -> bare title (either may be a red link, but the bare one must exist)
        for b in bare: pairs[rootify(b)] = b
        log(f"{level}: {len(have)} pages, {len(bare)} bare, {len(roots)} hyphenated roots, {len(pairs)} bare pages to check")
        bare_pages = api.pages([pfx + b for b in bare])
        head = {b: (re.search(r"\{\{head\|sem(?:-wes)?-pro\|(\w+)", bare_pages.get(pfx + b, (0, 0, ""))[2]) or [None, "?"])[1] for b in bare}
        linking = {}
        roots_to_check = list(pairs)
        for i in range(0, len(roots_to_check), 40):
            batch = roots_to_check[i:i + 40]
            r = api.call(action="query", prop="linkshere", titles="|".join(pfx + x for x in batch), lhlimit="max", lhprop="title")
            for p in r["query"]["pages"]:
                for l in p.get("linkshere", []):
                    linking.setdefault(nfc(p["title"])[len(pfx):], []).append(nfc(l["title"]))
            time.sleep(1)
        exists_root = {x: x in roots for x in pairs}
        pagetexts = api.pages(sorted({t for ls in linking.values() for t in ls if not t.startswith("User")}))
        for root, ls in sorted(linking.items()):
            b = pairs[root]
            for page in sorted(set(ls)):
                txt = pagetexts.get(page, (0, 0, ""))[2]
                col = Collect(); fix_text(txt, col)
                if (level, nfc(root)) not in [(l, nfc(t)) for l, t in col.seen]: continue      # a plain link, not a term of a sem-pro reference
                for ln in txt.split("\n"):
                    if root not in ln: continue
                    gloss = re.search(r"(?:\||<)t[:=]\s*(related to|forming words)[^|}>]*", ln, re.I)       # a root's gloss ("related to destruction"), not a verb's ("to weigh")
                    why = "root" if gloss else "check" if re.search(r"\broot\b", ln) else "verb"
                    rows.append(dict(level=level, root=root, bare=b, bare_head=head[b], root_page_exists="yes" if exists_root[root] else "red", page=page, guess=why, line=ln.strip()[:260]))
    return rows

def main(argv):
    rows = survey()
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["level", "root", "bare", "bare_head", "root_page_exists", "page", "guess", "line"]
    (WIKT / "root_verb_links.tsv").write_text("\t".join(cols) + "\n" + "\n".join("\t".join(r[c] for c in cols) for r in rows) + "\n", encoding="utf-8")
    (OUT / "root_verb.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(len(rows), "references;", dict(Counter((r["root_page_exists"], r["guess"]) for r in rows)))
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
