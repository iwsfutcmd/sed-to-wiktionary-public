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
const mw={config:{get:k=>({wgAction:cfg.action})[k]}, loader:{using:()=>({then:f=>{f();}})}, notify:(m,o)=>box.notes.push(m)};
const ctx={mw,$,location:{search:cfg.search},setTimeout:f=>f(),console};
ctx.window=ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
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
        self.assertIn("*ʿayn- → *ʕayn-", b["summary"]); self.assertIn("script-assisted", b["summary"])
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

if __name__ == "__main__":
    unittest.main(verbosity=1)
