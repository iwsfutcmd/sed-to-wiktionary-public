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
        self.assertEqual(s["insert"], "{{inh|akk|sem-pro|*warik-}}")
        self.assertIn("===Etymology===", s["full"]); self.assertIn("{{inh|akk|sem-pro|*warik-}}", s["full"])

    def test_append_mode_when_the_etymology_does_not_mention_us(self):
        page = "==Akkadian==\n===Etymology===\nCognate with {{cog|ar|وَرِك|t=hip}}.\n===Noun===\n# [[rear]]\n"
        s = B.suggestion(page, "akk", "PS", "warik-")
        self.assertEqual(s["mode"], "append")
        self.assertIn("Cognate with", s["current"])
        self.assertEqual(s["insert"], "{{inh|akk|sem-pro|*warik-}}")
        self.assertEqual(s["full"], "From {{inh|akk|sem-pro|*warik-}}. Cognate with {{cog|ar|وَرِك|t=hip}}.")

    def test_candidates_for_matches_only_the_clean_entry(self):
        d = draft("* {{desc|akk|warkatum|tr=warkatum|t=rear}}", "* {{desc|ar|بَقّ|t=gnat}}")
        pages = {"warkatum": "==Akkadian==\n===Etymology===\nCompare something.\n===Noun===\n# [[rear]]\n",
                 "بق": "==Arabic==\n===Etymology===\nFrom {{inh|ar|sem-pro|*baḳḳ-}}.\n===Noun===\n# [[gnat]]\n"}
        c = B.candidates_for(d, "warik-", pages)
        self.assertEqual([(x["code"], x["page"]) for x in c], [("akk", "warkatum")])

    def test_draft_title_level_reads_the_filename(self):
        self.assertEqual(B.draft_title_level(Path("Proto-Semitic_warik-.wiki")), ("warik-", "PS"))
        self.assertEqual(B.draft_title_level(Path("Proto-West_Semitic_ṣ́abb-.wiki")), ("ṣ́abb-", "PWS"))

class WholePage(unittest.TestCase):
    PAGE = "==Arabic==\n===Etymology===\nCompare {{cog|he|x}}.\n\n===Noun===\n# [[pig]]\n\n----\n\n==Persian==\n===Etymology===\nCompare y.\n===Noun===\n# z\n"
    def test_append_touches_only_that_language(self):
        new = B.edited_page(self.PAGE, "ar", "PS", "ḫVzīr-")
        self.assertIn("===Etymology===\nFrom {{inh|ar|sem-pro|*ḫVzīr-}}. Compare {{cog|he|x}}.", new)
        self.assertEqual(new.split("==Persian==")[1], self.PAGE.split("==Persian==")[1])
        self.assertEqual(new.replace("From {{inh|ar|sem-pro|*ḫVzīr-}}. ", ""), self.PAGE)
    def test_create_goes_after_alternative_forms_and_before_the_rest(self):
        page = "==Classical Syriac==\n===Alternative forms===\n* x\n\n===Noun===\n# [[pig]]\n"
        new = B.edited_page(page, "syc", "PS", "ḫVzīr-")
        self.assertEqual(new, "==Classical Syriac==\n===Alternative forms===\n* x\n\n===Etymology===\nFrom {{inh|syc|sem-pro|*ḫVzīr-}}.\n\n===Noun===\n# [[pig]]\n")
        page = "==Classical Syriac==\n{{wp}}\n===Noun===\n# [[pig]]\n"
        self.assertEqual(B.edited_page(page, "syc", "PWS", "ṣ́abb-"),
                         "==Classical Syriac==\n{{wp}}\n===Etymology===\nFrom {{inh|syc|sem-wes-pro|*ṣ́abb-}}.\n\n===Noun===\n# [[pig]]\n")
    def test_empty_etymology_is_filled(self):
        page = "==Akkadian==\n===Etymology===\n\n===Noun===\n# [[pig]]\n"
        self.assertEqual(B.edited_page(page, "akk", "PS", "ḫVzīr-"), "==Akkadian==\n===Etymology===\nFrom {{inh|akk|sem-pro|*ḫVzīr-}}.\n\n===Noun===\n# [[pig]]\n")

class ChosenSection(unittest.TestCase):
    PAGE = ("==Arabic==\n{{ar-rootbox|ض ر ط}}\n\n===Etymology 1.1===\n\n====Verb====\n# to fart\n\n===Etymology 1.2===\n\n====Noun====\n# x\n\n"
            "==Classical Syriac==\n\n===Etymology 1===\n{{syc-rootbox|ܒ ܩ ܩ}}\nCompare y.\n\n====Noun====\n# gnat\n\n===Etymology 2===\nZ.\n")
    def test_empty_chosen_section(self):
        new = B.edited_page(self.PAGE, "ar", "PS", "ṣ́araṭ-", section="Etymology 1.1")
        self.assertIn("===Etymology 1.1===\nFrom {{inh|ar|sem-pro|*ṣ́araṭ-}}.\n\n====Verb====", new)
        self.assertEqual(new.count("{{inh"), 1)
    def test_chosen_section_after_its_rootbox(self):
        new = B.edited_page(self.PAGE, "syc", "PS", "baḳḳ-", section="Etymology 1")
        self.assertIn("{{syc-rootbox|ܒ ܩ ܩ}}\nFrom {{inh|syc|sem-pro|*baḳḳ-}}. Compare y.", new)
        self.assertIn("===Etymology 2===\nZ.", new)
    def test_missing_section_is_an_error(self):
        with self.assertRaises(ValueError):
            B.edited_page(self.PAGE, "ar", "PS", "ṣ́araṭ-", section="Etymology 3")

class Chains(unittest.TestCase):
    def test_ety_chain_gets_the_step(self):
        page = "==Arabic==\n{{ar-rootbox|ش ح م}}\n{{ety|ar|id=fat|:root|ش ح م<id:root>|tree=1}}\n\n===Noun===\n# [[fat]]\n"
        new = B.edited_page(page, "ar", "PS", "śaḥm-")         # no prose: the sentence goes on its own line after the chain
        self.assertEqual(new, page.replace("tree=1}}\n", "tree=1|:inh|sem-pro:*śaḥm-}}\n{{inh+|ar|sem-pro|*śaḥm-}}.\n"))
    def test_ety_chain_with_prose(self):                         # Arabic ورك: the tree alone shows nothing in the text
        page = ("==Arabic==\n\n===Etymology===\n{{ety|ar|id=hip|:root|و ر ك<id:root>|tree=1}}\nFrom the root {{ar-root|و ر ك}}. "
                "Compare {{cog|he|יָרֵךְ|t=thigh}}.\n\n===Pronunciation===\n{{ar-pr|وَرِك}}\n")
        new = B.edited_page(page, "ar", "PS", "warik-")
        self.assertIn("tree=1|:inh|sem-pro:*warik-}}\nFrom the root {{ar-root|و ر ك}}. {{inh+|ar|sem-pro|*warik-}}. Compare {{cog|he|יָרֵךְ|t=thigh}}.\n\n===Pronunciation===", new)
        page2 = page.replace("Compare {{cog|he|יָרֵךְ|t=thigh}}.", "Of unclear formation.")
        self.assertIn("From the root {{ar-root|و ر ك}}. Of unclear formation. {{inh+|ar|sem-pro|*warik-}}.\n\n===Pronunciation===", B.edited_page(page2, "ar", "PS", "warik-"))
        self.assertIsNone(B.skip_reason(page, "ar", "fat"))
    def test_rootbox_stays_first(self):
        page = "==Hebrew==\n===Etymology===\n{{he-rootbox|י־ר־ך}}\nCognate with x.\n\n===Noun===\n# [[thigh]]\n"
        self.assertIn("{{he-rootbox|י־ר־ך}}\nFrom {{inh|hbo|sem-pro|*warik-}}. Cognate with x.", B.edited_page(page, "hbo", "PS", "warik-"))
    def test_another_word_with_the_same_spelling(self):
        page = "==Hebrew==\n{{he-rootbox|כ־ר־ר}}\n\n===Noun===\n# {{tcl|he|cushion|nogloss=1}}\n# [[pillow]]\n"
        self.assertIn("share no word", B.skip_reason(page, "hbo", "(young) ram"))

class Skip(unittest.TestCase):
    def test_reasons(self):
        sk = lambda body, code="ar", head="Arabic": B.skip_reason(f"=={head}==\n{body}\n===Noun===\n# x\n", code)
        self.assertIsNone(sk("===Etymology===\nCompare {{cog|he|x}}."))
        self.assertIsNone(sk(""))
        self.assertIn("several Etymology", sk("===Etymology 1===\nx\n===Noun===\n# a\n===Etymology 2===\ny"))
        self.assertIn("later stage", sk("===Etymology===\nCompare x.", "aii", "Assyrian Neo-Aramaic"))
        self.assertIn("names an ancestor", sk("===Etymology===\n{{inh+|ar|arc|x}}; cognate to y."))
        self.assertIn("names an ancestor", sk("===Etymology===\nCompare {{bor|ar|arc|x}}."))
        self.assertIn("names an ancestor", sk("===Etymology===\n{{ety|ar|:inh|arc:x}}"))
        self.assertIn("opens with a source", sk("===Etymology===\nFrom a lost noun ''*warkum''."))
        self.assertIsNone(sk("===Etymology===\nCompare {{inh|ar|sem-pro|*y-}}."))   # a PS reference is not an ancestor to defer to

class RealDrafts(unittest.TestCase):
    def test_plan_runs_over_whatever_is_cached(self):
        if not (K.CACHE.exists() and any(K.CACHE.iterdir())):
            self.skipTest("no cached Wiktionary pages (python3 scripts/wikt_conflicts.py --fetch)")
        for r in B.plan():
            self.assertIn(r["mode"], ("create", "append"))
            self.assertTrue(r["insert"].startswith("{{inh|"))
            self.assertIn(r["insert"], r["full"])

if __name__ == "__main__":
    unittest.main(verbosity=1)
