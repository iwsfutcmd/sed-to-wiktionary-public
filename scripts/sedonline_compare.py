"""Third-source comparison: SEDonline reconstructions vs. the printed SED tables vs. Wiktionary's PS/PWS titles.
Writes data/sedonline/sedonline_comparison.tsv (one row per SEDonline PS/PWS reconstruction) and prints a summary.
Folding is the same skeleton as wikt_match.py (ˀ→ʔ, ˁ→ʕ, ḏ/ṯ/ġ/ś variants, hyphen and * dropped); schematic V is not
expanded here, so `wikt_*` is an exact-skeleton match only. usage: sedonline_compare.py"""
import csv, json, re, unicodedata as U
from collections import Counter, defaultdict
from paths import DATA, WIKT

FOLD = [("ʾ", "ʔ"), ("ˀ", "ʔ"), ("ʿ", "ʕ"), ("ˁ", "ʕ"), ("ʻ", "ʕ"), ("ð", "ḏ"), ("θ", "ṯ"), ("ḳ", "q"), ("γ", "ġ"),
        ("ŝ", "ś"), ("ḡ", "ġ"), ("δ", "ḏ"), ("š", "š")]
def fold(s):
    s = U.normalize("NFC", s)
    for a, b in FOLD:
        s = s.replace(a, b)
    return U.normalize("NFC", s).replace("-", "").replace("*", "").strip()

def titles(name):
    d = defaultdict(list)
    for t in json.loads((WIKT / name).read_text(encoding="utf-8")):
        form = t.split("/", 1)[1]
        d[fold(form)].append(form)
    return d

def variants(form):
    """'*kal-/*kull-' / '*a, b' -> separate forms (alternatives separated by / , or)."""
    return [v for v in (fold(x) for x in re.split(r"\s*(?:/|,|;|\bor\b)\s*", form)) if v]

def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

def main():
    ips, ipw = titles("wik_ps.json"), titles("wik_pws.json")
    recs = read(DATA / "sedonline" / "sedonline_reconstructions.tsv")
    words = read(DATA / "sedonline" / "sedonline_words.tsv")
    langs = defaultdict(set)
    for w in words:
        langs[w["rec_id"]].add(w["lang"])
    sed = {}   # key '1N:5' -> SED printed form
    for r in read(DATA / "sed_vol1_vol2_reconstructions.tsv"):
        sed[f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}"] = r["protoform"]
    cited = {k for r in recs for k in r["sed_ref"].split(";") if k}

    out = []
    for r in recs:
        if r["level"] not in ("PS", "PWS"):
            continue
        vs = variants(r["form"])
        tit = lambda ix: ";".join(sorted({t for v in vs for t in ix.get(v, [])}))
        ps_t, pw_t = tit(ips), tit(ipw)
        keys = [k for k in r["sed_ref"].split(";") if k]
        out.append(dict(rec_id=r["rec_id"], level=r["level"], form=r["form"], gloss=r["gloss"], sed_ref=r["sed_ref"],
                        sed_form=";".join(sed.get(k, "") for k in keys),
                        n_words=r["n_words"], n_langs=len(langs[r["rec_id"]]),
                        wikt_ps="yes" if ps_t else "no", wikt_ps_title=ps_t,
                        wikt_pws="yes" if pw_t else "no", wikt_pws_title=pw_t))
    out.sort(key=lambda d: (d["wikt_ps"] == "yes" or d["wikt_pws"] == "yes", -d["n_langs"]))
    with open(DATA / "sedonline" / "sedonline_comparison.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(out)

    on_wik = lambda d: d["wikt_ps"] == "yes" or d["wikt_pws"] == "yes"
    for lv in ("PS", "PWS"):
        sub = [d for d in out if d["level"] == lv]
        print(f"SEDonline {lv}: {len(sub)}; on Wiktionary (PS or PWS title): {sum(on_wik(d) for d in sub)}; "
              f"with a SED I/II number: {sum(bool(d['sed_ref']) for d in sub)}")
    print("printed-SED entries (vol1+vol2):", len(sed), "| cited by some SEDonline reconstruction:", len(cited & set(sed)),
          "| not found:", len(set(sed) - cited))
    ps_pws_ref = {k for d in out for k in d["sed_ref"].split(";") if k}
    print("printed-SED entries cited by a SEDonline PS/PWS entry:", len(ps_pws_ref & set(sed)))
    print("SEDonline PS/PWS, no SED number, absent from Wikt, attested in >=5 languages:",
          sum(1 for d in out if not d["sed_ref"] and not on_wik(d) and d["n_langs"] >= 5))

if __name__ == "__main__":
    main()
