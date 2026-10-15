"""Third-source comparison: SEDonline reconstructions vs. the printed SED tables vs. Wiktionary's PS/PWS titles.
Writes data/sedonline/sedonline_comparison.tsv (one row per SEDonline PS/PWS reconstruction) and prints a summary.
Folding is the same skeleton as wikt_match.py (ˀ→ʔ, ˁ→ʕ, ḏ/ṯ/ġ/ś variants, hyphen and * dropped); schematic V is not
expanded here, so `wikt_*` is `yes` (exact form after folding), `skeleton` (a page with the same consonants under another vocalisation, titles listed) or `no`. usage: sedonline_compare.py"""
import csv, json, re, unicodedata as U
from collections import Counter, defaultdict
from paths import DATA, WIKT

FOLD = [("ʾ", "ʔ"), ("ˀ", "ʔ"), ("ʿ", "ʕ"), ("ˁ", "ʕ"), ("ʻ", "ʕ"), ("ð", "ḏ"), ("θ", "ṯ"), ("ḳ", "q"), ("γ", "ġ"),
        ("ŝ", "ś"), ("ḡ", "ġ"), ("δ", "ḏ"), ("š", "š")]
def canon(s):
    """NFC, with each run of combining marks sorted, so ṯ+dot-below and dot-below+ṯ compare equal."""
    out, run = [], []
    for ch in U.normalize("NFD", s):
        if U.combining(ch):
            run.append(ch)
        else:
            out += sorted(run); run = []; out.append(ch)
    out += sorted(run)
    return U.normalize("NFC", "".join(out))

def fold(s):
    s = U.normalize("NFC", s)
    for a, b in FOLD:
        s = s.replace(a, b)
    s = s.replace("ṱ", "ṯ̣")     # U+1E71 (t + circumflex below) is the same sound as ṯ̣; Wiktionary mostly writes ṯ + dot below
    return canon(s).replace("-", "").replace("*", "").strip()

VOWELS = "aiuāīūēōeoV"
def skeleton(form):
    """Consonants only: SEDonline gives roots (*ptḥ), Wiktionary stems (pataḥ-). Optional (...) parts, vowels, V,
    length/stress marks, hyphens and spaces dropped; geminates collapsed (so *pḥḥ ~ paḥḥ-)."""
    f = U.normalize("NFD", fold(re.sub(r"\([^()]*\)", "", form)))
    f = re.sub("[" + VOWELS + r"\-/\s\u0304\u0302\u0301ₓ]", "", f)
    return re.sub(r"(.)\1", r"\1", U.normalize("NFC", f))

def titles(name):
    d = defaultdict(list)
    for t in json.loads((WIKT / name).read_text(encoding="utf-8")):
        form = t.split("/", 1)[1]
        d[fold(form)].append(form)
    return d

def skeleton_index(name):
    d = defaultdict(list)
    for t in json.loads((WIKT / name).read_text(encoding="utf-8")):
        form = t.split("/", 1)[1]
        d[skeleton(form)].append(form)
    return d

def near_titles(ix, form, exact):
    """Titles with the same consonant skeleton as any variant of `form` (>= 3 consonants), minus the exact ones."""
    sk = {skeleton(v) for v in re.split(r"\s*(?:/|,|;|\bor\b)\s*", form.lstrip("*")) if v}
    return sorted({t for k in sk if len(k) >= 3 for t in ix.get(k, [])} - set(exact))

def variants(form):
    """'*kal-/*kull-' / '*a, b' -> separate forms (alternatives separated by / , or)."""
    return [v for v in (fold(x) for x in re.split(r"\s*(?:/|,|;|\bor\b)\s*", form)) if v]

def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

def main():
    ips, ipw = titles("wik_ps.json"), titles("wik_pws.json")
    sps, spw = skeleton_index("wik_ps.json"), skeleton_index("wik_pws.json")
    recs = read(DATA / "sedonline" / "sedonline_reconstructions.tsv")
    words = read(DATA / "sedonline" / "sedonline_words.tsv")
    langs = defaultdict(set)
    for w in words:
        langs[w["rec_id"]].add(w["lang"])
    sed = {}   # key '1N:5' -> SED printed form
    for r in read(DATA / "sed_vol1_vol2_reconstructions.tsv"):
        sed[f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}"] = r["protoform"]
    cited = {k for r in recs for k in r["sed_ref"].split(";") if k}

    on_wik = lambda d: "yes" in (d["wikt_ps"], d["wikt_pws"])
    near = lambda d: not on_wik(d) and "skeleton" in (d["wikt_ps"], d["wikt_pws"])
    out = []
    for r in recs:
        if r["level"] not in ("PS", "PWS"):
            continue
        vs = variants(r["form"])
        tit = lambda ix: ";".join(sorted({t for v in vs for t in ix.get(v, [])}))
        ps_t, pw_t = tit(ips), tit(ipw)
        ps_n, pw_n = near_titles(sps, r["form"], ps_t.split(";")), near_titles(spw, r["form"], pw_t.split(";"))
        keys = [k for k in r["sed_ref"].split(";") if k]
        out.append(dict(rec_id=r["rec_id"], level=r["level"], form=r["form"], gloss=r["gloss"], sed_ref=r["sed_ref"],
                        sed_form=";".join(sed.get(k, "") for k in keys),
                        n_words=r["n_words"], n_langs=len(langs[r["rec_id"]]),
                        wikt_ps="yes" if ps_t else "skeleton" if ps_n else "no", wikt_ps_title=ps_t or ";".join(ps_n),
                        wikt_pws="yes" if pw_t else "skeleton" if pw_n else "no", wikt_pws_title=pw_t or ";".join(pw_n)))
    out.sort(key=lambda d: (on_wik(d), near(d), -d["n_langs"]))
    with open(DATA / "sedonline" / "sedonline_comparison.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(out)

    for lv in ("PS", "PWS"):
        sub = [d for d in out if d["level"] == lv]
        print(f"SEDonline {lv}: {len(sub)}; exact PS/PWS title: {sum(on_wik(d) for d in sub)}; same consonants only: {sum(near(d) for d in sub)}; "
              f"with a SED I/II number: {sum(bool(d['sed_ref']) for d in sub)}")
    print("printed-SED entries (vol1+vol2):", len(sed), "| cited by some SEDonline reconstruction:", len(cited & set(sed)),
          "| not found:", len(set(sed) - cited))
    ps_pws_ref = {k for d in out for k in d["sed_ref"].split(";") if k}
    print("printed-SED entries cited by a SEDonline PS/PWS entry:", len(ps_pws_ref & set(sed)))
    print("SEDonline PS/PWS, no SED number, no Wikt page at all (not even same consonants), attested in >=5 languages:",
          sum(1 for d in out if not d["sed_ref"] and not on_wik(d) and not near(d) and d["n_langs"] >= 5))

if __name__ == "__main__":
    main()
