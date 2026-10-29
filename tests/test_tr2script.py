"""Run: python3 tests/test_tr2script.py   (no network, no dependencies)"""
import json, os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from tr2script import abjad, arabic, ethiopic, mandaic, readings, same_spelling
from paths import DATA

class Variants(unittest.TestCase):
    def test_readings(self):
        self.assertEqual(readings("šuš(š)"), ["šuš", "šušš"])
        self.assertEqual(readings("mwt/myt"), ["mwt", "myt"])
        self.assertEqual(readings("(h)arb"), ["arb", "harb"])
        self.assertEqual(readings("šḳy (aph.)"), ["šḳy (aph.)"])          # prose: left alone (and refused by the converters)
        self.assertEqual(readings("sūs"), ["sūs"])
    def test_same_spelling(self):
        am = lambda f: ethiopic.convert("am", f)
        self.assertEqual(same_spelling(am, "šuš(š)"), "ሹሽ")               # gemination unwritten: both readings ሹሽ
        self.assertIsNone(same_spelling(lambda f: ethiopic.convert("tig", f), "ḥāl/ḥal"))      # one reading not convertible: refuse
        self.assertEqual(ethiopic.convert("am", "əǯǯ"), "እጅ")                                  # SED ǯ = Wiktionary ǧ (Amharic እጅ 'hand')
        self.assertIsNone(same_spelling(am, "(a)dāmäsä"))                  # readings spelled differently: refuse
        self.assertIsNone(same_spelling(lambda f: abjad.convert("arc", f), "mwt/myt"))
        self.assertEqual(same_spelling(lambda f: abjad.convert("he", f), "nāˀ/nā"), "נא")      # final ā is written alef: both נא
        self.assertIsNone(same_spelling(lambda f: abjad.convert("arc", f), "ˀa/immar-"))   # partial slash: fragments never agree

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
        self.assertEqual(ethiopic.convert("har", "sūs"), "ሱስ")           # Harari length unwritten (Wiktionary ሙዝ = mūz)
        self.assertEqual(ethiopic.convert("har", "mūz"), "ሙዝ")
        self.assertEqual(ethiopic.convert("har", "ḥäǧīs"), "ሐጂስ")
        self.assertEqual(ethiopic.convert("tig", "warkat"), "ዋርካት")
        self.assertEqual(ethiopic.convert("tig", "ˁaṣəm"), ethiopic.convert("tig", "ʿaṣəm"))
    def test_refuses_instead_of_guessing(self):
        # Ge'ez (Leslau): a = ä, ā = a; each of these is a Wiktionary Ge'ez entry at this spelling (checked against the live pages)
        for lat, sc in [("kalb", "ከልብ"), ("ˀəzn", "እዝን"), ("ḥaddis", "ሐዲስ"), ("ŝāˁr", "ሣዕር"), ("ˁayn", "ዐይን"), ("ˁəṣ̂", "ዕፅ"), ("ṣəfr", "ጽፍር"),
                        ("samˁa", "ሰምዐ"), ("lelit", "ሌሊት"), ("warḳ", "ወርቅ")]:
            self.assertEqual(ethiopic.convert("gez", lat), sc, lat)
        self.assertEqual(ethiopic.convert("gez", "kəśād"), "ክሣድ")
        self.assertIsNone(ethiopic.convert("gez", "ˀanḳe, ˀanḳet"))
        self.assertIsNone(ethiopic.convert("ti", "aṭənt"))          # Tigrinya has distinct ʾä and ʾa: initial a is ambiguous
        self.assertEqual(ethiopic.convert("stv", "arās"), ethiopic.convert("am", "aras"))   # long ā = fourth order in Amharic-type sources
        self.assertIsNone(ethiopic.convert("ti", "ʕaṣmā"))          # Tigrinya/Tigre: length marks are not handled
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
        self.assertEqual(abjad.convert("hbo", "sās"), "סס")             # two radicals with a vowel between: not gemination
        self.assertEqual(abjad.convert("syc", "sāsā"), "ܣܣܐ")
        self.assertEqual(abjad.convert("arc", "ss"), "סס")              # bare root keeps both radicals
        self.assertEqual(abjad.convert("syc", "baqqā"), "ܒܩܐ")           # real gemination still written once
        self.assertEqual(abjad.convert("arc-old", "pgr"), "𐤐𐤂𐤓")           # Old Aramaic: Phoenician letters
        self.assertEqual(abjad.convert("arc-off", "gldʔ"), "𐡂𐡋𐡃𐡀")         # Official Aramaic: Imperial Aramaic
        self.assertEqual(abjad.convert("arc-pal", "nbl"), "\U0001086E\U00010861\U0001086B")    # Palmyrene medial nun
        self.assertEqual(abjad.convert("arc-nab", "prš"), "\U00010897\U0001089A\U0001089C")    # Nabataean, plain (not final) shin
        self.assertEqual(abjad.convert("xsa", "frs₁"), "𐩰𐩧𐩪")                                 # Old South Arabian s₁ = 𐩪 (Wiktionary s¹)
        self.assertEqual(abjad.convert("sem-srb", "ˀfrs₁n"), "𐩱𐩰𐩧𐩪𐩬")
        self.assertEqual(abjad.convert("arc-pal", "bn"), "\U00010861\U0001086D")               # ... and final nun
        self.assertEqual(abjad.convert("sam", "ṭabyā"), "ࠈࠁࠉࠀ")   # final ā -> alaf
    def test_refuses_when_matres_would_be_needed(self):
        for code, lat in [("syc", "ˁurṭē"), ("syc", "ṭūrā"), ("he", "ˁōp"), ("he", "ṣəbī"), ("syc", "bōḳo"), ("tmr", "ˁūpā")]:
            self.assertIsNone(abjad.convert(code, lat), (code, lat))
        self.assertEqual(abjad.convert("syc", "ˁurṭāyā"), None)                 # internal u
        self.assertEqual(abjad.convert("arc", "yarḵāṯēh"), "ירכתה")            # internal ē, final h: fine
    def test_other_scripts(self):
        self.assertEqual(abjad.convert("xsa", "wrk"), "𐩥𐩧𐩫"); self.assertEqual(abjad.convert("sem-srb", "ṣby"), "𐩮𐩨𐩺")
        self.assertEqual(abjad.convert("phn", "ˀmr"), "𐤀𐤌𐤓")
    def test_known_limits(self):
        self.assertEqual(abjad.convert("uga", "ˀmr"), "𐎀𐎎𐎗")           # Wiktionary writes 𐎛𐎎𐎗 (ʾi): not recoverable from the consonants
        self.assertIsNone(abjad.convert("he", "qwm x")); self.assertIsNone(abjad.convert("ar", "wrk")); self.assertIsNone(abjad.convert("he", "z1"))

class Arabic(unittest.TestCase):
    PAIRS = [("warik-", "وَرِك"), ("baqq-", "بَقّ"), ("ḏ̣aby-", "ظَبْي"), ("ẓaby-", "ظَبْي"), ("šaḥm-", "شَحْم"), ("šaḥuma", "شَحُمَ"), ("ḫarūs-", "خَرُوس"),
             ("kalb-", "كَلْب"), ("bayt-", "بَيْت"), ("ṯawr-", "ثَوْر")]
    def test_vocalised_stems(self):                     # the first seven are spellings used (and found on Wiktionary) in the drafts
        for lat, ar in self.PAIRS:
            self.assertEqual(arabic.convert(lat), ar, lat)
    def test_refuses_instead_of_guessing(self):
        for lat in ["nyk", "ḍrṭ", "ˀab-", "ʔabb-", "ab-", "kalbā", "kalbī", "ʕaṯm(-at)-", "ka/lb", "kalb, kalab", "wū", ""]:
            self.assertIsNone(arabic.convert(lat), lat)
    def test_sukun_not_on_the_last_letter(self):
        self.assertFalse(arabic.convert("kalb-").endswith("\u0652")); self.assertTrue(arabic.convert("kalb-").startswith("كَ"))

@unittest.skipUnless(os.environ.get("ONLINE"), "set ONLINE=1: round trip through Wiktionary's own Arabic transliteration")
class ArabicOracle(unittest.TestCase):
    def test_round_trip_through_wiktionary(self):
        import json, re, urllib.parse, urllib.request
        scripts = [(lat, ar) for lat, ar in Arabic.PAIRS]
        text = "\n".join(f"* {{{{desc|ar|{ar}}}}}" for _, ar in scripts)
        data = urllib.parse.urlencode(dict(format="json", formatversion=2, action="parse", title="Reconstruction:Proto-Semitic/x", text=text,
                                           prop="text", contentmodel="wikitext", disablelimitreport=1)).encode()
        html = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data,
                         headers={"User-Agent": "sed-to-wiktionary/1.0 (research)"}), timeout=30))["parse"]["text"]
        trs = re.findall(r"Arabic: [^(]*\(([^)]*)\)", re.sub(r"<[^>]+>", "", re.sub(r"<style.*?</style>", "", html, flags=re.S)))
        self.assertEqual(len(trs), len(scripts), trs)
        for (lat, ar), tr in zip(scripts, trs):
            want = lat.rstrip("-").replace("ḏ̣", "ẓ").replace("ḫ", "ḵ")      # Wiktionary writes خ as ḵ, the SED as ḫ
            self.assertEqual(tr, want, f"{ar}: Wiktionary reads it as {tr!r}, we meant {lat!r}")

if __name__ == "__main__":
    unittest.main(verbosity=1)


class Mandaic(unittest.TestCase):
    def test_wiktionary_entries(self):
        """Each of these is a Wiktionary Classical Mandaic entry whose title is exactly the script produced (checked against the live pages)."""
        for lat, sc in [("pagra", "ࡐࡀࡂࡓࡀ"), ("kul", "ࡊࡅࡋ"), ("nuna", "ࡍࡅࡍࡀ"), ("liba", "ࡋࡉࡁࡀ"), ("šuma", "ࡔࡅࡌࡀ"), ("ṣipra", "ࡑࡉࡐࡓࡀ"),
                        ("arḳa", "ࡀࡓࡒࡀ"), ("gabra", "ࡂࡀࡁࡓࡀ"), ("ṭab", "ࡈࡀࡁ"), ("tlata", "ࡕࡋࡀࡕࡀ"), ("daura", "ࡃࡀࡅࡓࡀ")]:
            self.assertEqual(mandaic.convert("myz", lat), sc, lat)
            self.assertEqual(mandaic.translit(sc), lat.replace("ḳ", "q"))
    def test_refusals(self):
        for lat in ["ḥamara", "ˀbra", "kulla", "nkt", "hrš", "b-", "dma, zma", "ġ", "baita "]:
            self.assertIsNone(mandaic.convert("myz", lat), lat)
        self.assertIsNone(mandaic.convert("ar", "pagra"))
    def test_inverse_of_wiktionarys_table(self):
        """Every letter the converter writes is read back as the same letter by Wiktionary's module (up to ˁ/ʿ, i/y, u/w, ḳ/q)."""
        for ch, lat in mandaic.TT.items():
            if lat in ("ẖ", "ḏ-", "kḏ", "ʕ", "a", "i", "u"):      # letters the converter does not write from the SED transcription / vowels
                continue
            src = "ˁ" if lat == "ʿ" else lat
            self.assertEqual(mandaic.convert("myz", "a" + src + "a"), "ࡀ" + ch + "ࡀ", lat)
