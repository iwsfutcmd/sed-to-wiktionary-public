"""Language codes used in the Wiktionary drafts: code -> (name as Wiktionary renders it, scripts its terms may be in, section headings
its entries appear under). Names are re-verified live by tests/test_drafts.py (ONLINE=1)."""
import re, unicodedata as U

LANGS = {
 "akk": ("Akkadian", {"Latin", "Cuneiform"}), "xeb": ("Eblaite", {"Latin"}), "ar": ("Arabic", {"Arabic"}),
 "arc": ("Aramaic", {"Hebrew"}), "jpa": ("Jewish Palestinian Aramaic", {"Hebrew"}), "tmr": ("Jewish Babylonian Aramaic", {"Hebrew"}),
 "sam": ("Samaritan Aramaic", {"Samaritan"}), "syc": ("Classical Syriac", {"Syriac"}), "myz": ("Classical Mandaic", {"Mandaic"}),
 "tru": ("Turoyo", {"Syriac"}), "aii": ("Assyrian Neo-Aramaic", {"Syriac", "Latin"}), "amw": ("Western Neo-Aramaic", {"Latin"}), "hbo": ("Biblical Hebrew", {"Hebrew"}), "he": ("Hebrew", {"Hebrew"}),
 "phn": ("Phoenician", {"Phoenician"}), "uga": ("Ugaritic", {"Ugaritic"}), "xsa": ("Sabaean", {"Old South Arabian"}),
 "sem-srb": ("Old South Arabian", {"Old South Arabian"}), "gez": ("Ge'ez", {"Ethiopic"}), "tig": ("Tigre", {"Ethiopic"}),
 "ti": ("Tigrinya", {"Ethiopic"}), "am": ("Amharic", {"Ethiopic"}), "agj": ("Argobba", {"Ethiopic"}), "har": ("Harari", {"Ethiopic"}),
 "gft": ("Gafat", {"Ethiopic"}), "stv": ("Silt'e", {"Ethiopic"}), "wle": ("Wolane", {"Ethiopic"}), "zwa": ("Zay", {"Ethiopic"}),
 "gru": ("Kistane", {"Ethiopic"}), "sgw": ("Sebat Bet Gurage", {"Ethiopic"}), "mvz": ("Mesqan", {"Ethiopic"}),
 "gdq": ("Mehri", {"Latin"}), "shv": ("Shehri", {"Latin"}), "hss": ("Harsusi", {"Latin"}), "bhm": ("Bathari", {"Latin"}), "sqt": ("Soqotri", {"Latin"})}
RANGES = [("Hebrew", 0x590, 0x5FF), ("Arabic", 0x600, 0x6FF), ("Syriac", 0x700, 0x74F), ("Arabic", 0x750, 0x77F), ("Samaritan", 0x800, 0x83F),
          ("Mandaic", 0x840, 0x85F), ("Ethiopic", 0x1200, 0x139F), ("Ethiopic", 0x2D80, 0x2DDF), ("Ethiopic", 0xAB00, 0xAB2F),
          ("Arabic", 0xFB50, 0xFDFF), ("Arabic", 0xFE70, 0xFEFF), ("Ugaritic", 0x10380, 0x1039F), ("Phoenician", 0x10900, 0x1091F),
          ("Old South Arabian", 0x10A60, 0x10A7F), ("Cuneiform", 0x12000, 0x1254F)]

# Section heading(s) a lemma of that language sits under on en.wiktionary.org
SECTIONS = {"hbo": ["Hebrew", "Biblical Hebrew"], "he": ["Hebrew"], "arc": ["Aramaic"], "xsa": ["Sabaean"], "sem-srb": ["Old South Arabian"]}
def sections(code):
    return SECTIONS.get(code) or [LANGS[code][0]]

def strip_marks(t):
    """The title of a Wiktionary entry is the spelling without vowel marks (Hebrew niqqud, Arabic tashkil, Syriac points)."""
    return "".join(c for c in U.normalize("NFC", t) if not (0x591 <= ord(c) <= 0x5C7 or 0x64B <= ord(c) <= 0x652 or ord(c) in (0x670, 0x651)
                                                           or 0x730 <= ord(c) <= 0x74A))
