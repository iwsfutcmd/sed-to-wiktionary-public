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
    "", "no templates at all ʾab-", "{{unclosed|sem-pro|*ʾab-", "}} stray {{m|sem-pro|*ʾab-}}",
    "{{inh|ar|sem-pro|id=x|*ʾab-|t=x}}\n{{inh|ar|sem-pro|*waraq-}}\n[[Reconstruction:Proto-Semitic/waraq-]]",
]

@unittest.skipUnless(shutil.which("node"), "node is not installed")
class SamePythonAndJs(unittest.TestCase):
    def js(self, cases, mapping):
        m = {f"{lv}\t{b}": g for (lv, b), g in mapping.items()}
        code = ("const R=require(process.argv[1]);let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{const j=JSON.parse(s);"
                "console.log(JSON.stringify(j.cases.map(t=>R.fixText(t,j.mapping))));});")
        r = subprocess.run(["node", "-e", code, str(ROOT / "scripts" / "respell_core.js")], input=json.dumps(dict(cases=cases, mapping=m)), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)
    def test_synthetic(self):
        for text, got in zip(SYNTH, self.js(SYNTH, M)):
            new, ch = F.fix_text(text, M)
            self.assertEqual(got["text"], new, text)
            self.assertEqual([tuple(c) for c in got["changes"]], [tuple(c) for c in ch], text)
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
const box={val:cfg.text, summary:'', diff:0, notes:[]};
function wrap(sel){ return {length: sel==='#wpTextbox1'&&!cfg.noBox?1:1,
  textSelection(op,v){ if(op==='getContents') return box.val; if(op==='setContents') box.val=v; },
  val(v){ if(sel==='#wpSummary'){ if(v===undefined) return box.summary; box.summary=v; } },
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
    def test_only_on_the_checklist_links(self):
        for cfg in (dict(search="?title=X&action=edit"), dict(search="?title=X&action=edit&respell=0"), dict(action="view"), dict(action="submit")):
            b = self.run_js(text="{{inh|ar|sem-pro|*ʿayn-}}", **cfg)
            self.assertEqual((b["val"], b["diff"], b["summary"]), ("{{inh|ar|sem-pro|*ʿayn-}}", 0, ""), cfg)
    def test_nothing_to_change(self):
        b = self.run_js(text="{{inh|ar|sem-pro|*ʕayn-}}")
        self.assertEqual((b["diff"], b["summary"]), (0, "")); self.assertTrue(any("nothing to change" in n for n in b["notes"]))

if __name__ == "__main__":
    unittest.main(verbosity=1)
