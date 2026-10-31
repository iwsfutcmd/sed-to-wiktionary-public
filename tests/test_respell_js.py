"""The in-browser respeller (scripts/respell_core.js) must give exactly the text of the tested Python fix_text().   Run: python3 tests/test_respell_js.py
Needs node; skipped without it. Real pages: tests/data/respell_pages.json (20 pages planned on 2026-10-16, with the Python result)."""
import json, shutil, subprocess, sys, unicodedata as U, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import wikt_fix_refs as F

M = {("PS", "ʾab-"): "ʔab-", ("PS", "ʿayn-"): "ʕayn-", ("PWS", "qarn-"): "ḳarn-", ("PS", "θ̣aby-"): "ṯ̣aby-", ("PS", "ṣ̂-"): "ṣ́-", ("PS", "waraq-"): "waraḳ-"}
SYNTH = [
    "{{inh|ar|sem-pro|*ʾab-|t=father}} {{inh+|he|sem-pro|*ʾab-}} {{der|en|sem-pro|*ʾab-||x}} {{cog|sem-pro|*ʿayn-<id:eye>}} {{m|sem-pro|ʾab-}}",
    "{{l|sem-pro||*ʾab-|pos=masculine}} {{desc|sem-pro|*ʾab-}} {{ety|ar|:inh|sem-pro:*ʾab-}} {{ety|ar|:inh|sem-pro:*ʾab-<id:x>}}",
    "[[Reconstruction:Proto-Semitic/ʾab-]] [[Reconstruction:Proto-Semitic/ʾab-|*ʾab-]] [[Reconstruction:Proto-Semitic/ʾab-|the father]] [[Reconstruction:Proto-West Semitic/qarn-|qarn-]]",
    "{{inh|ar|sem-pro|*ʾab-|t=[[father|dad]]}} {{foo|{{inh|he|sem-pro|*ʿayn-}}|x}} {{l|sem-pro|[[a|b]]|*ʾab-}}",
    "{{inh|ar|sem-pro|*" + U.normalize("NFD", "θ̣aby-") + "}} {{m|sem-pro|*ṣ̂-}}",
    "{{inh|he|sem-wes-pro|*ʾab-}} {{inh|ar|sem-pro|*qarn-}} {{m|he|ʾab-}} {{m|ar|*ʾab-}} {{inh|ar|sem-wes-pro|*qarn-}}",
    "{{inh|ar|sem-pro|*ʔab-|tr=ʾab-|t=ʾab- father}} {{R:sem-pro:SED|volume=I|id=1|entry=*ʾab-}} {{inh|ar|sem-pro|alt=*ʾab-|*ʔab-}} From ʾab- 'father'. {{m|sem-pro|*ʾab-ʾab-}} {{inh|ar|sem-pro|*{{foo|ʾab-}}}}",
    "{{inh|sem-pro|afa-pro|*ʾab-}} {{der|sem-pro|akk|*ʾab-}} {{af|ar|sem-pro|*ʾab-}} {{R:sem-pro:SED|entry=*ʾab-}}",
    "{{inh|amw|sem-pro|*ʿayn-|*ʿayn-um}} {{m|sem-pro|*ʾab-|*ʾab-um|t=x}} {{l|sem-pro||*ʾab-}}",
    "{{ety|ota|:bor|ar:x<ety:uder<sem-pro:*ʾab-<t:to be>>>|text=2|tree=1}} {{ety|ar|:inh|sem-pro:*ʿayn-|text=+}} {{ety|x|afa-pro:*ʾab-}}",
    "", "no templates at all ʾab-", "{{unclosed|sem-pro|*ʾab-", "}} stray {{m|sem-pro|*ʾab-}}",
    "{{inh|ar|sem-pro|id=x|*ʾab-|t=x}}\n{{inh|ar|sem-pro|*waraq-}}\n[[Reconstruction:Proto-Semitic/waraq-]]",
]

@unittest.skipUnless(shutil.which("node"), "node is not installed")
class SamePythonAndJs(unittest.TestCase):
    def js(self, cases, mapping, generic=False):
        m = {f"{lv}\t{b}": g for (lv, b), g in mapping.items()}
        code = ("const R=require(process.argv[1]);let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{const j=JSON.parse(s);R.setNotation(j.variants,j.manual,j.consonants);"
                "console.log(JSON.stringify(j.cases.map(t=>R.fixText(t,j.mapping,j.generic))));});")
        notation = dict(variants=[[F.nfc(a), F.nfc(b)] for a, b in F.VARIANTS], manual=[F.nfc(x) for x in F.MANUAL], consonants=F.CONSONANTS)
        r = subprocess.run(["node", "-e", code, str(ROOT / "scripts" / "respell_core.js")], input=json.dumps(dict(cases=cases, mapping=m, generic=generic, **notation)), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)
    def test_synthetic(self):
        for text, got in zip(SYNTH, self.js(SYNTH, M)):
            new, ch = F.fix_text(text, M)
            self.assertEqual(got["text"], new, text)
            self.assertEqual([tuple(c) for c in got["changes"]], [tuple(c) for c in ch], text)
    def test_other_level(self):                  # "PWS:stem" moves the term and its language code; JS must agree with Python
        mp = {("PS", "ṣ́abb-"): "PWS:ṣ́abb-", ("PS", "ṣ̂abb-"): "PWS:ṣ́abb-"}
        cases = ["{{der|id|sem-pro|*ṣ́abb-}} {{inh|he|sem-pro|*ṣ̂abb-}} {{ety|ar|:inh|sem-pro:*ṣ́abb-|text=+}} {{l|sem-pro|*ṣ́abb-|t=x}}",
                 "[[Reconstruction:Proto-Semitic/ṣ́abb-|*ṣ́abb-]] [[Reconstruction:Proto-Semitic/ṣ̂abb-]] {{inh|ar|sem-wes-pro|*ṣ́abb-}}"]
        for text, got in zip(cases, self.js(cases, mp)):
            new, ch = F.fix_text(text, mp)
            self.assertEqual(got["text"], new, text)
            self.assertEqual([tuple(c) for c in got["changes"]], [tuple(c) for c in ch], text)
    def test_generic_respelling(self):
        """Any other term is respelled into the ASEM notation (ʾ->ʔ, q->ḳ, θ->ṯ ...), as GenericMap does in Python; x̣ and č are left alone."""
        cases = SYNTH + ["{{inh|amw|sem-pro|*šabʕ-|*šabʿum}} {{m|sem-pro|*qarn-}} {{cog|sem-pro|*x̣arb-}} {{m|sem-pro|*čaʿlab-}} {{m|sem-pro|*ṣ́abuʿ-}}",
                         "{{ety|ota|:bor|ar:x<ety:uder<sem-pro:*maraṣ̂-<t:to be ill>>>|text=2}} {{inh|he|sem-pro|*ʔanθ-at-}} {{m|sem-pro|*ŝVbVr-}} {{m|sem-pro|*θ̣ipr-}}",
                         "{{inh|he|sem-pro|*ʾila}} {{m|sem-pro|*ḳarn-}} {{m|sem-pro|*sₓawm-}} {{m|sem-pro|*rawḏ̣-}}",
                         "{{inh|ar|sem-pro|*ʔbd}} {{inh|ar|sem-pro|*ṯql}} {{m|sem-pro|*bn}} {{m|sem-pro|*ḏbb}} {{inh|phn|sem-pro|*ʾš}} {{m|sem-pro|*ṣ́rb|t=x}} {{m|sem-pro|*ṯ̣lm}}",
                         "{{ety|ar|:inh|sem-pro:*ʿṯn}} {{m|sem-pro|*q-n-y}} {{m|sem-pro|*ʔ-b-d}} {{m|sem-pro|*ʔalp-}} {{m|sem-pro|*b}} {{m|sem-pro|*mrṣ̂}} {{m|sem-pro|*ʔbdʔbd}}"]
        for text, got in zip(cases, self.js(cases, M, generic=True)):
            new, ch = F.fix_text(text, F.GenericMap(M))
            self.assertEqual(got["text"], new, text)
            self.assertEqual([tuple(c) for c in got["changes"]], [tuple(c) for c in ch], text)
        got = self.js(["{{cog|sem-pro|*x̣arb-}} {{m|sem-pro|*sₓawm-}}"], {}, generic=True)[0]
        self.assertEqual(got["changes"], [])
    def test_real_pages(self):
        data = json.loads((ROOT / "tests" / "data" / "respell_pages.json").read_text(encoding="utf-8"))
        mapping = {(lv, b): g for lv, b, g in data["mapping"]}
        got = self.js([p["old"] for p in data["pages"]], mapping)
        for p, g in zip(data["pages"], got):
            self.assertEqual(g["text"], p["new"], p["title"])
            self.assertEqual(g["text"], F.fix_text(p["old"], mapping)[0], p["title"])
            self.assertEqual(len(g["changes"]), len(p["changes"]), p["title"])
    def test_idempotent(self):
        for g in self.js(SYNTH, M):
            again = self.js([g["text"]], M)[0]
            self.assertEqual(again, dict(text=g["text"], changes=[]))

@unittest.skipUnless(shutil.which("node"), "node is not installed")
class UserScript(unittest.TestCase):
    """site/wikt_respell.user.js against a stub of MediaWiki's edit page (mw, jQuery, the edit box)."""
    HARNESS = r"""
const fs=require('fs'), vm=require('vm');
const cfg=JSON.parse(process.argv[1]);
const box={val:cfg.text, summary:'', diff:0, notes:[], minor:null, watch:null};
function wrap(sel){ return {length: sel==='#wpTextbox1'&&!cfg.noBox?1:1,
  textSelection(op,v){ if(op==='getContents') return box.val; if(op==='setContents') box.val=v; },
  val(v){ if(sel==='#wpSummary'){ if(v===undefined) return box.summary; box.summary=v; } },
  prop(n,v){ if(n==='checked'){ if(sel==='#wpMinoredit') box.minor=v; if(sel==='#wpWatchthis') box.watch=v; } return this; },
  trigger(e){ if(sel==='#wpDiff'&&e==='click') box.diff++; } }; }
const $=function(a){ if(typeof a==='function'){ a(); return; } if(a==='#wpTextbox1'&&cfg.noBox) return {length:0}; return wrap(a); };
const mw={config:{get:k=>({wgAction:cfg.action,wgPageName:cfg.pageName||'X'})[k]}, loader:{using:()=>({then:f=>{f();}})}, notify:(m,o)=>box.notes.push(m)};
const ss={}; const sessionStorage={getItem:k=>(k in ss?ss[k]:null), setItem:(k,v)=>{ss[k]=v;}, removeItem:k=>{delete ss[k];}};
if (cfg.pendingFor) ss.asemRespellPending = cfg.pendingFor;
box.form = {listeners:[], addEventListener(ev,fn){ this.listeners.push(fn); }};
const document={getElementById:id=>id==='editform'?box.form:null};
box.closed=false; box.posted=null;
const ctx={mw,$,sessionStorage,document,close(){ box.closed=true; },
  opener: cfg.noOpener ? null : {postMessage(data,origin){ box.posted={data,origin}; }},
  location:{search:cfg.search},setTimeout:f=>f(),console};
ctx.window=ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
if (cfg.simulateSubmit) box.form.listeners.forEach(f=>f({submitter:{id:cfg.submitterId||'wpSave'}}));
box.pending = sessionStorage.getItem("asemRespellPending");
console.log(JSON.stringify(box));
"""
    def run_js(self, **cfg):
        cfg = dict(dict(text="{{inh|ar|sem-pro|*ʾab-}} and {{m|sem-pro|*ʔab-}}", action="edit", search="?title=X&action=edit&respell=1"), **cfg)
        us = ROOT / "site" / "wikt_respell.user.js"
        if not us.exists():
            self.skipTest("run: python scripts/wikt_fix_refs.py checklist")
        r = subprocess.run(["node", "-e", self.HARNESS, json.dumps(cfg, ensure_ascii=False), str(us)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout.strip().splitlines()[-1])
    def test_respells_summarises_and_shows_the_diff(self):
        b = self.run_js(text="{{inh|ar|sem-pro|*ʿayn-}} x [[Reconstruction:Proto-Semitic/ʿayn-]]")
        self.assertEqual(b["val"], "{{inh|ar|sem-pro|*ʕayn-}} x [[Reconstruction:Proto-Semitic/ʕayn-]]")
        self.assertIn("*ʿayn- → *ʕayn-", b["summary"]); self.assertNotIn("script-assisted", b["summary"])   # dropped 2026-10-30: the user page says which tools are used
        self.assertEqual(b["diff"], 1)
        self.assertIs(b["minor"], True); self.assertIs(b["watch"], False)       # minor edit, page not watched
    def test_only_on_the_checklist_links(self):
        for cfg in (dict(search="?title=X&action=edit"), dict(search="?title=X&action=edit&respell=0"), dict(action="view"), dict(action="submit")):
            b = self.run_js(text="{{inh|ar|sem-pro|*ʿayn-}}", **cfg)
            self.assertEqual((b["val"], b["diff"], b["summary"]), ("{{inh|ar|sem-pro|*ʿayn-}}", 0, ""), cfg)
            self.assertEqual((b["minor"], b["watch"]), (None, None), cfg)       # the checkboxes are left alone too
    def test_nothing_to_change(self):
        b = self.run_js(text="{{inh|ar|sem-pro|*ʕayn-}}")
        self.assertEqual((b["diff"], b["summary"], b["minor"], b["watch"]), (0, "", None, None)); self.assertTrue(any("nothing to change" in n for n in b["notes"]))
    def test_saving_arms_the_close_flag_with_the_page_title(self):
        b = self.run_js(simulateSubmit=True, pageName="Reconstruction:Proto-Semitic/ʔab-")
        self.assertEqual(b["pending"], "Reconstruction:Proto-Semitic/ʔab-")
        self.assertFalse(b["closed"])                                          # still on the edit page: does not close itself
    def test_show_changes_and_preview_do_not_arm_the_close_flag(self):
        for submitter in ("wpDiff", "wpPreview"):
            b = self.run_js(simulateSubmit=True, submitterId=submitter)
            self.assertIsNone(b["pending"], submitter)                        # only a real Save arms it -- this was the "closes immediately" bug
    def test_a_flagged_tab_closes_and_reports_once_it_lands_on_the_saved_article(self):
        b = self.run_js(action="view", pageName="Reconstruction:Proto-Semitic/ʔab-", pendingFor="Reconstruction:Proto-Semitic/ʔab-")
        self.assertTrue(b["closed"])
        self.assertIsNone(b["pending"])                                       # the flag is consumed, not left behind
        self.assertEqual(b["posted"]["data"], {"asemRespellSaved": "Reconstruction:Proto-Semitic/ʔab-"})
    def test_underscores_in_the_page_name_are_matched_as_spaces(self):
        b = self.run_js(action="view", pageName="Two_words", pendingFor="Two words")
        self.assertTrue(b["closed"])
    def test_a_flag_for_a_different_page_consumes_but_does_not_close(self):
        b = self.run_js(action="view", pageName="other-page", pendingFor="Reconstruction:Proto-Semitic/ʔab-")
        self.assertFalse(b["closed"]); self.assertIsNone(b["posted"])
        self.assertIsNone(b["pending"])                                       # still consumed: a stray flag does not linger
    def test_no_opener_still_closes_without_erroring(self):
        b = self.run_js(action="view", pageName="X", pendingFor="X", noOpener=True)
        self.assertTrue(b["closed"]); self.assertIsNone(b["posted"])
    def test_an_unflagged_tab_never_closes_itself(self):
        b = self.run_js(action="view")
        self.assertFalse(b["closed"])

if __name__ == "__main__":
    unittest.main(verbosity=1)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class SedIdSame(unittest.TestCase):
    """addSedId() (in the browser) and add_sed_id() (scripts/wikt_sed_ids.py) give the same text, on the references found live and edge cases."""
    def test_same(self):
        import wikt_sed_ids as S
        live = [r["ref"] for r in json.loads((ROOT / "data" / "wiktionary" / "sed_ref_ids.json").read_text(encoding="utf-8"))]
        cases = [("x " + r + " y", "636", "*ḳunpuḏ-") for r in live] + [
            ("{{R:sem-pro:SED|volume=2|pages=181–183, Nr. 133}}", "636", "*ḳunpuḏ-"),
            ("{{R:sem-pro:SED|entry=*prm}}", "57", "*prm"),                                  # has an entry: only id=
            ("{{R:sem-pro:SED|e=57}} {{R:sem-pro:SED}}", "9", ""),                           # the first one already links: the second gets it
            ("{{R:sem-pro:SED|id=1}}", "9", "*x"), ("no reference", "9", "*x"), ("{{R:sem-pro:SED}}", "12", ""),
        ]
        code = ("const R=require(process.argv[1]);let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{"
                "console.log(JSON.stringify(JSON.parse(s).map(c=>{const r=R.addSedId(c[0],c[1],c[2]);return [r.text,r.changed];})));});")
        out = subprocess.run(["node", "-e", code, str(ROOT / "scripts" / "respell_core.js")], input=json.dumps(cases), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), [list(S.add_sed_id(t, i, e)) for t, i, e in cases])
        self.assertEqual(S.add_sed_id("{{R:sem-pro:SED|e=57}} {{R:sem-pro:SED}}", "9")[0], "{{R:sem-pro:SED|e=57}} {{R:sem-pro:SED|id=9}}")


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ReplacementsSame(unittest.TestCase):
    """applyReplacements() (browser) and apply_pairs() (scripts/wikt_script_requests.py) agree, on the planned native-script fills."""
    def test_same(self):
        import wikt_script_requests as R, wikt_conflicts as K
        rows = json.loads((ROOT / "data" / "wiktionary" / "script_requests.json").read_text(encoding="utf-8"))
        cases = [(K.cached(p) or "", pairs) for p, pairs in list(R.page_edits(rows).items())[:40]] + [("a {{x}} b {{x}}", [["{{x}}", "{{y}}"]]), ("none", [["{{x}}", "{{y}}"]])]
        code = ("const R=require(process.argv[1]);let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{"
                "console.log(JSON.stringify(JSON.parse(s).map(c=>{const r=R.applyReplacements(c[0],c[1]);return [r.text,r.found];})));});")
        out = subprocess.run(["node", "-e", code, str(ROOT / "scripts" / "respell_core.js")], input=json.dumps(cases), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), [list(R.apply_pairs(t, [tuple(p) for p in pairs])) for t, pairs in cases])
