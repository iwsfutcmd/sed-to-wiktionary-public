"""Every page we write or add to (wiktionary_drafts/done/, merges/) cites the SED the same way: each {{R:sem-pro:SED}} links its SEDonline
record (id= or e=), and the page sits at the level SEDonline gives that record, unless LEVEL_EXCEPTIONS says why not (ʕigl- 'calf', a
Proto-West Semitic page citing a record the SED files as Proto-Semitic, was found this way and kept as it is by decision)."""
import csv, re, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

REF = re.compile(r"\{\{R:sem-pro:SED(\|[^{}]*)?\}\}")
# A page at another level than SEDonline gives, on purpose: page -> why. Anything else that disagrees fails.
LEVEL_EXCEPTIONS = {
    "Proto-Semitic_gild-": "SEDonline 704 is PWS, but the printed SED (I 78) has Akkadian and Hebrew and reads it as Proto-Semitic; the page follows the print",
    "Proto-Semitic_ʔiṣbaʕ-": "an existing Proto-Semitic page; SEDonline 739 is PWS, but the printed SED (I 256) has Akkadian neṣbettu and Eblaite",
    "Proto-West_Semitic_ʕigl-": "an existing Proto-West Semitic page; SEDonline 499 and the print (II 28, Eblaite) say PS, but the page stays PWS by the user's decision (2026-10-29)",
}
LEVEL = {r["rec_id"]: r["level"] for r in csv.DictReader(open(ROOT / "data" / "sedonline" / "sedonline_reconstructions.tsv", encoding="utf-8"), delimiter="\t")}

def our_files():
    for d in ("done", "merges"):
        yield from sorted((ROOT / "wiktionary_drafts" / d).glob("*.wiki"))

def refs(text):
    return [m.group(0) for m in REF.finditer(text)]

def rec_of(ref):
    m = re.search(r"\|\s*(?:id|e)\s*=\s*(\d+)", ref)
    return m.group(1) if m else None

def page_level(path):
    return "PWS" if path.name.startswith("Proto-West_Semitic_") else "PS"


class SedRefs(unittest.TestCase):
    def test_every_reference_links_sedonline(self):
        for f in our_files():
            for ref in refs(f.read_text(encoding="utf-8")):
                with self.subTest(page=f.stem, ref=ref):
                    self.assertIsNotNone(rec_of(ref), "no id=: the citation does not link to the SEDonline record")

    def test_page_level_is_the_seds(self):
        for f in our_files():
            for ref in refs(f.read_text(encoding="utf-8")):
                rec = rec_of(ref)
                if rec is None or LEVEL.get(rec) not in ("PS", "PWS"):
                    continue                                  # unlinked (the test above) or a record with no level of its own
                if f.stem in LEVEL_EXCEPTIONS:
                    continue
                with self.subTest(page=f.stem, rec=rec):
                    self.assertEqual(page_level(f), LEVEL[rec], f"SEDonline {rec} is {LEVEL[rec]}: the page belongs at that level")

    def test_the_calf_case(self):                         # what the check says about the page as it was
        self.assertEqual(LEVEL["499"], "PS")
        self.assertEqual(page_level(Path("Proto-West_Semitic_ʕigl-.wiki")), "PWS")


if __name__ == "__main__":
    unittest.main()
