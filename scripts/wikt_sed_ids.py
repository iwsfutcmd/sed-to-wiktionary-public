"""Find {{R:sem-pro:SED}} references on Wiktionary that do not link to SEDonline (no id=, no e=) and work out the record each one means.
usage: wikt_sed_ids.py        (network) -> data/wiktionary/sed_ref_ids.json

The record comes from what the reference says: volume and entry number ("Nr. 133", "No. 72") give the SED key (2N:133), else the title of the
reconstruction page it is on (matched as in wikt_match.py). The SEDonline record of that key must be the same entry: same letters with
diacritics stripped, or a gloss word in common with the printed entry (wikt_enrich.py: SEDonline's sed_ref is not unique). Anything that does not
resolve to exactly one record is left for a person."""
import csv, json, re, sys, urllib.parse, urllib.request
from collections import defaultdict
from paths import DATA, WIKT
import wikt_conflicts as K
from wikt_enrich import bare, alternatives, gwords

OUT = WIKT / "sed_ref_ids.json"
UA = K.UA
REF = re.compile(r"\{\{R:sem-pro:SED(\|[^{}]*)?\}\}")

def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

def users():
    titles, cont = [], {}
    while True:
        q = dict(action="query", format="json", formatversion=2, list="embeddedin", eititle="Template:R:sem-pro:SED", eilimit=500, **cont)
        d = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php?" + urllib.parse.urlencode(q), headers=UA)))
        titles += [p["title"] for p in d["query"]["embeddedin"]]
        if "continue" not in d:
            return titles
        cont = d["continue"]

def needs_id(ref):
    return not re.search(r"\|\s*(id|e)\s*=\s*\S", ref)

def keys_from_ref(ref):
    vol = re.search(r"\|\s*volume\s*=\s*(I{1,2}|[12])\b", ref)
    num = re.search(r"(?:Nr|No|nr|no)\.?\s*(\d+)", ref)
    if not (vol and num):
        return []
    v = {"I": "1", "II": "2"}.get(vol.group(1), vol.group(1))
    return [f"{v}N:{num.group(1)}"] + ([f"{v}V:{num.group(1)}"] if v == "1" else [])

def fits_page(title, text, rec):
    """The record must be the page's word: a reconstruction page's title has its letters; any other entry shares a gloss word with it
    (ḥargil- 'locust' cites Nr. 103 = *γVb(b)- 'dung'; ʔanp- 'nose' cites II No. 8, a predatory mammal)."""
    m = re.match(r"Reconstruction:Proto-(?:West )?Semitic/(.+)$", title)
    if m:
        return bare(m.group(1)) in alternatives(rec["norm"]) or bare(m.group(1)) in alternatives(rec["form"])
    return bool(gwords(rec["gloss"]) & gwords(" ".join(K.definitions(text))))

def add_sed_id(text, rec, entry=""):
    """Twin of addSedId() in scripts/respell_core.js: the first {{R:sem-pro:SED}} without id=/e= gets id= (and entry= if it has none)."""
    for m in REF.finditer(text):
        args = m.group(1) or ""
        if re.search(r"\|\s*(?:id|e)\s*=\s*\S", args):
            continue
        add = f"|id={rec}" + (f"|entry={entry}" if entry and not re.search(r"\|\s*entry\s*=", args) else "")
        return text[:m.start()] + "{{R:sem-pro:SED" + args + add + "}}" + text[m.end():], True
    return text, False

def main(argv):
    recs = read(DATA / "sed_vol1_vol2_reconstructions.tsv")
    by_key = {f"{r['vol']}{r['section'][0].upper()}:{r['no']}": r for r in recs}
    by_title = defaultdict(list)
    for r in recs:
        for lvl, col in (("Proto-Semitic", "wikt_ps_title"), ("Proto-West Semitic", "wikt_pws_title")):
            for t in filter(None, r[col].split(";")):
                by_title[f"Reconstruction:{lvl}/{t}"].append(r)
    site = defaultdict(list)
    for s in read(DATA / "sedonline" / "sedonline_reconstructions.tsv"):
        if s.get("sed_ref"):
            site[s["sed_ref"]].append(s)
    titles = users()
    K.fetch(titles, refresh=True, log=lambda *a: None)
    out = []
    for t in titles:
        text = K.cached(t) or ""
        for m in REF.finditer(text):
            ref = m.group(0)
            if not needs_id(ref):
                continue
            keys = [k for k in keys_from_ref(ref) if k in by_key] or \
                   [f"{r['vol']}{r['section'][0].upper()}:{r['no']}" for r in by_title.get(t, [])]
            cands = []
            for k in dict.fromkeys(keys):
                r = by_key[k]
                cands += [(k, s) for s in site.get(k, []) if bare(s["norm"]) in alternatives(r["protoform"]) or gwords(s["gloss"]) & gwords(r["gloss"])]
            row = dict(page=t, ref=ref, keys=keys)
            if re.match(r"(?:[A-Za-z ]+ talk|Talk|Wiktionary|User|Appendix|Template):", t):
                continue                                                  # discussion and project pages: not ours to touch
            if len({s["rec_id"] for _, s in cands}) == 1 and not fits_page(t, text, cands[0][1]):
                row.update(why=f"the reference points at {cands[0][0]} {cands[0][1]['form']} '{cands[0][1]['gloss']}', which does not fit this page: the number in it may be wrong")
                out.append(row); continue
            if len({s["rec_id"] for _, s in cands}) == 1:
                k, s = cands[0]
                new = ref[:-2] + f"|id={s['rec_id']}" + ("" if re.search(r"\|\s*entry\s*=", ref) else f"|entry={s['form'].replace('ˁ', 'ʕ').replace('ˀ', 'ʔ')}") + "}}"
                row.update(rec=s["rec_id"], key=k, form=s["form"], gloss=s["gloss"], new=new)
            else:
                row.update(why="no SED entry found" if not cands else "several SEDonline records fit: " + ", ".join(sorted({s['rec_id'] for _, s in cands})))
            out.append(row)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = [r for r in out if "rec" in r]
    print(f"{len(titles)} pages use the template; {len(out)} references without an SEDonline link on {len({r['page'] for r in out})} pages; "
          f"{len(ok)} resolved to one record, {len(out) - len(ok)} left for a person; see {OUT.relative_to(WIKT.parent.parent)}")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
