"""wikt_merge.py: what a merge adds must not already be on the page, through its own lines or a {{desctree}} (the ʕayn- 'eye' case)."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import wikt_merge as M

ROOT = Path(__file__).resolve().parent.parent

# *ʕayn- as it was live, and the Aramaic page its {{desctree|tmr|עַיְנָא}} reads (trimmed to what matters)
LIVE = """==Proto-Semitic==
====Descendants====
* West Semitic:
*** Northwest Semitic:
**** {{desc|arc|-}}
***** {{desctree|tmr|עַיְנָא|tr=ʿaynā}}
**** Canaanite:
***** {{desc|he|עַיִן}}
"""
AINA = """==Aramaic==
===Noun===
# eye
====Descendants====
* {{desc|aii|ܥܝܢܐ|tr=ʿayna}}
* {{desctree|myz|ࡀࡉࡍࡀ|ts=eyna}}
* {{desc|syc|ܥܰܝܢܳܐ|tr=ʿaynā}}
* {{desc|tru|ܥܰܝܢܳܐ}}
"""
PAGES = {"עינא": AINA, "ࡀࡉࡍࡀ": ""}


class Duplicates(unittest.TestCase):
    def test_first_eye_card_is_caught(self):              # the card as first written: Syriac, Mandaic, Turoyo, Assyrian already shown via the desctree
        merged = LIVE.replace("***** {{desctree|tmr|עַיְנָא|tr=ʿaynā}}\n", "***** {{desctree|tmr|עַיְנָא|tr=ʿaynā}}\n"
                              "***** {{desc|arc-imp|𐡏𐡉𐡍}}\n***** {{desc|syc|ܥܝܢܐ}}\n***** {{desc|myz|ࡀࡉࡍࡀ}}\n"
                              "***** {{desc|tru|ܥܰܝܢܳܐ}}\n***** {{desc|aii|ܥܲܝܢܵܐ}}\n")
        self.assertEqual(M.duplicates(LIVE, merged, PAGES.get), ["aii", "myz", "syc", "tru"])

    def test_fixed_eye_card_passes(self):
        merged = LIVE.replace("***** {{desctree|tmr|עַיְנָא|tr=ʿaynā}}\n", "***** {{desctree|tmr|עַיְנָא|tr=ʿaynā}}\n***** {{desc|arc-imp|𐡏𐡉𐡍}}\n")
        self.assertEqual(M.duplicates(LIVE, merged, PAGES.get), [])

    def test_a_language_already_on_the_page(self):
        merged = LIVE + "***** {{desc|he|עין}}\n"
        self.assertEqual(M.duplicates(LIVE, merged, PAGES.get), ["he"])


class SamePage(unittest.TestCase):
    def test_same_word_twice(self):
        self.assertEqual(M.same_page_repeats("* {{desc|syc|ܥܰܝܢܳܐ}}\n* {{desc|syc|ܥܝܢܐ|tr=ʕaynā}}\n"), ["syc"])

    def test_two_words_or_dialects_are_fine(self):
        self.assertEqual(M.same_page_repeats("* {{desc|am|አጥንት}}\n** {{desc|am|አጽም|bor=1}}\n"), [])            # bone
        self.assertEqual(M.same_page_repeats("* {{desc|sgw|ኤን|q=Chaha}}\n* {{desc|sgw|ኤን|q=Ezha}}\n"), [])

    def test_every_merge_file(self):                        # offline, on what is in the repo
        for f in sorted((ROOT / "wiktionary_drafts" / "merges").glob("*.wiki")):
            with self.subTest(merge=f.stem):
                self.assertEqual(M.same_page_repeats(f.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
