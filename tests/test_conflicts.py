"""Do the drafts contradict the Wiktionary pages they link to?   Run: python3 tests/test_conflicts.py   (offline)

The analyzer (scripts/wikt_conflicts.py) is tested on saved real pages in tests/data/wikt_pages/ (immerum is an excerpt), including the
case that started this: Akkadian `immerum` lists the Hebrew/Aramaic/Phoenician/Ugaritic "lamb" words as borrowings, so a Proto-Semitic
page treating them as inherited disagrees. The last test runs the analyzer over the real drafts using whatever pages are cached in
build/wikt_pages (fill the cache with: python3 scripts/wikt_conflicts.py --fetch) and fails on any CONFLICT."""
import sys, unittest, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import wikt_conflicts as K

FIX = ROOT / "tests" / "data" / "wikt_pages"
def page(title):
    f = FIX / (urllib.parse.quote(title, safe="") + ".txt")
    return f.read_text(encoding="utf-8") if f.exists() else None
PAGES = {t: page(t) for t in ["immerum", "بق", "ظبي", "ܒܩܐ", "šīrum", "warkatum"]}

def draft(*entries):
    return "{{reconstructed}}\n==Proto-Semitic==\n\n===Noun===\n{{sem-noun|m}}\n\n# x\n\n====Descendants====\n" + "\n".join(entries) + "\n\n===References===\n"
def levels(findings, level):
    return [(t, m) for l, t, m in findings if l == level]

class Analyzer(unittest.TestCase):
    def test_fixtures_exist(self):
        for t, p in PAGES.items():
            self.assertTrue(p, f"fixture for {t} is missing")

    def test_borrowing_conflict_immerum(self):
        d = draft("* {{desc|akk|immerum|tr=immerum|t=sheep}}", "* {{desc|hbo|אִמֵּר|tr=ʔimmēr|t=lamb}}", "* {{desc|phn|𐤀𐤌𐤓|t=lamb}}", "* {{desc|uga|𐎛𐎎𐎗|t=lamb}}")
        c = levels(K.analyze(d, "ʔimmar-", PAGES), "CONFLICT")
        self.assertEqual(len(c), 1, c)
        self.assertIn("BORROWED", c[0][1])
        for name in ("Biblical Hebrew", "Phoenician", "Ugaritic"):
            if name == "Biblical Hebrew":
                continue                                           # reported as Hebrew (he): hbo and he are the same section
            self.assertIn(name, c[0][1])

    def test_no_conflict_when_the_borrowed_languages_are_not_in_the_draft(self):
        d = draft("* {{desc|akk|immerum|tr=immerum|t=sheep}}")
        self.assertEqual(levels(K.analyze(d, "ʔimmar-", PAGES), "CONFLICT"), [])

    def test_etymology_that_names_our_title_is_agreement(self):
        d = draft("* {{desc|ar|بَقّ|t=gnat}}")
        f = K.analyze(d, "baḳḳ-", PAGES)
        self.assertEqual(levels(f, "CONFLICT"), [])
        self.assertTrue([m for _, m in levels(f, "INFO") if "already names" in m], f)

    def test_a_later_mention_of_borrowing_is_not_a_claim(self):      # بق: "... if X and Y are not borrowed from Arabic"
        w = levels(K.analyze(draft("* {{desc|ar|بَقّ|t=gnat}}"), "baḳḳ-", PAGES), "WARN")
        self.assertEqual([m for _, m in w if "borrowed" in m], [])

    def test_etymology_that_names_another_form_is_a_conflict(self):
        d = draft("* {{desc|ar|بَقّ|t=gnat}}")
        c = levels(K.analyze(d, "kalb-", PAGES), "CONFLICT")
        self.assertEqual(len(c), 1, c)
        self.assertIn("different Proto-Semitic form", c[0][1])

    def test_theta_and_dotted_t_are_the_same_title(self):
        d = draft("* {{desc|ar|ظَبْي|t=gazelle}}")
        for title in ("θ̣aby-", "ṯ̣aby-"):
            f = K.analyze(d, title, PAGES)
            self.assertEqual(levels(f, "CONFLICT"), [], title)
            self.assertTrue([m for _, m in levels(f, "INFO") if "already names" in m], title)

    def test_gloss_with_no_shared_word_is_warned(self):
        d = draft("* {{desc|ar|ظَبْي|t=dog}}")
        w = levels(K.analyze(d, "θ̣aby-", PAGES), "WARN")
        self.assertTrue([m for _, m in w if "no shared word" in m], w)
        ok = draft("* {{desc|ar|ظَبْي|t=gazelle}}")
        self.assertEqual([m for _, m in levels(K.analyze(ok, "θ̣aby-", PAGES), "WARN") if "no shared word" in m], [])

    def test_missing_page_and_missing_section_are_info_not_errors(self):
        d = draft("* {{desc|ar|غغغ|t=x}}", "* {{desc|he|ܒܩܐ|t=x}}")          # second: the page exists, but has no Hebrew section
        f = K.analyze(d, "baḳḳ-", {"غغغ": "", "ܒܩܐ": PAGES["ܒܩܐ"]})
        self.assertEqual([l for l, _, _ in f], ["INFO", "INFO"])
        self.assertIn("red link", f[0][2]); self.assertIn("no Hebrew section", f[1][2])

    def test_dash_terms_and_titles_without_marks(self):
        self.assertIsNone(K.term_title("syc", "-", {}))
        self.assertEqual(K.term_title("ar", "وَرِك", {}), "ورك")
        self.assertEqual(K.term_title("hbo", "יָרֵךְ", {}), "ירך")
        self.assertEqual(K.term_title("akk", "warkatum", {"tr": "warkatum"}), "warkatum")

    def test_borrowed_word_is_warned(self):
        pages = {"ورك": "==Arabic==\n===Etymology===\n{{bor|ar|akk|warkatum}}\n===Noun===\n# [[hip]]\n"}
        w = levels(K.analyze(draft("* {{desc|ar|وَرِك|t=hip}}"), "warik-", pages), "WARN")
        self.assertTrue([m for _, m in w if "borrowed" in m], w)

class RealDrafts(unittest.TestCase):
    def test_no_conflict_in_any_draft_with_cached_pages(self):
        if not (K.CACHE.exists() and any(K.CACHE.iterdir())):
            self.skipTest("no cached Wiktionary pages (python3 scripts/wikt_conflicts.py --fetch)")
        drafts = ROOT / "wiktionary_drafts"
        files = sorted(drafts.glob("Proto-Semitic_*.wiki")) + sorted((drafts / "done").glob("Proto-Semitic_*.wiki"))
        res = K.check_files(files)
        for name, findings in res.items():
            with self.subTest(draft=name):
                self.assertEqual(levels(findings, "CONFLICT"), [])
                for t, m in levels(findings, "WARN"):
                    print(f"\n  WARN {name}: {t}: {m}", file=sys.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=1)
