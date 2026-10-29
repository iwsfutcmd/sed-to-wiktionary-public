"""Checks for merges (wiktionary_drafts/merges/: lines added to a page that is not ours) so that nothing we add is already on the page.
usage: wikt_merge.py [FILE ...]      (network: reads the pages behind each {{desctree}})

A language can be on a page without a {{desc}} line of its own: {{desctree|tmr|עַיְנָא}} on *ʕayn- shows the whole Descendants list of the
Aramaic page עינא (Assyrian, Mandaic, Syriac, Lishana Deni, Turoyo). duplicates() reports every language we add that the page already shows,
either way. Pure functions are tested offline (tests/test_merge.py); the network part runs under ONLINE=1."""
import re, sys
from pathlib import Path
import wikt_conflicts as K
from wikt_langs import sections

DESC = re.compile(r"\{\{(desc|desctree)\|([a-z]{2,3}(?:-[a-z]{2,4})*)\|([^|}]*)([^{}]*)\}\}")

def desc_lines(text):
    """-> [(code, term, q, is_tree)] for the {{desc}}/{{desctree}} templates of a page (q: the dialect label, '' if none)."""
    out = []
    for m in DESC.finditer(text):
        q = re.search(r"\|q=([^|}]*)", m.group(4))
        out.append((m.group(2), m.group(3), q.group(1) if q else "", m.group(1) == "desctree"))
    return out

def same_page_repeats(text):
    """The same word listed twice: one language, one spelling (vowel marks aside). Two words of one language are fine (bone: Amharic አጥንት and
    the borrowed አጽም; flint: two Syriac words), and so is one spelling in several dialects, each named with q=."""
    seen, out = {}, set()
    for code, term, q, _ in desc_lines(text):
        key = (code, K.strip_marks(term).strip(), q)
        if term.strip() not in ("", "-") and key in seen:
            out.add(code)
        seen[key] = True
    return sorted(out)

PARENT = {"tmr": "arc", "jpa": "arc", "sam": "arc", "arc-cpa": "arc", "arc-old": "arc", "arc-imp": "arc", "arc-pal": "arc", "arc-nab": "arc",
          "arc-bib": "arc", "hbo": "he"}       # a {{desctree}} for a variety reads its parent's section (tmr עַיְנָא is under ==Aramaic== on עינא)

def descendants_section(page, code):
    sec = K.language_section(page or "", code) or (K.language_section(page or "", PARENT[code]) if code in PARENT else None) or ""
    m = re.search(r"(?ms)^=+\s*Descendants\s*=+\s*\n(.*?)(?=^=|\Z)", sec)
    return m.group(1) if m else ""

def tree_codes(text, get, depth=3):
    """Every language a page shows through its {{desctree}}s: the Descendants of the page behind each (get(title) -> wikitext), recursively."""
    out = set()
    if depth == 0:
        return out
    for code, term, _, tree in desc_lines(text):
        if not tree:
            continue
        title = K.strip_marks(term)
        sub = descendants_section(get(title), code)
        for c, _, _, _ in desc_lines(sub):
            out.add(c)
        out |= tree_codes(sub, get, depth - 1)
    return out

def added_codes(live, merged):
    import difflib
    new = "\n".join(l[1:] for l in difflib.unified_diff(live.split("\n"), merged.split("\n"), lineterm="", n=0) if l[:1] == "+" and l[:3] != "+++")
    return {c for c, _, _, _ in desc_lines(new)}

def duplicates(live, merged, get):
    """Languages the merge adds that the live page already shows: its own lines, or through a {{desctree}}."""
    shown = {c for c, _, _, _ in desc_lines(live)} | tree_codes(live, get)
    return sorted(added_codes(live, merged) & shown)

def main(argv):
    files = [Path(a) for a in argv] or sorted((Path(__file__).resolve().parent.parent / "wiktionary_drafts" / "merges").glob("*.wiki"))
    def get(title):
        if K.cached(title) is None:
            K.fetch([title])
        return K.cached(title) or ""
    bad = 0
    for f in files:
        title = re.sub(r"^Reconstruction:Proto-(West_)?Semitic_", lambda m: "Reconstruction:Proto-" + ("West Semitic/" if m.group(1) else "Semitic/"), "Reconstruction:" + f.stem)
        K.fetch([title], refresh=True)
        merged = f.read_text(encoding="utf-8")
        live = K.cached(title) or ""
        saved = live.rstrip() == merged.rstrip()
        rep = same_page_repeats(merged)
        dup = [] if saved else duplicates(live, merged, get)          # what we add, against the page as it stands (once saved, there is no "before")
        print(f"{f.stem} ({'saved' if saved else 'pending'}): " + ("ok" if not rep and not dup else f"SAME WORD TWICE {rep}; ADDED BUT ALREADY SHOWN {dup}"))
        bad += bool(rep or dup)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
