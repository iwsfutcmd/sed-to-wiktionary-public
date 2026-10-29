"""Which existing Wiktionary reconstruction pages could the SED fill out?   usage: wikt_enrich.py [--refresh]

For every SED entry that already has a page (data/sed_wiktionary_gaps.tsv status "covered", not one of ours), the page's descendant languages
are compared with the languages of the SEDonline record of the same entry (same consonants once diacritics are stripped, a gloss word in common,
as wikt_match.py pairs them). The SED languages missing from the page, and whether the page cites the SED, are written to
  data/wiktionary/enrich_candidates.tsv      sorted by the number of missing languages: the first rows gain the most.
Language codes are compared at the level Wiktionary trees use: Biblical Hebrew = Hebrew, the Aramaic varieties = Aramaic (see ALIAS).
A page that names a language only in prose, or hides it under {{desctree}}, counts it as present: the scan errs towards "nothing to add"."""
import csv, re, sys, unicodedata as U
from collections import defaultdict
from paths import DATA, WIKT
import wikt_conflicts as K
import wikt_draft as WD

OUT = WIKT / "enrich_candidates.tsv"
ALIAS = {**K.ALIAS, "jpa": "arc", "tmr": "arc", "sam": "arc", "arc-cpa": "arc"}     # Jewish/Samaritan/CPA Aramaic are often listed as plain Aramaic
SEMITIC_CODES = {c for c, _, _ in WD.LANG.values()}

def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

def bare(f):
    f = re.sub(r"\([^()]*\)", "", K.fold(f) if hasattr(K, "fold") else f)
    f = "".join(c for c in U.normalize("NFD", f) if not U.combining(c))
    return re.sub(r"[aiueoāīūēōV/,\-*\s]", "", f)

def gwords(g):
    return set(re.findall(r"[a-z]{3,}", g.lower())) - {"the", "and", "kind", "with"}

def alternatives(form):
    out = set()
    for part in form.split(","):
        out |= {re.sub(r"(\S)/(\S)", lambda m: m.group(i), part) for i in (1, 2)}
    return {bare(a) for a in out}

def norm(code):
    return ALIAS.get(code, code)

def page_langs(text):
    """Language codes of the descendants listed on a reconstruction page: every {{desc}}/{{desctree}}, and links in its Descendants sections."""
    codes = {norm(c) for c in re.findall(r"\{\{(?:desc|desctree|desc\+)\|([a-z]{2,3}(?:-[a-z]{2,4})*)\|", text)}    # anywhere: lišān- lists them
    for m in re.finditer(r"(?ms)^=+\s*Descendants\s*=+\s*\n(.*?)(?=^=+\s*(?!Descendants)[^=\n]+=+\s*$|\Z)", text):
        for c in re.findall(r"\{\{(?:desc|desctree|desc\+|l|m|l-self|cog)\|([a-z]{2,3}(?:-[a-z]{2,4})*)\|", m.group(1)):
            codes.add(norm(c))
    return codes

def main(argv):
    gaps = read(DATA / "sed_wiktionary_gaps.tsv")
    recs = {(r["vol"], r["section"], r["no"]): r for r in read(DATA / "sed_vol1_vol2_reconstructions.tsv")}
    site = defaultdict(list)
    for r in read(DATA / "sedonline" / "sedonline_reconstructions.tsv"):
        if r.get("sed_ref"):
            site[r["sed_ref"]].append(r)
    words = defaultdict(list)
    for w in read(DATA / "sedonline" / "sedonline_words.tsv"):
        words[w["rec_id"]].append(w)
    rows = []
    for g in gaps:
        if g["status"] != "covered" or g.get("ours"):
            continue
        r = recs[(g["vol"], g["section"], g["no"])]
        key = f"{g['vol']}{g['section'][0].upper()}:{g['no']}"
        rec = [s for s in site.get(key, []) if bare(s["norm"]) in alternatives(r["protoform"]) and gwords(s["gloss"]) & gwords(r["gloss"])] or \
              [s for s in site.get(key, []) if gwords(s["gloss"]) & gwords(r["gloss"])]
        titles = [("Reconstruction:Proto-Semitic/" + t) for t in r["wikt_ps_title"].split(";") if t] + \
                 [("Reconstruction:Proto-West Semitic/" + t) for t in r["wikt_pws_title"].split(";") if t]
        rows.append(dict(key=key, protoform=r["protoform"], gloss=r["gloss"], match="exact" if "yes" in (r["wikt_ps"], r["wikt_pws"]) else "pattern",
                         titles=titles, rec=rec[0]["rec_id"] if rec else ""))
    K.fetch([t for x in rows for t in x["titles"]], refresh="--refresh" in argv)
    def target(t):                                          # old spellings are redirects (ʾid- -> ʔid-): count the page they point to, once
        text = K.cached(t) or ""
        m = re.match(r"(?i)\s*#REDIRECT\s*\[\[([^\]|#]+)", text)
        return m.group(1).strip() if m else t
    for _ in range(2):
        K.fetch([target(t) for x in rows for t in x["titles"]], refresh=False)
    for x in rows:
        x["titles"] = list(dict.fromkeys(target(t) for t in x["titles"]))
    out = []
    for x in rows:
        sed = {}
        for w in words.get(x["rec"], []):
            if w["lang"] in WD.LANG:
                sed.setdefault(norm(WD.LANG[w["lang"]][0]), w["lang"])
        for t in x["titles"]:
            text = K.cached(t) or ""
            if not text or re.match(r"(?i)\s*#REDIRECT", text):
                continue
            have = page_langs(text)
            missing = sorted({c for c in sed if c not in have}, key=lambda c: K.LANGS.get(c, (c,))[0])
            out.append(dict(key=x["key"], protoform=x["protoform"], gloss=x["gloss"], title=t.split(":", 1)[1], match=x["match"], rec=x["rec"],
                            page_langs=len(have), sed_langs=len(sed), n_missing=len(missing),
                            missing=", ".join(K.LANGS.get(c, (c,))[0] for c in missing),
                            cites_sed="yes" if re.search(r"R:sem-pro:SED|Militarev|(?<!Hamito-)Semitic Etymological Dictionary|(?<![A-Z])SED\b", text) else "no"))
    out.sort(key=lambda d: (-d["n_missing"], d["key"]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(out)
    print(f"{len(out)} existing page(s) checked; {sum(d['n_missing'] >= 5 for d in out)} would gain 5+ SED languages; "
          f"{sum(d['cites_sed'] == 'no' for d in out)} do not cite the SED; see {OUT.relative_to(WIKT.parent.parent)}")
    return out

if __name__ == "__main__":
    main(sys.argv[1:])
