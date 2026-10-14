"""Parse the cached SEDonline pages (build/sedonline/rec/*.html, see sedonline_fetch.py) into

  data/sedonline/sedonline_reconstructions.tsv   one row per reconstruction
  data/sedonline/sedonline_words.tsv             one row per cited word (join: rec_id)

Unlike the PDFs' text layer, these forms are real Unicode (ˀ ˁ š ṣ́ ḏ ṯ ...), but SEDonline uses its own
transcription: glottals are ˀ/ˁ (U+02C0/U+02C1), not ʔ/ʕ, so `norm` folds those, plus the usual variants,
to the same skeleton `wikt_match.py` uses. usage: sedonline_parse.py"""
import csv, re, sys
from bs4 import BeautifulSoup
from paths import BUILD, DATA

SRC = BUILD / "sedonline" / "rec"
OUT = DATA / "sedonline"

def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).replace(" ,", ",").strip() if el else ""

def split_title(h):
    """'*ˀab- - father' -> ('*ˀab-', 'father'); the first ' - ' separates form from gloss."""
    form, _, gloss = h.partition(" - ")
    return form.strip(), gloss.strip()

def panels(root):
    """Yield (lang, id, form, gloss, ref, note) for each .panel under root (a words/reconstructions block)."""
    for p in root.select("div.panel"):
        head = p.select_one(".panel-heading")
        lab = head.select_one("span.label")
        a = head.select_one("span.h3 a[href]")
        if not a:
            continue
        line = head.select_one("span.h3:has(a)")
        small = line.find("small")
        ref = txt(small).strip("()") if small else ""
        if small:
            small.extract()
        form, gloss = split_title(txt(line))
        body = p.select_one(".panel-body")
        yield (txt(lab), a["href"].rstrip("/").rsplit("/", 1)[-1], form, gloss, ref, txt(body))

def norm(form):
    """Fold SEDonline's transcription to the project's: ˀ→ʔ, ˁ→ʕ, drop the leading * and trailing/leading hyphen noise."""
    f = form.lstrip("*").strip()
    return f.replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ʾ", "ʔ").replace("ʿ", "ʕ")

SUB = str.maketrans({"ᵥ": "v", "ᴠ": "v", "ₙ": "n"})
def sed_keys(ref):
    """'SED II Nos. 131, 139' -> '2N:131;2N:139'; 'SED I 46ᵥ' -> '1V:46' (same vol/section/no keys as the
    reconstruction tables: N nominal, V verbal; Vol. 2 is all nominal). A bare 'SED No. 179' names no volume: skipped."""
    out = []
    for m in re.finditer(r"SED\s+(II|I)\b\s*(?:Nos?\.|№)?\s*((?:\d+\s*[ᵥᴠ]?\s*(?:,|and|&|;)?\s*)+)", ref):
        vol = 2 if m.group(1) == "II" else 1
        for n, v in re.findall(r"(\d+)\s*([ᵥᴠ]?)", m.group(2)):
            out.append(f"{vol}{'V' if v else 'N'}:{n}")
    return ";".join(dict.fromkeys(out))

def parse(path):
    s = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    h1 = s.select_one("h1")
    if not h1:
        return None
    rid = path.stem
    level = txt(s.select_one("div.h1 span.label")) or "?"
    small = h1.find("small")
    ref = txt(small).strip("()") if small else ""
    if small:
        small.extract()
    form, gloss = split_title(txt(h1))
    # free-text note: the first row after the header that holds plain text and no panels
    note = ""
    for row in s.select("div.col-md-12 > div.row > div.col-md-12"):
        if not row.find(["div", "a", "button"]) and txt(row):
            note = txt(row)
            break
    sed_ref = sed_keys(ref)
    rel = {}
    for key in ("reconstruction", "reconstructions"):
        blk = s.find(id=key)
        rel[key] = [(lang, i, f, g) for lang, i, f, g, _, _ in panels(blk)] if blk else []
    words = []
    blk = s.find(id="reconstruction_words")
    if blk:
        words = [(rid, wid, lang, f, g, r, n) for lang, wid, f, g, r, n in panels(blk)]
    rec = dict(rec_id=rid, level=level, form=form, norm=norm(form), gloss=gloss, ref=ref, sed_ref=sed_ref, note=note,
               parents=";".join(f"{l}:{i}" for l, i, _, _ in rel["reconstruction"]),
               children=";".join(f"{l}:{i}" for l, i, _, _ in rel["reconstructions"]), n_words=len(words))
    return rec, words

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs, words, bad = [], [], []
    for p in sorted(SRC.glob("*.html"), key=lambda p: int(p.stem)):
        r = parse(p)
        if r is None:
            bad.append(p.stem)
            continue
        recs.append(r[0]); words += r[1]
    cols = list(recs[0])
    with open(OUT / "sedonline_reconstructions.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(recs)
    with open(OUT / "sedonline_words.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rec_id", "word_id", "lang", "form", "gloss", "ref", "note"]); w.writerows(words)
    print(len(recs), "reconstructions,", len(words), "words; unparsable pages:", bad[:10], len(bad))

if __name__ == "__main__":
    main()
