"""Detect non-standard Proto-Semitic notation in references, and produce the pattern for a Wiktionary edit filter.   usage: wikt_asem_check.py [corpus.json]

WT:ASEM notation (ʔ ʕ ḳ ṯ ṯ̣ ḏ ṣ́ ś ḡ ...); the variants people type instead: ʾ ʿ ˀ ˁ q θ θ̣ ṱ ð δ ṣ̂ ŝ ɣ ġ ḍ x̣ č ...
Two detectors that must agree:
  structural(text)   reads the wikitext like a parser (the same code as wikt_fix_refs.fix_text): only the TERM of a sem-pro / sem-wes-pro reference is looked at,
                     so tr=, t=, entry= and other languages never fire.  This is the reference behaviour.
  FILTER_PCRE        one regular expression for Wiktionary's edit filter (AbuseFilter, PCRE, to be run on added_lines): the same terms, without a parser.
                     It cannot see a term inside a nested template; tests/test_asem_check.py records that limit and checks the rest against structural().
Run on a saved corpus (build/asem_corpus.json, {page: wikitext}) it reports how often each fires and where they disagree."""
import json, re, sys, unicodedata as U
from paths import BUILD
from wikt_fix_refs import fix_text, nfc, parse
from wikt_orthography import standardise, MANUAL

class StdMap:
    """A mapping for fix_text() that 'rewrites' every term to its standard spelling: the rewrites are the violations."""
    def get(self, key, default=None):
        std, dev, man = standardise(key[1])
        if any(g in MANUAL for g in man):
            return std + "⟨?⟩"                                   # a letter no rule reads (x̣, č): still a violation (other unusual letters, sₓ, ḏ̣ ..., are not judged)
        return std if dev and std != key[1] else default

def structural(text):
    """-> [(kind, bad spelling, standard spelling)] for the references in `text` whose term is not in the ASEM notation."""
    out = fix_text(text, StdMap())[1]
    x = U.normalize("NFC", text)
    for t in parse(x):                                                  # the root letters of {{sem-pro-conj/...|m|r|ṣ̂|vn=marṣ̂}}
        if x[t["args"][0][0]:t["args"][0][1]].strip().startswith("sem-pro-conj"):
            for a, b in t["args"][1:]:
                v = x[a:b]
                v = v.split("=", 1)[1] if re.match(r"\s*[\w-]+\s*=", v) else v
                std, dev, man = standardise(v.strip())
                if dev and std != v.strip():
                    out.append(("conj", v.strip(), std))
    return out

# ---- the variant characters, as code point sequences (one list feeds both the PCRE and the Python form)
BAD = [["02BE"], ["02BF"], ["02C0"], ["02C1"], ["02BC"], ["02BB"],              # ʾ ʿ ˀ ˁ ʼ ʻ  (for ʔ ʕ)
       ["0071"],                                                                # q (for ḳ)
       ["03B8"], ["00F0"], ["03B4"], ["0263"], ["03B3"], ["0121"],              # θ ð δ ɣ γ ġ  (for ṯ ḏ ḡ)
       ["1E71"], ["0074", "032D"], ["1E93"],                                    # ṱ, t + circumflex below, ẓ (for ṯ̣)
       ["1E63", "0302"], ["0073", "0323", "0302"], ["0073", "0302", "0323"],    # ṣ̂ (for ṣ́)
       ["015D"], ["0073", "0302"],                                              # ŝ (for ś)
       ["1E0D"], ["0064", "0323"],                                              # ḍ (for ṣ́)
       ["0078", "0323"], ["010D"]]                                              # x̣ č: no automatic reading, a person decides
def _alt(fmt):
    return "|".join("".join(fmt(c) for c in seq) for seq in BAD)
PCRE_BAD = _alt(lambda c: "\\x{%s}" % c)
PY_BAD = _alt(lambda c: "\\u%s" % c)

ETY = r"(?:inh\+?|der\+?|bor\+?|lbor|slbor|cal|calque|pcal|psm)"                                   # the 2nd argument names the language of the term
REF = r"(?:m\+?|l\+?|cog|noncog|ncog|desc|desctree|syn|ant|cf|cognate|mention|link|nc)"                # the 1st does
def _filter(bad):
    arg = r"[^|{}<>\n=]*?(?:" + bad + ")"
    head = r"\{\{\s*(?:" + ETY + r"\s*\|[^|{}\n]*|" + REF + r")\s*\|\s*sem-(?:wes-)?pro\s*\|"
    # the term (the next argument, an empty one skipped: {{l|sem-pro||*X}}) or a later argument written *X (an alternative form) holds a variant character
    tmpl = head + r"(?:(?:\s*\|)?\s*\*?|[^{}\n]*?\|\s*\*)" + arg
    ety = r"(?<![\w-])sem-(?:wes-)?pro:\*?[^<>|{}\s]*?(?:" + bad + ")"           # {{ety|..|sem-pro:*X}} and nested <ety:uder<sem-pro:*X>>
    link = r"\[\[Reconstruction:Proto-(?:West )?Semitic/[^\]|#\n]*?(?:" + bad + ")"
    conj = r"\{\{\s*sem-pro-conj[^{}\n]*?(?:" + bad + ")"                       # the root letters of a conjugation table
    return "(?:" + tmpl + "|" + ety + "|" + link + "|" + conj + ")"
FILTER_PCRE = _filter(PCRE_BAD)
_FILTER_PY = re.compile(_filter(PY_BAD))

def regex_hits(text):
    return [m.group(0) for m in _FILTER_PY.finditer(U.normalize("NFC", text))]

# ---- finding the pages: Wiktionary's own search (CirrusSearch regular expressions) over the whole wiki, one query per variant character
SEARCH_CHARS = ["ʾ", "ʿ", "ˀ", "ˁ", "ʼ", "ʻ", "q", "θ", "ð", "δ", "ɣ", "γ", "ġ", "ṱ", "ẓ", "ḍ", "ŝ", "ṣ̂", "ṣ̂", "x̣", "č"]      # the two ṣ̂ are NFC and the other order of the marks
def search_pages(log=print):
    """-> {page: wikitext} of every page where a sem-pro / sem-wes-pro term holds one of the variant characters (any namespace), merged into build/asem_corpus.json."""
    import time
    from wikt_fix_refs import Api
    api = Api(); found = set()
    for ch in dict.fromkeys(SEARCH_CHARS):
        for form in {U.normalize("NFC", ch), U.normalize("NFD", ch)}:
            q = "insource:/sem-(wes-)?pro[|:]\\*?[^|}<\\n]*" + form + "/"
            off = 0
            while True:
                r = api.call(action="query", list="search", srsearch=q, srnamespace="*", srlimit=50, sroffset=off)
                if "error" in r:
                    log(f"  search for {ch!r}: {r['error'].get('info', '')[:100]}"); break
                hits = [x["title"] for x in r["query"]["search"]]
                found.update(hits)
                if "continue" not in r or not hits:
                    break
                off = r["continue"]["sroffset"]; time.sleep(1)
            time.sleep(1)
        log(f"  {ch}: {len(found)} pages so far")
    path = BUILD / "asem_corpus.json"
    corpus = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    got = api.pages(sorted(found))
    corpus.update({t: v[2] for t, v in got.items()})
    path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    return corpus, found

def main(argv):
    if argv and argv[0] == "--search":
        corpus, found = search_pages()
        print(f"{len(found)} pages found by search; corpus now {len(corpus)} pages")
        return 0
    path = argv[0] if argv else str(BUILD / "asem_corpus.json")
    corpus = json.loads(open(path, encoding="utf-8").read())
    both = only_s = only_r = none = 0
    miss, extra = [], []
    for title, text in corpus.items():
        s, r = bool(structural(text)), bool(regex_hits(text))
        if s and r: both += 1
        elif s: only_s += 1; miss.append(title)
        elif r: only_r += 1; extra.append(title)
        else: none += 1
    print(f"{len(corpus)} pages: both detectors fire on {both}, only the parser on {only_s}, only the regex on {only_r}, neither on {none}")
    print("regex misses (the parser sees a violation the regex does not):", miss[:20])
    print("regex false positives:", extra[:20])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
