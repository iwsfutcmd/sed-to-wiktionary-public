"""Offline tests of scripts/wikt_fix_refs.py (the reference respeller).   Run: python3 tests/test_fix_refs.py

fix_text() decides every edit, so it is tested hardest: it must change the TERM of a reconstruction reference and nothing else."""
import json, sys, tempfile, unittest, unicodedata as U
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import wikt_fix_refs as F

M = {("PS", "ʾab-"): "ʔab-", ("PS", "ʿayn-"): "ʕayn-", ("PWS", "qarn-"): "ḳarn-", ("PS", "θ̣aby-"): "ṯ̣aby-", ("PS", "ṣ̂-"): "ṣ́-"}
def fix(t, m=M):
    return F.fix_text(t, m)[0]

class Templates(unittest.TestCase):
    def test_inh_cog_m_l_desc(self):
        for before, after in [("{{inh|ar|sem-pro|*ʾab-|t=father}}", "{{inh|ar|sem-pro|*ʔab-|t=father}}"),
                              ("{{inh+|he|sem-pro|*ʾab-}}", "{{inh+|he|sem-pro|*ʔab-}}"),
                              ("{{der|en|sem-pro|*ʾab-||x}}", "{{der|en|sem-pro|*ʔab-||x}}"),
                              ("{{cog|sem-pro|*ʿayn-<id:eye>}}", "{{cog|sem-pro|*ʕayn-<id:eye>}}"),
                              ("{{m|sem-pro|ʾab-}}", "{{m|sem-pro|ʔab-}}"),                      # no asterisk
                              ("{{l|sem-pro||*ʾab-|pos=masculine}}", "{{l|sem-pro||*ʔab-|pos=masculine}}"),
                              ("{{desc|sem-pro|*ʾab-}}", "{{desc|sem-pro|*ʔab-}}")]:
            self.assertEqual(fix(before), after)
    def test_ety_chain(self):
        self.assertEqual(fix("{{ety|ar|:inh|sem-pro:*ʾab-}}"), "{{ety|ar|:inh|sem-pro:*ʔab-}}")
    def test_wikilink(self):
        self.assertEqual(fix("[[Reconstruction:Proto-Semitic/ʾab-]]"), "[[Reconstruction:Proto-Semitic/ʔab-]]")
        self.assertEqual(fix("[[Reconstruction:Proto-Semitic/ʾab-|*ʾab-]]"), "[[Reconstruction:Proto-Semitic/ʔab-|*ʔab-]]")
        self.assertEqual(fix("[[Reconstruction:Proto-Semitic/ʾab-|the father]]"), "[[Reconstruction:Proto-Semitic/ʔab-|the father]]")
        self.assertEqual(fix("[[Reconstruction:Proto-West Semitic/qarn-]]"), "[[Reconstruction:Proto-West Semitic/ḳarn-]]")
    def test_nested_and_piped(self):
        t = "{{inh|ar|sem-pro|*ʾab-|t=[[father|dad]]}} {{foo|{{inh|he|sem-pro|*ʿayn-}}|x}}"
        self.assertEqual(fix(t), "{{inh|ar|sem-pro|*ʔab-|t=[[father|dad]]}} {{foo|{{inh|he|sem-pro|*ʕayn-}}|x}}")
    def test_piped_link_before_the_term(self):
        self.assertEqual(fix("{{l|sem-pro|[[a|b]]|*ʾab-}}"), "{{l|sem-pro|[[a|b]]|*ʔab-}}")
    def test_unicode_forms(self):
        self.assertEqual(fix("{{inh|ar|sem-pro|*" + U.normalize("NFD", "θ̣aby-") + "}}"), "{{inh|ar|sem-pro|*ṯ̣aby-}}")
        self.assertEqual(fix("{{m|sem-pro|*ṣ̂-}}"), "{{m|sem-pro|*ṣ́-}}")

class Untouched(unittest.TestCase):
    def same(self, t):
        self.assertEqual(fix(t), t)
    def test_other_languages_and_levels(self):
        self.same("{{inh|he|sem-wes-pro|*ʾab-}}")                 # PS spelling in a PWS reference: another page
        self.same("{{inh|ar|sem-pro|*qarn-}}")                    # PWS key, PS context
        self.same("{{m|he|ʾab-}}")                                # Hebrew term
        self.same("{{m|ar|*ʾab-}}")
    def test_only_the_term(self):
        self.same("{{inh|ar|sem-pro|*ʔab-|tr=ʾab-|t=ʾab- father}}")
        self.same("{{R:sem-pro:SED|volume=I|id=1|entry=*ʾab-}}")  # quotes a source
        self.same("{{inh|ar|sem-pro|alt=*ʾab-|*ʔab-}}")           # named parameter
        self.same("From ʾab- 'father'.")                          # running text
        self.same("{{m|sem-pro|*ʾab-ʾab-}}")                      # a different stem
        self.same("{{inh|ar|sem-pro|*{{foo|ʾab-}}}}")             # term built by another template
    def test_idempotent_and_exact(self):
        t = "{{inh|ar|sem-pro|*ʾab-}} {{cog|sem-pro|*ʿayn-}} [[Reconstruction:Proto-Semitic/ʾab-]] {{ety|x|:inh|sem-pro:*ʾab-}}"
        once, ch = F.fix_text(t, M)
        self.assertEqual(len(ch), 4)
        self.assertEqual(F.fix_text(once, M), (once, []))
        self.assertEqual({k for k, _, _ in ch}, {"term", "ety", "link"})

class Mapping(unittest.TestCase):
    def test_pure_respellings_only(self):
        m, person, pages = F.load_mapping()
        self.assertEqual(m[("PS", "baʿl-")], "baʕl-")
        self.assertEqual(m[("PS", "waraq-")] if ("PS", "waraq-") in m else None, "waraḳ-")
        self.assertNotIn(("PS", "ʾab-"), m)                       # ʾab- redirects to the stem ʔabw-: a person decides
        self.assertIn(("PS", "ʾab-"), {(l, t) for l, t, _ in person})
        for (lv, bad), good in m.items():
            self.assertNotEqual(bad, good)
            self.assertEqual(F.nfc(F.standardise(bad)[0]), good, (bad, good))      # never anything but the standard spelling of the same stem

class Apply(unittest.TestCase):
    """The editing loop, against a fake API: nothing is written without a y, an edit since the plan is recomputed, results are logged."""
    class Fake:
        def __init__(self, live):
            self.live, self.edits, self.logged_in = live, [], False
        def login(self, u, p): self.logged_in = True
        def pages(self, titles): return {t: self.live[t] for t in titles if t in self.live}
        def edit(self, title, text, summary, baserevid, bot=False):
            self.edits.append((title, text, summary, baserevid, bot)); return dict(edit=dict(result="Success", newrevid=baserevid + 1))
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.old = F.OUT; F.OUT = Path(self.tmp.name)
        text = "{{inh|ar|sem-pro|*ʾab-}}"
        items = [dict(title=t, revid=1, timestamp="x", old=text, new=fix(text), changes=[("term", "ʾab-", "ʔab-")]) for t in ("A", "B", "C")]
        (F.OUT / "plan.json").write_text(json.dumps(dict(mapping=[[lv, b, g] for (lv, b), g in M.items()], items=items), ensure_ascii=False), encoding="utf-8")
        self.live = {t: (1, "x", text) for t in ("A", "B", "C")}
        import os; os.environ["WIKT_PASSWORD"] = "x"
    def tearDown(self):
        F.OUT = self.old; self.tmp.cleanup()
    def run_apply(self, answers, live=None, **kw):
        api = self.Fake(live or self.live); it = iter(answers)
        F.apply("U", api=api, ask=lambda _: next(it), pause=0, out=lambda *_: None, **kw)
        return api
    def test_yes_no(self):
        api = self.run_apply(["y", "n", "y"])
        self.assertEqual([e[0] for e in api.edits], ["A", "C"])
        self.assertTrue(api.logged_in)
        self.assertEqual(api.edits[0][1], "{{inh|ar|sem-pro|*ʔab-}}")
        self.assertIn("*ʾab- → *ʔab-", api.edits[0][2]); self.assertIn("semi-automated", api.edits[0][2])
    def test_quit_and_all(self):
        self.assertEqual([e[0] for e in self.run_apply(["y", "q"]).edits], ["A"])
    def test_all_the_rest(self):
        self.assertEqual([e[0] for e in self.run_apply(["a"]).edits], ["A", "B", "C"])
    def test_resumes_without_repeating(self):
        self.run_apply(["y", "q"])
        self.assertEqual([e[0] for e in self.run_apply(["a"]).edits], ["B", "C"])
    def test_edited_since_the_plan(self):
        live = dict(self.live); live["B"] = (7, "y", "{{inh|ar|sem-pro|*ʾab-}} and a new line")
        api = self.run_apply(["y", "y", "y"], live=live)
        b = [e for e in api.edits if e[0] == "B"][0]
        self.assertEqual((b[1], b[3]), ("{{inh|ar|sem-pro|*ʔab-}} and a new line", 7))      # recomputed from the live text, based on the live revision
    def test_already_fixed_by_hand(self):
        live = dict(self.live); live["A"] = (9, "y", "{{inh|ar|sem-pro|*ʔab-}}")
        api = self.run_apply(["a"], live=live)
        self.assertEqual([e[0] for e in api.edits], ["B", "C"])

if __name__ == "__main__":
    unittest.main(verbosity=1)
