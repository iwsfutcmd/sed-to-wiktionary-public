"""Is a Wiktionary draft good to go?   Offline (default):  python3 tests/test_drafts.py
Also against the live wiki:                              ONLINE=1 python3 tests/test_drafts.py
Report of warnings (not failures), e.g. forms still missing a script:  python3 tests/test_drafts.py --report

Checks every wiktionary_drafts/*.wiki (a draft) and wiktionary_drafts/done/*.wiki (already saved: structure, reference, words and
script checks only, since the live page is authoritative for those).

Per draft: well-formed wikitext; the SED reference matches the SEDonline entry it was built from; print and site agree on the entry
(sed_print_vs_site_agreement.tsv) and no Wiktionary title with that form exists; every word SEDonline lists is on the page; every
term is in the script its language is written in; glosses are English; tr= follows Wiktionary's conventions; the file is what the
generator produces (when its Wiktionary page cache is present). Online: the title is still free, no other spelling of the title already has incoming links,
and the language codes mean what we think."""
import json, os, re, sys, tempfile, time, unicodedata as U, unittest, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from paths import DATA, BUILD
from sedonline_compare import read, fold, titles, skeleton
import wikt_draft as WD

DRAFTS = ROOT / "wiktionary_drafts"
NEW = sorted(DRAFTS.glob("Proto-Semitic_*.wiki"))
DONE = sorted((DRAFTS / "done").glob("Proto-Semitic_*.wiki"))
ONLINE = bool(os.environ.get("ONLINE"))

from wikt_langs import LANGS, RANGES
def scripts_of(text):
    out = set()
    for ch in text:
        o = ord(ch)
        for name, a, b in RANGES:
            if a <= o <= b:
                out.add(name); break
        else:
            if U.category(ch).startswith("L") and U.name(ch, "").startswith("LATIN"):
                out.add("Latin")
    return out

ENT = re.compile(r"\{\{(desc|l)\|([^|{}]+)\|([^|{}]*)((?:\|[^{}]*)?)\}\}")
def entries(text):
    """[(template, code, term, params)] for the descendants section."""
    body = text[text.index("====Descendants===="):text.index("===References===")]
    out = []
    for m in ENT.finditer(body):
        params = dict(p.split("=", 1) for p in m.group(4).split("|") if "=" in p)
        out.append((m.group(1), m.group(2), m.group(3), params))
    return out
def title_of(path):
    return path.name[len("Proto-Semitic_"):-len(".wiki")]
def rec_of(text):
    m = re.search(r"\{\{R:sem-pro:SED\|volume=(I+)\|id=(\d+)\|entry=([^}]*)\}\}", text)
    return m.groups() if m else None
def norm(s):
    s = U.normalize("NFC", s).replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ḳ", "q").replace("ǝ", "ə").lower()
    return re.sub(r"[\s*\-()]", "", s)

def forall(files):
    """Run the decorated check on every file, each as its own subTest named after the draft."""
    def deco(fn):
        def test(self):
            self.assertTrue(files, "no drafts found")
            for f in files:
                with self.subTest(draft=title_of(f)):
                    fn(self, f.read_text(encoding="utf-8"), title_of(f))
        test.__name__ = fn.__name__
        test.__doc__ = fn.__doc__
        return test
    return deco

RECS = {r["rec_id"]: r for r in read(DATA / "sedonline" / "sedonline_reconstructions.tsv")}
WORDS = defaultdict(list)
for w in read(DATA / "sedonline" / "sedonline_words.tsv"):
    WORDS[w["rec_id"]].append(w)
AGREE = {r["rec_id"]: r for r in read(DATA / "sedonline" / "sed_print_vs_site_agreement.tsv")}

def convention_problems(t):
    """tr= / term conventions for descendants (see test_transliteration_follows_wiktionary_conventions)."""
    out = []
    for tpl, code, term, params in entries(t):
        tr = params.get("tr", "")
        if re.search("[ˀˁǝḳɨ]", tr):
            out.append(f"{code}: tr={tr!r} uses SED symbols (use ʔ ʕ ə q)")
        if code in WD.AUTO_TR and "tr" in params:
            out.append(f"{code}: Wiktionary transliterates this itself; drop tr={tr}")
        if code in ("gdq", "shv", "hss", "bhm", "sqt", "amw", "xeb") and "tr" in params:
            out.append(f"{code}: a Latin term needs no tr=")
    return out

class Drafts(unittest.TestCase):
    # ---------- structure ----------
    @forall(NEW + DONE)
    def test_wikitext_is_well_formed(self, t, title):
        self.assertTrue(t.startswith("{{reconstructed}}\n==Proto-Semitic==\n"), "must start with {{reconstructed}} and ==Proto-Semitic==")
        self.assertEqual(t.count("{{"), t.count("}}"), "unbalanced {{ }}")
        self.assertEqual(t.count("[["), t.count("]]"), "unbalanced [[ ]]")
        pos = re.findall(r"^={3}(Noun|Verb)={3}$", t, flags=re.M)
        self.assertEqual(len(pos), 1, "exactly one ===Noun=== or ===Verb===")
        self.assertIn("====Descendants====", t); self.assertIn("===References===", t)
        self.assertLess(t.index("===" + pos[0] + "==="), t.index("====Descendants===="))
        self.assertLess(t.index("====Descendants===="), t.index("===References==="))
        self.assertRegex(t, r"(?m)^# \S", "needs at least one definition")
        if pos[0] == "Noun":
            self.assertRegex(t, r"\{\{sem-noun\|", "noun needs {{sem-noun|...}}")
        else:
            self.assertIn("{{head|sem-pro|verb}}", t)
        self.assertNotRegex(t, r"TODO|FIXME|\?\?\?|\[script needed\]")
        self.assertTrue(t.endswith("\n") and not t.endswith("\n\n"))

    @forall(NEW + DONE)
    def test_reference_matches_sedonline(self, t, title):
        ref = rec_of(t)
        self.assertIsNotNone(ref, "needs {{R:sem-pro:SED|volume=...|id=...|entry=...}}")
        vol, rid, entry = ref
        self.assertIn(rid, RECS, "unknown SEDonline id")
        rec = RECS[rid]
        self.assertEqual(rec["level"], "PS", "the printed volumes reconstruct Proto-Semitic")
        keys = [k for k in rec["sed_ref"].split(";") if k]
        self.assertIn({"I": "1", "II": "2"}[vol], [k[0] for k in keys], "volume does not match the SED number SEDonline cites")
        # entry = the SED spelling; compare consonant skeletons so ṣ̂/ṣ́, ŝ/ś, ˀ/ʔ do not matter
        self.assertEqual(skeleton(entry), skeleton(rec["form"]), f"entry {entry!r} vs SEDonline {rec['form']!r}")

    @forall(NEW + DONE)
    def test_title_belongs_to_the_reconstruction(self, t, title):
        _, rid, _ = rec_of(t)
        self.assertEqual(skeleton(title), skeleton(RECS[rid]["form"]), "title and reconstruction have different consonants")
        self.assertTrue(title.endswith("-") or not re.search("[aiuāīū]", title), "stems end in -, roots have no vowels")

    # ---------- selection rule ----------
    @forall(NEW + DONE)
    def test_print_and_site_agree(self, t, title):
        _, rid, _ = rec_of(t)
        self.assertIn(rid, AGREE, "entry is not cited by number from the printed SED")
        a = AGREE[rid]
        self.assertEqual(a["agree"], "1", f"print and site differ: {a['protoform']} / {a['web_form']}; "
                         f"only in print: {a['langs_only_print']}; only on site: {a['langs_only_web']}")

    @forall(NEW)
    def test_no_wiktionary_page_with_this_form_in_the_snapshot(self, t, title):
        idx = {**titles("wik_ps.json"), **titles("wik_pws.json")}
        self.assertNotIn(fold(title), idx, "the title snapshot already has this form")

    # ---------- content ----------
    @forall(NEW + DONE)
    def test_every_sedonline_word_is_on_the_page(self, t, title):
        _, rid, _ = rec_of(t)
        ents = entries(t)
        self.assertTrue(ents)
        skip = WD.PAGES.get(title, {}).get("exclude", {})              # words left out on purpose, each with a reason
        words_ = [w for w in WORDS[rid] if (w["lang"], w["form"]) not in skip]
        per = Counter(code for _, code, _, _ in ents)
        expect = Counter(WD.LANG[w["lang"]][0] for w in words_)
        for code, n in expect.items():
            need = 1 if code == "xeb" else n               # Eblaite spelling variants are one word
            self.assertGreaterEqual(per[code], need, f"{LANGS.get(code, (code,))[0]}: {per[code]} entries for {n} SEDonline words")
        blob = norm(" ".join(term + " " + p.get("tr", "") for _, _, term, p in ents))
        for w in words_:                                    # forms are checkable where the page keeps Latin (tr= or a Latin term)
            code = WD.LANG[w["lang"]][0]
            if code in WD.AUTO_TR or code == "xeb":
                continue
            first = re.sub(r"\s*\((suff|det)[^)]*\)$", "", w["form"]).split(",")[0].split("/")[0].strip()
            self.assertIn(norm(first)[:5], blob, f"{w['lang']} {w['form']!r} is missing")

    @forall(NEW + DONE)
    def test_terms_are_in_the_script_of_their_language(self, t, title):
        for tpl, code, term, params in entries(t):
            self.assertIn(code, LANGS, f"language code {code!r} has not been verified")
            if term == "-":
                self.assertTrue(params.get("tr"), f"{code}: '-' needs tr=")
                continue
            sc = scripts_of(term)
            self.assertTrue(sc and sc <= LANGS[code][1], f"{code} {term!r}: script {sc} is not one of {LANGS[code][1]}")
            if code == "akk" and "alt" in params:
                self.assertTrue(scripts_of(params["alt"]) <= {"Cuneiform"}, "alt= must be cuneiform")

    @forall(NEW + DONE)
    def test_glosses_are_short_english(self, t, title):
        foreign = re.compile(r"\b(der|die|das|und|im|ein|eine|von|mit|le|la|les|un|une|des|du|di|il|lo|gli|partorire|guérir|accouché|Kindbett)\b", re.I)
        for tpl, code, term, params in entries(t):
            g = params.get("t", "")
            self.assertLessEqual(len(g), 100, f"{code}: gloss too long: {g}")
            self.assertFalse(re.search(r"[^\x00-\x7F]", g), f"{code}: non-ASCII in gloss {g!r}")
            self.assertIsNone(foreign.search(g), f"{code}: gloss looks non-English: {g!r}")
            self.assertFalse(g.startswith("="), f"{code}: gloss is a note, not a meaning: {g!r}")

    @forall(NEW)
    def test_transliteration_follows_wiktionary_conventions(self, t, title):
        self.assertEqual(convention_problems(t), [])

    def test_pages_already_on_wiktionary_are_flagged_when_they_would_change(self):
        """Not a failure: the saved copies in done/ are what you pasted. This FLAGS what has changed since (convention fixes, new data),
        so you can update the live page. Details: `make done-check` (diffs, new versions in wiktionary_drafts/updates/)."""
        if not (BUILD / "wikt_pages").exists():
            self.skipTest("no Wiktionary page cache")
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            changed = WD.check_done()
        for title in changed:
            say(f"\n  FLAG: done/{title} would change if regenerated (make done-check)")
        for f in DONE:
            for problem in convention_problems(f.read_text(encoding="utf-8")):
                say(f"\n  FLAG: done/{title_of(f)}: {problem}")

    @forall(NEW)
    def test_branches_are_in_wiktionarys_order(self, t, title):
        order = ["East Semitic", "West Semitic", "Central Semitic", "Northwest Semitic", "Canaanite", "Old South Arabian", "Ethiopian Semitic",
                 "Modern South Arabian"]
        heads = [m.group(1) for m in re.finditer(r"^\*+ ([A-Z][A-Za-z ]+):$", t, flags=re.M)]
        for group in (("East Semitic", "West Semitic"), ("Central Semitic", "Ethiopian Semitic", "Modern South Arabian")):
            got = [h for h in heads if h in group]
            self.assertEqual(got, sorted(got, key=order.index), f"branch order: {heads}")

    def test_committed_draft_is_what_the_generator_produces(self):
        if not (BUILD / "wikt_pages").exists():
            self.skipTest("no Wiktionary page cache (run scripts/wikt_draft.py once, it needs the network)")
        with tempfile.TemporaryDirectory() as tmp:
            for title, cfg in WD.PAGES.items():
                f = DRAFTS / f"Proto-Semitic_{title}.wiki"
                if not f.exists():
                    continue
                with self.subTest(draft=title):
                    WD.build(title, cfg, out=tmp)
                    self.assertEqual((Path(tmp) / f.name).read_text(encoding="utf-8"), f.read_text(encoding="utf-8"),
                                     "draft was edited by hand or is stale: re-run scripts/wikt_draft.py (or move it to done/)")

# ---------------- live wiki ----------------
UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
def api(**q):
    """One request: 20 s timeout, at most two quick retries on 429, then fail loudly (never sit in a long back-off)."""
    data = urllib.parse.urlencode(dict(format="json", formatversion=2, **q)).encode()
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=20))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 2:
                raise unittest.SkipTest(f"en.wiktionary.org answered HTTP {e.code} (rate limited?): try again later")
            time.sleep(min(float(e.headers.get("Retry-After") or 3), 8))
        except (urllib.error.URLError, TimeoutError) as e:
            raise unittest.SkipTest(f"en.wiktionary.org not reachable: {e}")
def say(msg):
    print(msg, file=sys.stderr, flush=True)
def spellings(title):
    """Other spellings Wiktionary mixes for the same Proto-Semitic title."""
    swaps = [("ḳ", "q"), ("q", "ḳ"), ("ṯ̣", "θ̣"), ("θ̣", "ṯ̣"), ("ṯ̣", "ṱ"), ("ṣ́", "ṣ̂"), ("ṣ̂", "ṣ́"), ("ś", "ŝ"), ("ŝ", "ś"), ("ʔ", "ˀ"), ("ʕ", "ˁ"),
             ("ṯ", "θ"), ("θ", "ṯ"), ("ḏ", "δ"), ("ḫ", "x"), ("ġ", "γ")]
    t0 = U.normalize("NFC", title); out = set()
    for a, b in swaps:
        if a in t0:
            out.add(t0.replace(a, b))
    return out - {t0}

@unittest.skipUnless(ONLINE, "set ONLINE=1 to check against en.wiktionary.org")
class Online(unittest.TestCase):
    """A handful of requests, each with a 20 s timeout."""
    PFX = "Reconstruction:Proto-Semitic/"
    def test_titles_are_free_and_not_linked_under_another_spelling(self):
        alts = {t: sorted(spellings(t)) for t in map(title_of, NEW)}
        say("  titles (one request)")
        names = [self.PFX + x for t, a in alts.items() for x in [t] + a]
        exists = {}
        for i in range(0, len(names), 50):
            for pg in api(action="query", titles="|".join(names[i:i + 50]))["query"]["pages"]:
                exists[pg["title"]] = not pg.get("missing")
        for title, others in alts.items():
            with self.subTest(draft=title):
                self.assertFalse(exists.get(self.PFX + title), "a page with this title already exists on Wiktionary")
                for alt in others:
                    self.assertFalse(exists.get(self.PFX + alt), f"{alt!r} already exists: use that title")
                    say(f"  links to {alt}")
                    bl = api(action="query", list="backlinks", bltitle=self.PFX + alt, bllimit=5, blnamespace="0|118")["query"]["backlinks"]
                    self.assertFalse(bl, f"{alt!r} is linked from {[b['title'] for b in bl]}: use that title")

    def test_language_codes_mean_what_we_think(self):
        codes = sorted({code for f in NEW + DONE for _, code, _, _ in entries(f.read_text(encoding="utf-8"))})
        say("  language codes (one request)")
        html = api(action="parse", title=self.PFX + "x", text="\n".join(f"* {{{{desc|{c}|-|tr=x}}}}" for c in codes), prop="text",
                   contentmodel="wikitext", disablelimitreport=1)["parse"]["text"]
        lines = [l.strip() for l in re.sub(r"<style.*?</style>", "", re.sub(r"<[^>]+>", "\n", html.replace("</li>", "</li>\n")), flags=re.S).split("\n")
                 if re.match(r"^[^:]{2,40}:$", l.strip())]
        self.assertIn("Lua error", html) if False else None
        self.assertNotIn("Lua error", html, "one of the language codes is not valid")
        got = [l[:-1] for l in lines]
        for code in codes:
            with self.subTest(code=code):
                self.assertIn(LANGS[code][0], got, f"{code} should render as {LANGS[code][0]!r}; page shows {got}")

def report():
    """Warnings that are not failures: descendants still without a script, per draft."""
    for f in NEW:
        t = f.read_text(encoding="utf-8"); ents = entries(t)
        miss = [(c, p.get("tr")) for _, c, term, p in ents if term == "-"]
        print(f"{title_of(f):10} {len(ents):3} descendants, {len(miss)} without script: {miss}")

if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        unittest.main(verbosity=1)
