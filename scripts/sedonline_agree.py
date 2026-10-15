"""Where do the printed SED and SEDonline agree? -> data/sedonline/sed_print_vs_site_agreement.tsv
For each printed entry cited by a SEDonline reconstruction: `form_same` / `gloss_same` (after folding; dot-below ignored because
the print table dropped some), and `core_langs_print` / `core_langs_web` over a core of unambiguous languages (Akk, Ebl, Ugr, Hbr,
Pho, Arb, Sab, Gez, Tgr, Tna, Amh, Har, Mhr, Jib, Hrs, Soq, Syr, Mnd, JewAram); `agree` only if all three match and SEDonline files it as PS (the printed volumes reconstruct Proto-Semitic; the site also has PWS/PCS levels).
Strict by design: OCR rows missing from the print reflex table also show as differences. usage: sedonline_agree.py"""
import csv, re, collections, unicodedata as U
from sedonline_compare import read
from paths import DATA

PRINT = {"Akk.": "Akk", "Ebl.": "Ebl", "Ugr.": "Ugr", "Hbr.": "Hbr", "pB.": "Hbr", "Pho.": "Pho", "Arb.": "Arb", "Sab.": "Sab",
         "Gez.": "Gez", "Tgr.": "Tgr", "Tna.": "Tna", "Amh.": "Amh", "Har.": "Har", "Mhr.": "Mhr", "Jib.": "Jib", "Hrs.": "Hrs",
         "Soq.": "Soq", "Syr.": "Syr", "Mnd.": "Mnd", "Jud.": "JewAram"}
WEB = {"Akkadian": "Akk", "Ebla": "Ebl", "Ugaritic": "Ugr", "Hebrew": "Hbr", "Phoenician": "Pho", "Arabic": "Arb", "Sabaic": "Sab",
       "Geez": "Gez", "Tigre": "Tgr", "Tigrinya": "Tna", "Amharic": "Amh", "Harari": "Har", "Mehri": "Mhr", "Jibbali": "Jib",
       "Harsusi": "Hrs", "Soqotri": "Soq", "Syriac": "Syr", "Mandaic": "Mnd",
       "Jewish Palestinian Aramaic": "JewAram", "Jewish Babylonian Aramaic": "JewAram"}

def nform(s):
    s = U.normalize("NFD", s).replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ʾ", "ʔ").replace("ʿ", "ʕ").replace("̣", "")
    return U.normalize("NFC", re.sub(r"[\s*]", "", s)).lower()
ngloss = lambda g: re.sub(r"[^a-z]+", " ", g.lower()).strip()

def main():
    pv = read(DATA / "sedonline" / "sed_print_vs_site.tsv")
    rec = {r["rec_id"]: r for r in read(DATA / "sedonline" / "sedonline_reconstructions.tsv")}
    sed = {f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}": r for r in read(DATA / "sed_vol1_vol2_reconstructions.tsv")}
    web = collections.defaultdict(set)
    for w in read(DATA / "sedonline" / "sedonline_words.tsv"):
        if w["lang"] in WEB:
            web[w["rec_id"]].add(WEB[w["lang"]])
    prn = collections.defaultdict(set)
    for r in read(DATA / "sed_vol1_vol2_reflexes.tsv"):
        if "cf" in r["flags"]:
            continue
        key = f"{r['vol']}{'V' if r['section'] == 'verbal' else 'N'}:{r['no']}"
        for tok in r["lang"].split():
            if tok in PRINT:
                prn[key].add(PRINT[tok])
    out = []
    for p in pv:
        if p["status"] != "cited":
            continue
        s = sed[p["key"]]
        best = None
        for c in [c.split(":")[0] for c in p["candidates"].split(";")]:
            r = rec[c]
            fs = nform(r["form"].replace(", ", ",")) == nform(s["protoform"].replace(", ", ","))
            gs = ngloss(r["gloss"]) == ngloss(s["gloss"])
            if best is None or (fs and gs):
                best = (c, r, fs, gs)
        c, r, fs, gs = best
        pl, wl = prn[p["key"]], web[c]
        out.append(dict(key=p["key"], protoform=s["protoform"], gloss=s["gloss"], rec_id=c, web_form=r["form"], web_gloss=r["gloss"], web_level=r["level"],
                        form_same=int(fs), gloss_same=int(gs), core_langs_print=" ".join(sorted(pl)), core_langs_web=" ".join(sorted(wl)),
                        langs_only_print=" ".join(sorted(pl - wl)), langs_only_web=" ".join(sorted(wl - pl)),
                        agree=int(fs and gs and pl == wl and r["level"] == "PS")))
    with open(DATA / "sedonline" / "sed_print_vs_site_agreement.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(out)
    print(len(out), "cited entries;", "form+gloss same:", sum(o["form_same"] and o["gloss_same"] for o in out),
          "; fully agree (also core languages and level PS):", sum(o["agree"] for o in out))

if __name__ == "__main__":
    main()
