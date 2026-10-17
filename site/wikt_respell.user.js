// ASEM respeller (https://github.com/iwsfutcmd/sed-to-wiktionary, scripts/respell_core.js). Acts only on edit links ending in &respell=1.
// Respell references to Proto-Semitic / Proto-West Semitic reconstructions to the WT:ASEM notation.
// A line-for-line port of fix_text() in scripts/wikt_fix_refs.py (tests/test_respell_js.py checks that both give the same text).
// Pure: fixText(text, mapping) -> { text, changes }.  mapping: { "PS\tʾab-": "ʔab-", ... } (level TAB stem -> standard stem).
(function (root) {
  "use strict";
  var LANGS = { "sem-pro": "PS", "sem-wes-pro": "PWS" };
  function nfc(s) { return s.normalize("NFC"); }

  // every {{...}} (nested ones too): args[k] = [a, b] with text.slice(a, b) one argument without its pipe; args[0] is the name
  function parse(text) {
    var res = [], stack = [], i = 0, n = text.length;
    while (i < n) {
      if (text.startsWith("{{", i)) { stack.push({ start: i, starts: [i + 2], links: 0 }); i += 2; continue; }
      if (text.startsWith("}}", i) && stack.length) {
        var t = stack.pop(), st = t.starts, args = [];
        for (var k = 0; k < st.length; k++) args.push([st[k], k + 1 < st.length ? st[k + 1] - 1 : i]);
        res.push({ start: t.start, end: i + 2, args: args }); i += 2; continue;
      }
      if (text.startsWith("[[", i) && stack.length) { stack[stack.length - 1].links++; i += 2; continue; }
      if (text.startsWith("]]", i) && stack.length) { var s = stack[stack.length - 1]; s.links = Math.max(0, s.links - 1); i += 2; continue; }
      if (text[i] === "|" && stack.length && stack[stack.length - 1].links === 0) stack[stack.length - 1].starts.push(i + 1);
      i++;
    }
    return res;
  }

  // positional arguments (no top-level `name=`) after the template name
  function positional(text, args) {
    var out = [];
    for (var k = 1; k < args.length; k++) {
      var v = text.slice(args[k][0], args[k][1]);
      if (/^\s*[\w-]+\s*=/.test(v) && !v.replace(/^\s+/, "").startsWith("[")) continue;
      out.push(args[k]);
    }
    return out;
  }

  // '*ʾab-<t:x>' -> [prefix, stem, suffix]
  function termCore(value) {
    var m = /^(\s*\*?)([^<>|{}\[\]]+?)(\s*(?:<[^>]*>)*\s*)$/.exec(value);
    return m ? [m[1], m[2], m[3]] : null;
  }

  function fixText(text, mapping) {
    var edits = []; // [a, b, replacement, kind, old, new]
    function lookup(level, stem) { var v = mapping[level + "\t" + nfc(stem)]; return v && nfc(stem) !== v ? v : null; }
    function termEdit(level, a, b) {
      var parts = termCore(text.slice(a, b));
      if (!parts) return;
      var nw = lookup(level, parts[1]);
      if (nw) edits.push([a, b, parts[0] + nw + parts[2], "term", parts[1], nw]);
    }
    var tpls = parse(text);
    tpls.forEach(function (t) {
      var pos = positional(text, t.args);
      pos.forEach(function (ab, k) {
        var level = LANGS[text.slice(ab[0], ab[1]).trim()];
        if (!level) return;
        pos.slice(k + 1, k + 3).forEach(function (c) { if (text.slice(c[0], c[1]).trim()) termEdit(level, c[0], c[1]); });
      });
      t.args.slice(1).forEach(function (ab) { // {{ety|ar|:inh|sem-pro:*X}}
        var m = /^(\s*(sem-pro|sem-wes-pro):)(\*?)([^<>|{}\[\]]+?)(\s*(?:<[^>]*>)*\s*)$/.exec(text.slice(ab[0], ab[1]));
        if (!m) return;
        var nw = lookup(LANGS[m[2]], m[4]);
        if (nw) { var a0 = ab[0] + m[1].length + m[3].length; edits.push([a0, a0 + m[4].length, nw, "ety", m[4], nw]); }
      });
    });
    var re = /\[\[(Reconstruction:Proto-(?:West )?Semitic\/)([^\]|#]+)(\|[^\]]*)?\]\]/g, m;
    while ((m = re.exec(text)) !== null) {
      var level = m[1].indexOf("West") >= 0 ? "PWS" : "PS", stem = m[2].trim(), nw = lookup(level, stem);
      if (!nw) continue;
      var s2 = m.index + m[0].indexOf(m[2], m[0].indexOf("/") + 1);
      edits.push([s2, s2 + m[2].length, nw, "link", stem, nw]);
      var disp = (m[3] || "").slice(1);
      if (m[3] && (disp.trim() === "*" + stem || disp.trim() === stem)) {
        var s3 = m.index + m[0].indexOf(m[3]);
        edits.push([s3 + 1, s3 + m[3].length, (disp.startsWith("*") ? "*" : "") + nw, "link-text", stem, nw]);
      }
    }
    edits.sort(function (x, y) { return x[0] - y[0] || x[1] - y[1]; });
    var seen = {}, uniq = [];
    edits.forEach(function (e) { var key = e[0] + ":" + e[1]; if (!seen[key]) { seen[key] = 1; uniq.push(e); } });
    for (var i = 0; i + 1 < uniq.length; i++) if (uniq[i][1] > uniq[i + 1][0]) throw new Error("overlapping edits");
    var out = text;
    for (var j = uniq.length - 1; j >= 0; j--) out = out.slice(0, uniq[j][0]) + uniq[j][2] + out.slice(uniq[j][1]);
    return { text: out, changes: uniq.map(function (e) { return [e[3], e[4], e[5]]; }) };
  }

  var api = { fixText: fixText, parse: parse };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.WiktRespell = api;
})(typeof window !== "undefined" ? window : this);

(function () {
  var MAP = {
 "PS\tbaʿl-": "baʕl-",
 "PS\tlabiʾ-": "labiʔ-",
 "PS\tmaraṣ̂-": "maraṣ́-",
 "PS\tmiʾat-": "miʔat-",
 "PS\tnašaq-": "našaḳ-",
 "PS\tqaraṣ-": "ḳaraṣ-",
 "PS\tqarib-": "ḳarib-",
 "PS\tqarn-": "ḳarn-",
 "PS\tqarqar-": "ḳarḳar-",
 "PS\tqudš-": "ḳudš-",
 "PS\traʾš-": "raʔš-",
 "PS\ttišʿ-": "tišʕ-",
 "PS\twaraq-": "waraḳ-",
 "PS\tðikar-": "ḏikar-",
 "PS\tśaʿr-": "śaʕr-",
 "PS\tšabʿ-": "šabʕ-",
 "PS\tšamaʿ-": "šamaʕ-",
 "PS\tšidθ-": "šidṯ-",
 "PS\tʾabn-": "ʔabn-",
 "PS\tʾakal-": "ʔakal-",
 "PS\tʾalp-": "ʔalp-",
 "PS\tʾarṣ́-": "ʔarṣ́-",
 "PS\tʾasar-": "ʔasar-",
 "PS\tʾayyal-": "ʔayyal-",
 "PS\tʾaḥad-": "ʔaḥad-",
 "PS\tʾaḫað-": "ʔaḫaḏ-",
 "PS\tʾaḫaḏ-": "ʔaḫaḏ-",
 "PS\tʾil-": "ʔil-",
 "PS\tʾirbay-": "ʔirbay-",
 "PS\tʾiš-": "ʔiš-",
 "PS\tʾuðn-": "ʔuḏn-",
 "PS\tʾuḏn-": "ʔuḏn-",
 "PS\tʿapar-": "ʕapar-",
 "PS\tʿayn-": "ʕayn-",
 "PS\tʿazab-": "ʕazab-",
 "PS\tʿaḳrab-": "ʕaḳrab-",
 "PS\tʿaṯtar-": "ʕaṯtar-",
 "PS\tθalg-": "ṯalg-",
 "PS\tθamāniy-": "ṯamāniy-",
 "PS\tθawr-": "ṯawr-",
 "PS\tθaʿlab-": "ṯaʕlab-",
 "PS\tθūm-": "ṯūm-",
 "PS\tθ̣aby-": "ṯ̣aby-",
 "PS\tθ̣ill-": "ṯ̣ill-",
 "PS\tθ̣upr-": "ṯ̣upr-",
 "PS\tḍabuʿ-": "ṣ́abuʕ-",
 "PS\tḏiʾb-": "ḏiʔb-",
 "PS\tḥaql-": "ḥaḳl-",
 "PS\tḥaraθ-": "ḥaraṯ-",
 "PS\tḥdθ-": "ḥdṯ-",
 "PS\tṣaɣir-": "ṣaḡir-",
 "PS\tṣ́abuʿ-": "ṣ́abuʕ-",
 "PS\tṣ́aʾn-": "ṣ́aʔn-",
 "PS\tṯaʿlab-": "ṯaʕlab-",
 "PS\tṱill-": "ṯ̣ill-",
 "PS\tṱupr-": "ṯ̣upr-"
};
  mw.loader.using(["jquery.textSelection"]).then(function () { $(function () {
    if (mw.config.get("wgAction") !== "edit" || !/[?&]respell=1(&|$)/.test(location.search)) return;   // only for the links of the checklist page
    var $ta = $("#wpTextbox1");
    if (!$ta.length) { mw.notify("Respell: no plain edit box here (turn CodeMirror off).", { type: "error", autoHide: false }); return; }
    var r = WiktRespell.fixText($ta.textSelection("getContents"), MAP);
    if (!r.changes.length) { mw.notify("Respell: nothing to change on this page (already fixed?).", { type: "warn", autoHide: false }); return; }
    $ta.textSelection("setContents", r.text);
    var seen = {}, pairs = [];
    r.changes.forEach(function (c) { var k = "*" + c[1] + " → *" + c[2]; if (!seen[k]) { seen[k] = 1; pairs.push(k); } });
    $("#wpSummary").val("respell Proto-Semitic reference to the WT:ASEM notation (" + pairs.slice(0, 4).join(", ") + (pairs.length > 4 ? " …" : "") + ") (script-assisted)");
    mw.notify("Respell: " + r.changes.length + " change(s). Check the diff, then Save.", { autoHide: false });
    setTimeout(function () { $("#wpDiff").trigger("click"); }, 400);
  }); });
})();
