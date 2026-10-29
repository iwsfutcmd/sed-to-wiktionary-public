"""wikt_enrich.py: how an existing page's descendant languages are read and how a SEDonline record is paired with a SED entry."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import wikt_enrich as E


class PageLangs(unittest.TestCase):
    def test_descendants_section(self):
        page = "==Proto-Semitic==\n===Noun===\n# x\n====Descendants====\n* {{desc|akk|a}}\n* {{desc|he|b}}\n** {{desc|arc|c}}\n===References===\n* {{R:x|{{l|ar|d}}}}\n"
        self.assertEqual(E.page_langs(page), {"akk", "he", "arc"})

    def test_desc_under_another_heading(self):              # lišān- lists them under "Derived terms", ʔibr- under "Descedants"
        page = "===Noun===\n====Derived terms====\n*{{l|sem-pro||*liš-ān-u-m}}\n** {{desc|akk|lišānum}}\n** {{desc|ar|لِسَان}}\n"
        self.assertEqual(E.page_langs(page), {"akk", "ar"})

    def test_varieties_count_as_their_language(self):       # Biblical Hebrew is Hebrew; the Aramaic varieties are Aramaic
        page = "====Descendants====\n* {{desc|hbo|a}}\n* {{desc|arc-imp|b}}\n* {{desc|jpa|c}}\n"
        self.assertEqual(E.page_langs(page), {"he", "arc"})


class SameEntry(unittest.TestCase):
    def test_bare_ignores_diacritics_and_optional_parts(self):
        self.assertEqual(E.bare("*ʕaṯm(-at)-"), E.bare("ʕaṯ̣m-"))

    def test_alternatives(self):                             # two forms; a letter alternation
        self.assertIn(E.bare("purḡūṯ-"), E.alternatives("*ṗVrγVṯ-, *ṗVrṯaγ-"))
        self.assertIn(E.bare("miʕay-"), E.alternatives("*maʕay/w(-at)-"))

    def test_other_letters_do_not_pair(self):               # 1N:44 also tags *dbr on SEDonline
        self.assertNotIn(E.bare("dbr"), E.alternatives("*bizz-"))


if __name__ == "__main__":
    unittest.main()
