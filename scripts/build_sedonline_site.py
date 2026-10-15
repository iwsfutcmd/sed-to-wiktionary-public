"""Fill site/sedonline_template.html with the SEDonline tables -> site/sedonline.html (self-contained browser page).
Needs data/sedonline/*.tsv (make sedonline). Wiktionary matching reuses sedonline_compare (exact skeleton, PS/PWS only).
usage: build_sedonline_site.py"""
import csv, json
from collections import defaultdict
from paths import DATA, SITE
from sedonline_compare import fold, titles, variants, read

PFX = {"PS": "Reconstruction:Proto-Semitic/", "PWS": "Reconstruction:Proto-West Semitic/"}

def main():
    recs = read(DATA / "sedonline" / "sedonline_reconstructions.tsv")
    words = read(DATA / "sedonline" / "sedonline_words.tsv")
    sed = {f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}": r["protoform"]
           for r in read(DATA / "sed_vol1_vol2_reconstructions.tsv")}
    ix = {"PS": titles("wik_ps.json"), "PWS": titles("wik_pws.json")}

    langs, lid = [], {}
    by = defaultdict(list)
    for w in words:
        if w["lang"] not in lid:
            lid[w["lang"]] = len(langs); langs.append(w["lang"])
        by[w["rec_id"]].append([lid[w["lang"]], w["form"], w["gloss"], w["ref"], w["note"], int(w["word_id"])])

    out = []
    for r in recs:
        keys = [k for k in r["sed_ref"].split(";") if k]
        wikt = {}
        for lv in ("PS", "PWS"):
            t = sorted({x for v in variants(r["form"]) for x in ix[lv].get(v, [])})
            if t:
                wikt[lv] = t
        out.append(dict(id=int(r["rec_id"]), lv=r["level"], f=r["form"], g=r["gloss"], ref=r["ref"], n=r["note"],
                        sed=[[k, sed.get(k, "")] for k in keys],
                        up=[p.rsplit(":", 1) for p in r["parents"].split(";") if p],
                        dn=[p.rsplit(":", 1) for p in r["children"].split(";") if p],
                        wk=wikt, w=by[r["rec_id"]]))
    blob = json.dumps(dict(langs=langs, recs=out, pfx=PFX, snapshot="2026-10-14"), ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")
    html = (SITE / "sedonline_template.html").read_text(encoding="utf-8").replace("__DATA__", blob)
    (SITE / "sedonline.html").write_text(html, encoding="utf-8")
    print(f"site/sedonline.html: {len(html) / 1e6:.2f} MB, {len(out)} reconstructions, {len(words)} words")

if __name__ == "__main__":
    main()
