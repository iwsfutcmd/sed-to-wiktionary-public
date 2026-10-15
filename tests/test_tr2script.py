"""Run: python3 tests/test_tr2script.py   (no network, no dependencies)"""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from tr2script import abjad, ethiopic
from paths import DATA

class Ethiopic(unittest.TestCase):
    def test_every_syllable_round_trips(self):
        table = json.loads((DATA / "scripts" / "ethi_translit.json").read_text(encoding="utf-8"))["table"]
        bad = [(ch, lat, ethiopic.convert("am", lat)) for ch, lat in table.items() if ethiopic.convert("am", lat) != ch]
        self.assertEqual(bad, [])
    def test_known_wiktionary_spellings(self):          # Reconstruction:Proto-Semitic/ʕaṯ̣m-: Ge'ez/Amharic/Tigrinya descendants and their tr=
        for lang, lat, ch in [("am", "ʿäṣ́m", "ዐፅም"), ("am", "ʿäṣm", "ዐጽም"), ("am", "ʾäṣm", "አጽም"), ("ti", "ʿaṣmi", "ዓጽሚ"), ("am", "ʾäṭənt", "አጥንት")]:
            self.assertEqual(ethiopic.convert(lang, lat), ch, lat)
    def test_source_conventions(self):                  # SEDonline spellings (ˁ, ˀ, ḵ, gemination written as a double letter)
        self.assertEqual(ethiopic.convert("am", "wärč"), "ወርች")
        self.assertEqual(ethiopic.convert("sgw", "wäččä"), "ወቸ")
        self.assertEqual(ethiopic.convert("ti", "wäräḵät"), "ወረኸት")
        self.assertEqual(ethiopic.convert("am", "aṭənt"), "አጥንት")      # Wiktionary Amharic entry for 'bone'
        self.assertEqual(ethiopic.convert("am", "aras"), "አራስ")
        self.assertEqual(ethiopic.convert("tig", "warkat"), "ዋርካት")
        self.assertEqual(ethiopic.convert("tig", "ˁaṣəm"), ethiopic.convert("tig", "ʿaṣəm"))
    def test_refuses_instead_of_guessing(self):
        self.assertIsNone(ethiopic.convert("gez", "ḥəfn"))          # no Ge'ez profile
        self.assertIsNone(ethiopic.convert("ti", "aṭənt"))          # Tigrinya has distinct ʾä and ʾa: initial a is ambiguous
        self.assertIsNone(ethiopic.convert("am", "arās"))           # length marks are not handled
        self.assertIsNone(ethiopic.convert("am", "wä rč"))
        self.assertIsNone(ethiopic.convert("am", "wärč1"))

class Abjad(unittest.TestCase):
    def test_spellings_that_exist_on_wiktionary(self):          # each is a live Wiktionary entry (checked with wikt_draft.py --verify)
        for code, lat, sc in [("syc", "ˀemmrā", "ܐܡܪܐ"), ("syc", "ṭabyā", "ܛܒܝܐ"), ("syc", "bāḳā", "ܒܩܐ"), ("uga", "ṯ̣by", "𐎑𐎁𐎊"),
                              ("uga", "mrṣ", "𐎎𐎗𐎕"), ("hbo", "mrṣ", "מרץ"), ("arc", "ˀmr", "אמר"), ("arc", "mrˁ", "מרע")]:
            self.assertEqual(abjad.convert(code, lat), sc, (code, lat))
    def test_matres_and_final_forms(self):
        self.assertEqual(abjad.convert("he", "yrk"), "ירך")              # final kaf
        self.assertEqual(abjad.convert("he", "yirkā"), "ירכא")           # final ā -> alef
        self.assertEqual(abjad.convert("arc", "yarḵāṯēh"), "ירכתה")      # spirantised ḵ ṯ -> כ ת
        self.assertEqual(abjad.convert("sam", "ṭby"), "ࠈࠁࠉ")
        self.assertEqual(abjad.convert("sam", "ṭabyā"), "ࠈࠁࠉࠀ")   # final ā -> alaf
    def test_turoyo_in_syriac_script(self):                       # Wiktionary Turoyo entry for 'mosquito' is titled ܒܩܐ
        self.assertEqual(abjad.convert("tru", "bōḳo"), "ܒܩܐ")
    def test_other_scripts(self):
        self.assertEqual(abjad.convert("xsa", "wrk"), "𐩥𐩧𐩫"); self.assertEqual(abjad.convert("sem-srb", "ṣby"), "𐩮𐩨𐩺")
        self.assertEqual(abjad.convert("phn", "ˀmr"), "𐤀𐤌𐤓")
    def test_known_limits(self):
        self.assertEqual(abjad.convert("uga", "ˀmr"), "𐎀𐎎𐎗")           # Wiktionary writes 𐎛𐎎𐎗 (ʾi): not recoverable from the consonants
        self.assertIsNone(abjad.convert("he", "qwm x")); self.assertIsNone(abjad.convert("ar", "wrk")); self.assertIsNone(abjad.convert("he", "z1"))

if __name__ == "__main__":
    unittest.main(verbosity=1)
