"""Offline tests of scripts/wikt_asem_check.py: the parser-based detector and the edit-filter regular expression.   Run: python3 tests/test_asem_check.py

Both must flag a Proto-Semitic reference whose term uses a variant character (ʾ ʿ q θ ṣ̂ ŝ ɣ ...), and neither may fire on tr=, t=, entry=, other languages,
Proto-Afroasiatic terms, or the standard notation. The regex is also run through Perl (a PCRE engine) and, if build/asem_corpus.json is there (fetched by
wikt_asem_check.py's corpus step, 1329 live pages), compared with the parser on every page."""
import json, shutil, subprocess, sys, tempfile, unittest, unicodedata as U
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import wikt_asem_check as A

BAD = [
    "{{inh|ar|sem-pro|*ʾab-}}", "{{inh|ar|sem-pro|*ʿayn-|t=eye}}", "{{cog|sem-pro|*qarn-}}", "{{m|sem-pro|*θalg-}}", "{{m|sem-pro|*θ̣aby-}}", "{{m|sem-pro|*ṱill-}}",
    "{{m|sem-pro|*maraṣ̂-}}", "{{m|sem-pro|*ŝaḥm-}}", "{{m|sem-pro|*ṣaɣir-}}", "{{m|sem-pro|*ðikar-}}", "{{m|sem-pro|*ḍabuʕ-}}", "{{m|sem-pro|*x̣arb-}}", "{{m|sem-pro|*čaʕlab-}}",
    "{{der|aii|sem-pro|*qyẓ}}",                                                      # ẓ (ẓ ~ Arabic ظ, Hebrew ץ): another spelling of the interdental emphatic, for ṯ̣

    "{{desc|sem-pro|*ʾab-}}", "{{l|sem-pro||*ʾab-}}", "{{der|en|sem-pro|*baʿl-||owner}}", "{{inh+|he|sem-wes-pro|*qarn-}}",
    "{{inh|amw|sem-pro|*šabʕ-|*šabʿum}}",                                           # an alternative form shown with the term
    "{{ety|ar|:inh|sem-pro:*ʾab-}}", "{{ety|ota|:bor|ar:x<ety:uder<sem-pro:*maraṣ̂-<t:to be ill>>>|text=2}}",
    "[[Reconstruction:Proto-Semitic/ʾab-]]", "[[Reconstruction:Proto-West Semitic/qarn-|*qarn-]]",
    "{{m|sem-pro|*" + U.normalize("NFD", "θ̣aby-") + "}}",
    "{{sem-pro-conj/*paʕala-*yipʕal|m|r|ṣ̂|vn=marṣ́}}", "{{sem-pro-conj/*paʕala-*yipʕal|ʾ|b|d|vn=ʔbd}}", "{{sem-pro-conj/*paʕala-*yipʕal|r|p|ʔ|vn=rpʾ}}",     # the root letters of a conjugation table
]
GOOD = [
    "{{inh|ar|sem-pro|*ʔab-}}", "{{inh|ar|sem-pro|*ʕayn-|t=eye}}", "{{cog|sem-pro|*ḳarn-}}", "{{m|sem-pro|*ṯalg-}}", "{{m|sem-pro|*ṯ̣aby-}}", "{{m|sem-pro|*maraṣ́-}}", "{{m|sem-pro|*śaḥm-}}",
    "{{m|sem-pro|*ṣaḡir-}}", "{{m|sem-pro|*ḏikar-}}", "{{m|sem-pro|*bV-}}", "{{m|sem-pro|*šaḥ(a)r-}}", "{{m|sem-pro|*sₓawm-}}",
    "{{inh|ar|sem-pro|*ʔab-|tr=ʾab-|t=ʿayn father}}",                                # the transliteration and the gloss are not the reconstruction
    "{{R:sem-pro:SED|volume=I|id=1|entry=*ʾab-}}",                                    # quotes a source
    "{{m|he|ʾab-}} {{inh|he|arc|ʾab-}} {{m|ar|*qarn-}}",                              # other languages
    "{{inh|sem-pro|afa-pro|*sṗɣ||seven}}", "{{der|sem-pro|akk|*ʾab-}}", "{{ety|x|afa-pro:*ʾab-}}",          # Proto-Semitic as the language that inherits
    "{{sem-pro-conj/*paʕala-*yipʕal|m|r|ṣ́|vn=marṣ́}}", "{{sem-pro-conj/*paʕala-*yipʕal|ʔ|b|d|vn=ʔbd}}",
    "{{af|ar|sem-pro|*ʾab-}}", "From ʾab- 'father'.", "", "[[Reconstruction:Proto-Dravidian/appa]]",
]

class Parser(unittest.TestCase):
    def test_flags(self):
        for t in BAD:
            self.assertTrue(A.structural(t), t)
    def test_leaves_alone(self):
        for t in GOOD:
            self.assertEqual(A.structural(t), [], t)
    def test_reports_the_standard_spelling(self):
        self.assertEqual(A.structural("{{m|sem-pro|*ʾab-}}"), [("term", "ʾab-", "ʔab-")])
        self.assertEqual(A.structural("{{m|sem-pro|*θ̣aby-}}"), [("term", "θ̣aby-", "ṯ̣aby-")])
        self.assertEqual(A.structural("{{der|aii|sem-pro|*qyẓ}}"), [("term", "qyẓ", "ḳyṯ̣")])
        self.assertEqual(A.structural("{{sem-pro-conj/*paʕala-*yipʕal|m|r|ṣ̂|vn=marṣ́}}"), [("conj", "ṣ̂", "ṣ́")])

class Regex(unittest.TestCase):
    def test_flags(self):
        for t in BAD:
            self.assertTrue(A.regex_hits(t), t)
    def test_leaves_alone(self):
        for t in GOOD:
            self.assertEqual(A.regex_hits(t), [], t)
    def test_known_limit_nested_templates(self):
        # a term built inside another template is invisible to a regular expression (the parser does not read it either)
        self.assertEqual(A.regex_hits("{{inh|ar|sem-pro|*{{foo|ʾab-}}}}"), [])
    @unittest.skipUnless(shutil.which("perl"), "perl is not installed")
    def test_pcre_form_agrees_with_python(self):
        with tempfile.TemporaryDirectory() as d:
            files = []
            for i, t in enumerate(BAD + GOOD):
                f = Path(d) / f"{i}.txt"; f.write_text(t, encoding="utf-8"); files.append((f, t in BAD))
            (Path(d) / "t.pl").write_text(r'use utf8; binmode(STDOUT,":utf8"); my $re = qr/%s/u; for my $f (@ARGV) { open(my $h,"<:encoding(UTF-8)",$f); local $/; my $t=<$h>; print "$f\t", ($t =~ $re ? 1 : 0), "\n"; }'
                                          % A.FILTER_PCRE.replace("/", "\\/"), encoding="utf-8")
            r = subprocess.run(["perl", str(Path(d) / "t.pl")] + [str(f) for f, _ in files], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = {l.split("\t")[0]: l.split("\t")[1].strip() == "1" for l in r.stdout.splitlines()}
            for f, expected in files:
                self.assertEqual(got[str(f)], expected, f.read_text(encoding="utf-8"))

class Corpus(unittest.TestCase):
    def test_agree_on_live_pages(self):
        f = ROOT / "build" / "asem_corpus.json"
        if not f.exists():
            self.skipTest("no corpus (build/asem_corpus.json)")
        corpus = json.loads(f.read_text(encoding="utf-8"))
        disagree = [t for t, x in corpus.items() if bool(A.structural(x)) != bool(A.regex_hits(x))]
        self.assertEqual(disagree, [], f"{len(disagree)} of {len(corpus)} pages")

if __name__ == "__main__":
    unittest.main(verbosity=1)
