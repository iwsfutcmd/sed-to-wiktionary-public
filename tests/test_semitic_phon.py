"""semitic_phon.py: the sound-correspondence sanity check that a form is plausible beside its cognates (it would have caught Ugaritic *bgy)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import semitic_phon as P


class Correspondences(unittest.TestCase):
    def test_bgy_is_caught(self):                     # בעא: the source said Ugaritic bgy; Arabic بغى and Hebrew בעה point to *ġ
        ok, why = P.check("uga", "bgy", [("ar", "بَغَى"), ("he", "בָּעָה")])
        self.assertIs(ok, False, why)
        ok, why = P.check("uga", "𐎁𐎂𐎊", [("ar", "بَغَى")])
        self.assertIs(ok, False, why)

    def test_bgy_corrected_passes(self):              # Fay Freak's correction, 𐎁𐎙𐎊 bġy
        self.assertIs(P.check("uga", "𐎁𐎙𐎊", [("ar", "بَغَى"), ("he", "בָּעָה")])[0], True)
        self.assertIs(P.check("uga", "bġy", [("ar", "بغى")])[0], True)

    def test_merged_letters(self):                    # Hebrew ש covers *š *ś *ṯ; Aramaic ע covers *ʕ *ġ
        self.assertIs(P.check("he", "שלש", [("ar", "ثلاث")])[0], True)            # *ṯalāṯ-
        self.assertIs(P.check("arc", "עין", [("ar", "عَيْن")])[0], True)
        self.assertIs(P.check("arc", "תלת", [("ar", "ثلاث")])[0], True)            # Aramaic t < *ṯ

    def test_weak_consonants_and_feminine_t(self):
        self.assertIs(P.check("he", "שָׁנָה", [("ar", "سَنَة")])[0], True)
        self.assertIs(P.check("gez", "ልብ", [("he", "לֵב")])[0], True)

    def test_unrelated_consonants_fail(self):
        self.assertIs(P.check("uga", "spr", [("ar", "كَلْب")])[0], False)

    def test_no_comparanda_is_no_verdict(self):
        self.assertIsNone(P.check("uga", "spr", [])[0])
        self.assertIsNone(P.check("uga", "spr", [("en", "sapphire")])[0])


if __name__ == "__main__":
    unittest.main()


class FillSanity(unittest.TestCase):
    """wikt_script_requests.sanity() on the real case: the בעא line as it was before our fill."""
    LINE = ("Compare {{cog|he|בָּעָה|t=to inquire, to seek, to ask}}, {{cog|ar|بَغَى|t=to desire, to want}}, {{cog|uga||tr=bgy}}, "
            "and {{cog|akk||ts=bu''û|t=to look for, to seek}}.")
    def test_bgy_fill_is_refused(self):
        import wikt_script_requests as R
        R.K.cached = lambda t, _orig=R.K.cached: self.LINE if t == "TEST" else _orig(t)
        row = dict(page="TEST", code="uga", template="{{cog|uga||tr=bgy}}")
        verdict, why = R.sanity(row, "𐎁𐎂𐎊", {})
        self.assertIs(verdict, False, why)
        self.assertIs(R.sanity(row, "𐎁𐎙𐎊", {})[0], True)


class Lossless(unittest.TestCase):
    """Old South Arabian, Mandaic, Eblaite and Ethiopic fills may go ahead unconfirmed (the user's call, 2026-10-31), never when contradicted."""
    def test_rule(self):
        import wikt_script_requests as R
        self.assertIn("xsa", R.LOSSLESS); self.assertIn("myz", R.LOSSLESS)
        self.assertNotIn("uga", R.LOSSLESS); self.assertNotIn("arc", R.LOSSLESS); self.assertNotIn("ar", R.LOSSLESS)
