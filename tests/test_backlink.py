"""Does wikt_backlink.py propose the right template, in the right place?   Run: python3 tests/test_backlink.py   (offline)"""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import wikt_backlink as B
import wikt_conflicts as K

def draft(*entries):
    return "{{reconstructed}}\n==Proto-Semitic==\n\n===Noun===\n{{sem-noun|m}}\n\n# x\n\n====Descendants====\n" + "\n".join(entries) + "\n\n===References===\n"

class Backlink(unittest.TestCase):
    def test_inh_template_names_the_right_level(self):
        self.assertEqual(B.inh_template("akk", "PS", "warik-"), "{{inh|akk|sem-pro|*warik-}}")
        self.assertEqual(B.inh_template("ar", "PWS", "ṣ́abb-"), "{{inh|ar|sem-wes-pro|*ṣ́abb-}}")

    def test_create_mode_when_the_page_has_no_etymology_section(self):
        page = "==Akkadian==\n===Noun===\n# [[rear]]\n"
        s = B.suggestion(page, "akk", "PS", "warik-")
        self.assertEqual(s["mode"], "create")
        self.assertIn("===Etymology===", s["insert"]); self.assertIn("{{inh|akk|sem-pro|*warik-}}", s["insert"])

    def test_append_mode_when_the_etymology_does_not_mention_us(self):
        page = "==Akkadian==\n===Etymology===\nCognate with {{cog|ar|وَرِك|t=hip}}.\n===Noun===\n# [[rear]]\n"
        s = B.suggestion(page, "akk", "PS", "warik-")
        self.assertEqual(s["mode"], "append")
        self.assertIn("Cognate with", s["current"])
        self.assertEqual(s["insert"], "{{inh|akk|sem-pro|*warik-}}")

    def test_candidates_for_matches_only_the_clean_entry(self):
        d = draft("* {{desc|akk|warkatum|tr=warkatum|t=rear}}", "* {{desc|ar|بَقّ|t=gnat}}")
        pages = {"warkatum": "==Akkadian==\n===Etymology===\nCompare something.\n===Noun===\n# [[rear]]\n",
                 "بق": "==Arabic==\n===Etymology===\nFrom {{inh|ar|sem-pro|*baḳḳ-}}.\n===Noun===\n# [[gnat]]\n"}
        c = B.candidates_for(d, "warik-", pages)
        self.assertEqual([(x["code"], x["page"]) for x in c], [("akk", "warkatum")])

    def test_draft_title_level_reads_the_filename(self):
        self.assertEqual(B.draft_title_level(Path("Proto-Semitic_warik-.wiki")), ("warik-", "PS"))
        self.assertEqual(B.draft_title_level(Path("Proto-West_Semitic_ṣ́abb-.wiki")), ("ṣ́abb-", "PWS"))

class RealDrafts(unittest.TestCase):
    def test_plan_runs_over_whatever_is_cached(self):
        if not (K.CACHE.exists() and any(K.CACHE.iterdir())):
            self.skipTest("no cached Wiktionary pages (python3 scripts/wikt_conflicts.py --fetch)")
        for r in B.plan():
            self.assertIn(r["mode"], ("create", "append"))
            self.assertTrue(r["insert"].startswith("{{inh|"))

if __name__ == "__main__":
    unittest.main(verbosity=1)
