"""Which printed SED reconstructions (Vols. 1-2) does SEDonline lack? -> data/sedonline/sed_print_vs_site.tsv
status: `cited`      a SEDonline reconstruction cites the entry by number (sed_ref);
        `matched`    no number, but a SEDonline reconstruction has the same consonant skeleton and a shared gloss word;
        `not_found`  neither: check by hand. `candidates` lists the closest SEDonline reconstructions as id:why, where why is
                     `cites` / `form+gloss` / `gloss` (shared gloss word, ranked by skeleton similarity).
Heuristic: the skeleton drops vowels, V, length/schwa marks and optional (...) parts; it does not model root variants. usage: sedonline_missing.py"""
import csv, re
from difflib import SequenceMatcher
from sedonline_compare import fold, read
from paths import DATA

STOP = set("a an the of to be or and kind with in on part have has had".split())
gloss_words = lambda g: {w for w in re.findall(r"[a-z]+", g.lower()) if w not in STOP and len(w) > 2}
def skel(p):
    s = fold(re.sub(r"\([^)]*\)|[/]|\bor\b|,.*", "", p.replace("ʷ", ""))).replace("ŝ", "ś")
    return re.sub("[aiuāīūēōVV̄̂ₓ̣́-]", "", s)

def main():
    sed = read(DATA / "sed_vol1_vol2_reconstructions.tsv")
    recs = read(DATA / "sedonline" / "sedonline_reconstructions.tsv")
    cited = {}
    for r in recs:
        for k in r["sed_ref"].split(";"):
            if k:
                cited.setdefault(k, []).append(r["rec_id"])
    R = [(r, skel(r["form"].split(",")[0]), gloss_words(r["gloss"])) for r in recs]
    out = []
    for s in sed:
        key = f"{s['vol']}{'V' if s['section'] == 'verbal' else 'N'}:{s['no']}"
        ls, g = skel(s["protoform"]), gloss_words(s["gloss"])
        if key in cited:
            status, cands = "cited", [f"{i}:cites" for i in cited[key]]
        else:
            exact = [r["rec_id"] for r, l, gg in R if l and l == ls and g & gg]
            if exact:
                status, cands = "matched", [f"{i}:form+gloss" for i in exact]
            else:
                scored = sorted(((len(g & gg), SequenceMatcher(None, ls, l).ratio(), r["rec_id"]) for r, l, gg in R if g & gg),
                                reverse=True)
                scored = sorted(scored, key=lambda t: (-t[1], -t[0]))[:6]
                status, cands = "not_found", [f"{i}:gloss" for _, _, i in scored]
        out.append(dict(key=key, vol=s["vol"], section=s["section"], no=s["no"], protoform=s["protoform"], gloss=s["gloss"],
                        pdf_page=s["pdf_page"], status=status, candidates=";".join(cands)))
    with open(DATA / "sedonline" / "sed_print_vs_site.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print(Counter(o["status"] for o in out))

if __name__ == "__main__":
    main()
