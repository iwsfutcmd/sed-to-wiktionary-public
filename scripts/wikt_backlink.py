"""Draft the {{inh|...}} to add to a daughter page that doesn't cite us yet, for a person to paste in by hand.

  python wikt_backlink.py plan             find CANDIDATE daughter pages (via wikt_conflicts.analyze) across every draft, using the
                                            Wiktionary pages cached at build/wikt_pages/ (python wikt_conflicts.py --fetch to fill it)
  python wikt_backlink.py show [PAGE ...]  print the suggested insertion for one or more candidate pages (default: all)

This never edits Wiktionary. For each candidate it proposes one template, {{inh|code|sem-pro|*title}} (or sem-wes-pro on a
Proto-West Semitic draft), and where to put it: appended to an existing Etymology section that doesn't yet mention us, or a
new Etymology section placed right after the language header, when the page's section has none. Wording the sentence around
the template, and actually adding it, stays a person's job -- see the CANDIDATE condition in wikt_conflicts.analyze()."""
import csv, json, sys
from pathlib import Path
from paths import ROOT, WIKT
import wikt_conflicts as K

OUT = WIKT / "backlink_candidates.tsv"
PREFIXES = {"Proto-Semitic_": "PS", "Proto-West_Semitic_": "PWS"}

def draft_title_level(path):
    pfx = next(p for p in PREFIXES if path.name.startswith(p))
    return path.name[len(pfx):-len(".wiki")], PREFIXES[pfx]

def inh_template(code, level, title):
    tpl_lang = "sem-wes-pro" if level == "PWS" else "sem-pro"
    return f"{{{{inh|{code}|{tpl_lang}|*{title}}}}}"

def suggestion(page, code, level, title):
    """-> dict(mode: create | append, insert, full, current).  `insert` is the bare template; `full` is the whole
    Etymology body to paste in, ready to use as-is; `current` is the existing Etymology (append mode only), shown
    so a person can see what `full` is replacing. Append mode follows the convention already used on the live
    pages that do cite us (kišādum, nīākum, pānum, marāṣum): 'From {{inh|...}}. <existing sentence(s)>'."""
    sec = K.language_section(page, code)
    ety = K.etymology(sec)
    tpl = inh_template(code, level, title)
    if not ety.strip():
        full = f"===Etymology===\n{tpl}.\n\n"
        return dict(mode="create", insert=tpl, full=full)
    current = ety.strip()
    full = f"From {tpl}. {current}"
    return dict(mode="append", insert=tpl, current=current, full=full)

def candidates_for(draft_text, title, pages):
    """-> [dict(code, term, page, mode, insert, current)] for the entries of one draft that wikt_conflicts.analyze() flags CANDIDATE."""
    findings = K.analyze(draft_text, title, pages)
    cand_labels = {term for lvl, term, _ in findings if lvl == "CANDIDATE"}
    out = []
    for code, term, params in K.entries(draft_text):
        if f"{K.LANGS[code][0]} {term}" not in cand_labels:
            continue
        t = K.term_title(code, term, params)
        out.append(dict(code=code, term=term, page=t))
    return out

def draft_files():
    drafts = ROOT / "wiktionary_drafts"
    return sorted(p for pfx in PREFIXES for p in drafts.glob(f"{pfx}*.wiki")) + \
           sorted(p for pfx in PREFIXES for p in (drafts / "done").glob(f"{pfx}*.wiki"))

def plan():
    files = draft_files()
    rows = []
    for f in files:
        title, level = draft_title_level(f)
        text = f.read_text(encoding="utf-8")
        pages = {}
        for code, term, params in K.entries(text):
            t = K.term_title(code, term, params)
            if t is not None:
                c = K.cached(t)
                if c is not None:
                    pages[t] = c
        for c in candidates_for(text, title, pages):
            s = suggestion(pages[c["page"]], c["code"], level, title)
            rows.append(dict(draft=f.name, level=level, title=title, code=c["code"], lang=K.LANGS[c["code"]][0],
                              term=c["term"], page=c["page"], mode=s["mode"], insert=s["insert"], full=s["full"], current=s.get("current", "")))
    WIKT.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["draft", "level", "title", "code", "lang", "term", "page", "mode", "insert", "full", "current"])
        for r in rows:
            w.writerow([r[k] for k in ("draft", "level", "title", "code", "lang", "term", "page", "mode", "insert", "full", "current")])
    created = sum(r["mode"] == "create" for r in rows)
    print(f"{len(rows)} candidate(s) across {len({r['draft'] for r in rows})} draft(s): {created} need a new Etymology section, {len(rows) - created} append to an existing one")
    print(f"see {OUT.relative_to(ROOT)}; diffs: show")
    return rows

def show(argv):
    if not OUT.exists():
        raise SystemExit("run `plan` first")
    with open(OUT, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        if argv and r["page"] not in argv:
            continue
        print(f"\n== {r['page']}  ({r['lang']}, cites *{r['title']} from {r['draft']})")
        if r["mode"] == "create":
            print("  no Etymology section -- paste this right after the language header:")
        else:
            print("  existing Etymology (does not mention us yet) -- replace it with:")
        print("  " + r["full"].replace("\n", "\n  "))

def main(argv):
    if not argv or argv[0] not in ("plan", "show"):
        print(__doc__); return 2
    if argv[0] == "plan":
        plan()
    else:
        show(argv[1:])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
