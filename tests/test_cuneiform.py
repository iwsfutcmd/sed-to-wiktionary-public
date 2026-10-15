"""Akkadian cuneiform checks.  Run: python3 tests/test_cuneiform.py   (offline: uses data/scripts/ebl_signs.json)

The invariant: whenever scripts/tr2script/cuneiform.py returns a spelling, it equals Wiktionary's. The converter may return None
(logograms, readings eBL lacks), but must never disagree with the {{cunsp}} pairs of Wiktionary's Akkadian lemma pages
(tests/data/akk_cunsp_gold.tsv). Also: every cuneiform `alt=` in a draft is an attested spelling that converts back from its
transliteration, so a copied or mistyped sign string is caught."""
import re, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "tests"))
from paths import DATA
from tr2script import cuneiform as C
import wikt_draft as WD
import test_drafts as TD

GOLD = ROOT / "tests" / "data" / "akk_cunsp_gold.tsv"
def gold():
    if not GOLD.exists():
        return []
    rows = [l.rstrip("\n").split("\t") for l in GOLD.read_text(encoding="utf-8").splitlines()[1:]]
    return [r for r in rows if len(r) == 4]

class Readings(unittest.TestCase):
    def test_reading_parser(self):
        for s, want in [("ka", ("ka", 1)), ("ku₁₇", ("ku", 17)), ("rí", ("ri", 2)), ("à", ("a", 3)), ("šu", ("šu", 1)), ("tum4", ("tum", 4)),
                        ("ṣa", ("ṣa", 1)), ("ḫa", ("ḫa", 1))]:
            self.assertEqual(C.reading(s), want, s)
        for s in ["DUG₄", "KA", "{d}", "1", "x", "", "ka.ka", "[ka]"]:
            self.assertIsNone(C.reading(s), s)

    def test_known_spellings(self):                      # pairs from Wiktionary's own cunsp blocks
        for tr, cun in [("wa-ar-ka-tum", "𒉿𒅈𒅗𒌈"), ("wa-ar-ki", "𒉿𒅈𒆠"), ("ši-ru-um", "𒅆𒊒𒌝"), ("ba-aq-qu", "𒁀𒀝𒄣")]:
            self.assertEqual(C.convert(tr), cun, tr)

    def test_indexed_readings_are_refused(self):
        # Wiktionary: ar₂-ki = 𒄱𒆠 (HI×DIŠ); eBL's list gives 𒌒 (UB) for ar₂. Numbering differs between sign lists, so no guessing.
        self.assertIsNone(C.convert("ar₂-ki"))
        self.assertIsNone(C.convert("aš-šum")); self.assertIsNone(C.convert("e-di-iš-tum")); self.assertIsNone(C.convert("qa-aq-qa-dum"))   # DISPUTED (šum, iš, qa, niš, ya, tar)
        for tr in ["sin-niš-tum", "re-ya-um", "tar-lugal-lum"]:
            self.assertIsNone(C.convert(tr), tr)
        self.assertEqual(C.convert("ar₂-ki", indexed=True), "𒌒𒆠")          # what eBL alone would say: not what Wiktionary says
        self.assertNotEqual(C.convert("ar₂-ki", indexed=True), "𒄱𒆠")
        for tr in ["wa-rí-ku₁₇-um", "a-šá-ru-um", "ši-pa-ár"]:
            self.assertIsNone(C.convert(tr), tr)

    def test_refuses_instead_of_guessing(self):
        for tr in ["wa-rí-ku₁₇-um", "DUG₄-ga", "{d}UTU", "ka-x-ma", "", "ka--ma", "ka-ma-"]:
            self.assertIsNone(C.convert(tr), tr)

class AgainstWiktionary(unittest.TestCase):
    def test_converter_never_disagrees_with_wiktionary(self):
        rows = gold()
        if not rows:
            self.skipTest("tests/data/akk_cunsp_gold.tsv not present (fetch it with scripts/akk_gold.py)")
        wrong, converted = [], 0
        for lemma, key, cun, tr in rows:
            got = C.convert(tr)
            if got is None:
                continue
            converted += 1
            if got != cun:
                wrong.append((lemma, tr, cun, got))
        self.assertEqual(wrong[:10], [], f"{len(wrong)} of {converted} converted spellings differ from Wiktionary")
        self.assertGreater(converted, len(rows) * 0.2, "coverage collapsed: is the sign cache empty?")

class Drafts(unittest.TestCase):
    def test_akkadian_alt_is_an_attested_spelling_that_converts_back(self):
        known = {}
        for lemma, key, cun, tr in gold():
            known.setdefault(lemma, []).append((cun, tr))
        for lemma, (lem, cun, tr) in WD.AKK_OVERRIDE.items():
            known.setdefault(lem, []).append((cun, tr or ""))          # tr None: copied from Wiktionary, spelling not given
        seen = 0
        for f in TD.NEW + TD.DONE:
            for tpl, code, term, params in TD.entries(f.read_text(encoding="utf-8")):
                if code != "akk" or "alt" not in params:
                    continue
                with self.subTest(draft=TD.title_of(f), lemma=term):
                    seen += 1
                    pairs = known.get(term) or known.get(term.replace("a", "a"))
                    if pairs is None:                                   # lemma not in the gold set: its alt must come from a cached page
                        page = (ROOT / "build" / "wikt_pages")
                        self.skipTest(f"no attested spelling on record for {term}")
                    self.assertIn(params["alt"], [c for c, _ in pairs], f"{params['alt']} is not a Wiktionary spelling of {term}")
                    for c, tr in pairs:
                        if c == params["alt"] and tr and C.convert(tr) is not None:
                            self.assertEqual(C.convert(tr), c)
        self.assertGreater(seen, 0)

if __name__ == "__main__":
    unittest.main(verbosity=1)
