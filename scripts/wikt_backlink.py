"""Draft the {{inh|...}} to add to a daughter page that doesn't cite us yet, for a person to paste in by hand.

  python wikt_backlink.py plan             find CANDIDATE daughter pages (via wikt_conflicts.analyze) across every draft, using the
                                            Wiktionary pages cached at build/wikt_pages/ (python wikt_conflicts.py --fetch to fill it)
  python wikt_backlink.py show [PAGE ...]  print the suggested insertion for one or more candidate pages (default: all)
  python wikt_backlink.py pages            re-download every candidate page and write the whole edited page for each one that is safe
                                            to change mechanically (data/wiktionary/backlink_pages.json); the rest are listed with the reason

This never edits Wiktionary. For each candidate it proposes one template, {{inh|code|sem-pro|*title}} (or sem-wes-pro on a
Proto-West Semitic draft), and where to put it: appended to an existing Etymology section that doesn't yet mention us, or a
new Etymology section placed right after the language header, when the page's section has none. Wording the sentence around
the template, and actually adding it, stays a person's job -- see the CANDIDATE condition in wikt_conflicts.analyze()."""
import csv, json, re, sys
from pathlib import Path
from paths import ROOT, WIKT
import wikt_conflicts as K

OUT = WIKT / "backlink_candidates.tsv"
PAGES_OUT = WIKT / "backlink_pages.json"
# later stages of a language the draft also cites: they inherit through it, so the Proto-Semitic link belongs on the ancestor's page
LATER_STAGE = {"aii": "Aramaic / Classical Syriac", "tru": "Aramaic / Classical Syriac", "lhs": "Aramaic", "amw": "Aramaic"}
OPENS_WITH_A_SOURCE = re.compile(r"(?i)\s*(?:from|borrowed|a loan|loan|unknown|uncertain|perhaps|possibly|probably|ultimately|via|through)\b")
# A person's verdict on a page the rules could not settle, keyed (page, code): ("leave", why) takes it off the list,
# ("section", heading) writes the edit into that Etymology section of a page that has several.
DECISIONS = {
    ("כר", "hbo"): ("leave", "no entry on the page is our word (its כַּר is 'cushion, pillow')"),
    ("ሓረሰ", "ti"): ("leave", "'to plough' is too far from our sense"),
    ("ܒܥܝܪܐ", "aii"): ("leave", "a later stage: it inherits through Aramaic, as it should"),
    ("בעיר", "hbo"): ("leave", "already good as it is"),
    ("ܒܩܐ", "tru"): ("leave", "leads back to Aramaic: no need to go all the way to Proto-Semitic"),
    ("فجر", "ar"): ("leave", "fine as it is"),
    ("שאר", "hbo"): ("leave", "fine as it is"),
    ("خرس", "ar"): ("leave", "none of its etymologies is our word"),
    ("ܒܩܐ", "syc"): ("section", "Etymology 1"),
    ("ضرط", "ar"): ("section", "Etymology 1.1"),
    ("ܥܠܩܬܐ", "syc"): ("section", "Etymology 1"),
    ("علق", "ar"): ("leave", "the leech noun shares Etymology 5 with the verbal noun of عَلِقَ 'to hang'; the singulative عَلَقَة carries the link"),
    # ("replace", [(old, new), ...]): wording a person chose, applied to that language's section. علقة: the uncited "{{der|ar|syc}} ... or ... ?" becomes
    # a comparison, as the SED (II 32) gives Arabic as inherited and notes no Aramaism (see memory: SED over uncited Wiktionary)
    ("פרש", "hbo"): ("section", "Etymology 1"),
    ("ܦܪܫܐ", "syc"): ("section", "Etymology 1"),
    ("𐩰𐩧𐩪", "xsa"): ("leave", "a state form of 𐩰𐩧𐩪𐩣: the link goes on that lemma (EXTRA)"),
    # فرس: the horse noun is Etymology 2, an {{etymon}} tree that shows no text: the step goes in the tree and as a sentence, as on شحم.
    # Needs our page's {{desc|ar|فَرَس|id=horse}} saved first: otherwise the module calls the link to فرس ambiguous (three etymons there)
    ("فرس", "ar"): ("replace", [("{{etymon|ar|id=horse}}\nCognate with", "{{etymon|ar|id=horse|:inh|sem-wes-pro:*paraš-}}\n{{inh+|ar|sem-wes-pro|*paraš-}}. Cognate with")]),
    ("علقة", "ar"): ("replace", [("{{ety|ar|id=leech}}", "{{ety|ar|id=leech|:inh|sem-pro:*ʕalaḳ-}}"),
                                 ("Compare {{cog|he|עֲלוּקָה|tr='aluká}}; {{cog|ar|علق}} (various verbs); {{der|ar|syc|ܥܰܠܘܽܩܳܐ|tr=ˁallūq, ˁallūqā}} or "
                                  "{{cog|tmr|עַלקָא|tr=ˁelləqā, ˁellaqṯā}}, or {{cog|akk||tr=ilku, ilḳitu}}?",
                                  "{{inh+|ar|sem-pro|*ʕalaḳ-}}. Compare {{cog|he|עֲלוּקָה|tr='aluká}}; {{cog|ar|علق}} (various verbs); {{cog|syc|ܥܰܠܘܽܩܳܐ|tr=ˁallūq, ˁallūqā}}, "
                                  "{{cog|tmr|עַלקָא|tr=ˁelləqā, ˁellaqṯā}}, {{cog|akk||tr=ilku, ilḳitu}}.")]),
}
# Shown on a card before its button: an order to keep, or something to check
NOTES = {("فرس", "ar"): "Save the paraš- re-save on the worklist (1b) FIRST: until our page names this etymology (id=horse), "
                        "Wiktionary calls the link to فرس ambiguous. Then Show changes here should show no red error text."}

# Pages the scan cannot find by itself, named by a person: a lemma our page does not link (only one of its forms), or a page whose
# Etymology 1 is another word, so the conflict check never lists it. Each is edited by its DECISIONS entry, or as usual if it has none.
EXTRA = [dict(page="𐩰𐩧𐩪𐩣", code="xsa", title="paraš-", level="PWS"),
         dict(page="فرس", code="ar", title="paraš-", level="PWS")]
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

def skip_reason(page, code, gloss=""):
    """Why this page must be done by a person, or None if the edit can be made mechanically."""
    sec = K.language_section(page, code)
    if sec is None:
        return "no section for the language"
    ours, theirs = K.words(gloss), set().union(*[K.words(d) for d in K.definitions(sec)] or [set()])
    if ours and theirs and not ours & theirs:                   # e.g. Hebrew כר 'cushion, pillow' is not our כַּר '(young) ram'
        return f"the page's senses share no word with ours ({gloss!r}): it may be a different word with the same spelling"
    if len(re.findall(r"(?m)^===+\s*Etymology[^=\n]*===+", sec)) > 1:
        return "several Etymology sections: which one is ours is a judgement call"
    if code in LATER_STAGE:
        return f"a later stage: it should inherit through {LATER_STAGE[code]}, so the Proto-Semitic link belongs on the ancestor's page"
    ety = K.etymology(sec).strip()
    ety_tpl = re.search(r"\{\{ety\|[^{}]*\}\}", sec)                  # an {{ety}} chain anywhere in the section is its etymology
    chain = ety_tpl.group(0) if ety_tpl else ""
    if re.search(r"\{\{(?:inh|inh\+|der|der\+|bor|bor\+|lbor)\|[\w-]+\|(?!sem-pro\||sem-wes-pro\||afa-pro\|)[\w-]+\|", ety) \
            or re.search(r":(?:inh|der|bor)\|(?!sem-pro:|sem-wes-pro:)[\w-]+:", ety + chain):
        return "the etymology already names an ancestor or source: the link belongs there, or the sentence needs rewording"
    if chain:
        return None                                             # edited inside the chain
    if OPENS_WITH_A_SOURCE.match(ety):
        return f"the etymology already opens with a source ({ety[:50]!r}…): prepending would garble it"
    return None

def edited_page(page, code, level, title, section=None):
    """The whole page with the {{inh}} added to that language's section only: 'From {{inh}}. ' before the existing etymology, or a new
    Etymology section before the first subsection (after Alternative forms, which comes first by WT:ELE)."""
    tpl = inh_template(code, level, title)
    for name in K.sections(code):
        m = re.search(r"(?m)^==" + re.escape(name) + r"==\s*$", page)
        if m:
            break
    else:
        raise ValueError("no section")
    start = m.end()
    nxt = re.search(r"(?m)^==[^=]", page[start:])
    end = start + nxt.start() if nxt else len(page)
    sec = page[start:end]
    ety_tpl = re.search(r"\{\{ety\|[^{}]*\}\}", sec)
    if ety_tpl and not section:
        # {{ety|ar|:root|...|tree=1}} draws only a tree, so the step goes in the chain AND in the prose, as Arabic ثقل has it:
        # {{inh+}} ("Inherited from Proto-Semitic *x") as its own sentence, so the existing words are not reworded.
        lang_code = "sem-wes-pro" if level == "PWS" else "sem-pro"
        new_tpl = ety_tpl.group(0)[:-2] + f"|:inh|{lang_code}:*{title}}}}}"
        sentence = f"{{{{inh+|{code}|{lang_code}|*{title}}}}}."
        after = sec[ety_tpl.end():]
        stop = re.search(r"(?m)^(?:===|\[\[|\{\{(?![a-z]+-?root\b|ar-root|cog|m\||l\||inh|der|bor))", after)    # the prose ends at the next heading or box
        prose_end = stop.start() if stop else len(after)
        prose = after[:prose_end]
        if prose.strip():
            cmp = re.search(r"(?<=[.;]\s)(?=(?:Compare|Cognate|Cf\.|See also)\b)", prose)
            if cmp:
                prose = prose[:cmp.start()] + sentence + " " + prose[cmp.start():]
            else:
                para = prose.strip("\n").split("\n\n")[0]
                i = prose.index(para) + len(para)
                prose = prose[:i] + " " + sentence + prose[i:]
        else:
            prose = "\n" + sentence + prose
        return page[:start] + sec[:ety_tpl.start()] + new_tpl + prose + after[prose_end:] + page[end:]
    head = re.escape(section) if section else r"Etymology[^=\n]*"            # `section`: that one of several Etymology sections
    em = re.search(r"(?ms)^===+\s*" + head + r"\s*===+\s*\n(.*?)(?=^===|\Z)" if section else
                   r"(?ms)^===+\s*" + head + r"===+\s*\n(.*?)(?=^===+(?!Etymology)|\Z)", sec)
    if section and not em:
        raise ValueError(f"no {section} section")
    if em and em.group(1).strip():
        body = em.group(1)
        lead = len(body) - len(body.lstrip())
        box = re.match(r"(?:\{\{[\w-]*(?:rootbox|wp|wikipedia|root)\b[^{}]*\}\}\s*\n)+", body[lead:])      # display boxes stay first
        if box:
            lead += box.end()
        new_sec = sec[:em.start(1) + lead] + f"From {tpl}. " + sec[em.start(1) + lead:]
    elif em:                                                    # empty section: right after its header line
        hl = sec.index("\n", em.start()) + 1
        new_sec = sec[:hl] + f"From {tpl}.\n\n" + sec[hl:].lstrip("\n")
    else:
        heads = list(re.finditer(r"(?m)^===[^=].*$", sec))
        at = heads[0].start() if heads else len(sec)
        if heads and re.match(r"===\s*Alternative forms", heads[0].group(0)):
            at = heads[1].start() if len(heads) > 1 else len(sec)
        new_sec = sec[:at] + f"===Etymology===\nFrom {tpl}.\n\n" + sec[at:]
    return page[:start] + new_sec + page[end:]

def replaced(page, code, pairs):
    """The page with each (old, new) applied once inside that language's section; an `old` that is not there exactly once is an error (the page changed)."""
    for name in K.sections(code):
        m = re.search(r"(?m)^==" + re.escape(name) + r"==\s*$", page)
        if m:
            break
    else:
        raise ValueError("no section")
    nxt = re.search(r"(?m)^==[^=]", page[m.end():])
    end = m.end() + nxt.start() if nxt else len(page)
    sec = page[m.end():end]
    for old, new in pairs:
        if sec.count(old) != 1:
            raise ValueError(f"not found exactly once: {old[:40]!r}")
        sec = sec.replace(old, new)
    return page[:m.end()] + sec + page[end:]

def merge_same_page(items):
    """One card per page: an edit built on an earlier one of the same page (see pages()) replaces it, with both languages, its diff against the
    live text, and every note. Saving two cards of one page from the live text would undo the first."""
    import difflib
    out, at = [], {}
    for x in items:
        if "full" in x and x["page"] in at:
            prev = out[at[x["page"]]]
            live = K.cached(x["page"]) or ""
            x = dict(x, lang=prev["lang"] + ", " + x["lang"], code=prev["code"] + "," + x["code"],
                     diff=[l for l in difflib.unified_diff(live.split("\n"), x["full"].split("\n"), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")])
            out[at[x["page"]]] = x
            continue
        if "full" in x:
            at[x["page"]] = len(out)
        out.append(x)
    return out

def r_cites_not(x):
    """An EXTRA page still to do: it has the language and does not cite the reconstruction yet."""
    sec = K.language_section(K.cached(x["page"]) or "", x["code"])
    lang = "sem-wes-pro" if x["level"] == "PWS" else "sem-pro"          # the level counts: فرس cites Proto-Semitic *paraš- 'to separate'
    return sec is not None and not re.search(r"(?<![\w:-])" + lang + r"[|:]\*" + re.escape(x["title"]) + r"[|}<]", sec)

def gloss_of(row):
    if not row.get("draft"):
        return ""
    text = (ROOT / "wiktionary_drafts" / "done" / row["draft"]) if (ROOT / "wiktionary_drafts" / "done" / row["draft"]).exists() else ROOT / "wiktionary_drafts" / row["draft"]
    for code, term, params in K.entries(text.read_text(encoding="utf-8")):
        if code == row["code"] and term == row["term"]:
            return params.get("t", "")
    return ""

def summary(level, title):
    lang = "Proto-West Semitic" if level == "PWS" else "Proto-Semitic"
    return f"Etymology: inherited from {lang} *{title} ([[Reconstruction:{lang}/{title}]], after Militarev & Kogan's SED)"

def pages(refresh=True):
    """Re-download every candidate page, then write the edited page for the safe ones and the reason for the rest."""
    rows = plan()
    extra = [dict(x, lang=K.LANGS[x["code"]][0], term=x["page"], draft=None) for x in EXTRA]
    titles = sorted({r["page"] for r in rows + extra})
    if refresh and titles:
        K.fetch(titles, refresh=True)
    out, edited = [], {}                                        # edited: page -> its text with the edits so far (two languages of one page, as Ge'ez and Tigrinya ፈረስ)
    for r in plan() + [x for x in extra if r_cites_not(x)]:     # again, on the fresh text: a page fixed meanwhile drops out
        page = edited.get(r["page"]) or K.cached(r["page"]) or ""
        verdict, arg = DECISIONS.get((r["page"], r["code"]), (None, None))
        if verdict == "leave":
            out.append(dict(page=r["page"], lang=r["lang"], code=r["code"], term=r["term"], title=r["title"], level=r["level"], left=arg))
            continue
        why = None if verdict in ("section", "replace") else skip_reason(page, r["code"])                     # structural: a person has to write the edit
        unsure = None if why or verdict else skip_reason(page, r["code"], gloss_of(r))     # senses differ: the edit is ready, a person confirms it is the same word
        item = dict(page=r["page"], lang=r["lang"], code=r["code"], term=r["term"], title=r["title"], level=r["level"], gloss=gloss_of(r))
        if why:
            item["skip"] = why
        else:
            if unsure:
                sec = K.language_section(page, r["code"]) or ""
                item.update(confirm=unsure, their_senses=[re.sub(r"\s+", " ", d).strip() for d in re.findall(r"(?m)^# (.*)$", sec)][:6])
            new = replaced(page, r["code"], arg) if verdict == "replace" else edited_page(page, r["code"], r["level"], r["title"], section=arg if verdict == "section" else None)
            if verdict == "section":
                item["section"] = arg
            if verdict == "replace" and any("{{der|" in o for o, _ in arg):
                item["reworded"] = True
            if (r["page"], r["code"]) in NOTES:
                item["note"] = NOTES[(r["page"], r["code"])]
            item.update(full=new, summary=summary(r["level"], r["title"]) + ("; borrowing claim without a source made a comparison (the SED notes none)" if verdict == "replace" and any("{{der|" in o for o, _ in arg) else ""),
                        diff=[l for l in __import__("difflib").unified_diff(page.split("\n"), new.split("\n"), lineterm="", n=0)
                              if l[:1] in "+-" and l[:3] not in ("+++", "---")])
        if "full" in item:
            edited[r["page"]] = item["full"]
        out.append(item)
    out = merge_same_page(out)
    PAGES_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum("full" in x and "confirm" not in x for x in out); c = sum("confirm" in x for x in out); l = sum("left" in x for x in out)
    print(f"{n} page(s) ready to edit, {c} ready once a person confirms the sense, {l} left as decided, {len(out) - n - c - l} need a person; see {PAGES_OUT.relative_to(ROOT)}")
    return out

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
    if not argv or argv[0] not in ("plan", "show", "pages"):
        print(__doc__); return 2
    if argv[0] == "plan":
        plan()
    elif argv[0] == "pages":
        pages()
    else:
        show(argv[1:])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
