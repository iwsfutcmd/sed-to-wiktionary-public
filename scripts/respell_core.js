// Respell references to Proto-Semitic / Proto-West Semitic reconstructions to the WT:ASEM notation.
// A line-for-line port of fix_text() in scripts/wikt_fix_refs.py (tests/test_respell_js.py checks that both give the same text).
// Pure: fixText(text, mapping) -> { text, changes }.  mapping: { "PS\tʾab-": "ʔab-", ... } (level TAB stem -> standard stem).
(function (root) {
  "use strict";
  var LANGS = { "sem-pro": "PS", "sem-wes-pro": "PWS" };
  function set(a) { var o = {}; a.forEach(function (x) { o[x] = 1; }); return o; }
  var ETY_TPL = set(["inh", "inh+", "der", "der+", "bor", "bor+", "lbor", "slbor", "cal", "calque", "pcal", "psm"]);
  var REF_TPL = set(["m", "m+", "l", "l+", "cog", "noncog", "ncog", "desc", "desctree", "syn", "ant", "cf", "cognate", "mention", "link", "nc"]);
  function nfc(s) { return s.normalize("NFC"); }
  // the ASEM notation: variant -> standard pairs and the letters no rule reads, handed over by the caller (they come from scripts/wikt_orthography.py)
  var VARIANTS = [], MANUAL = [], CONSONANTS = [];
  function setNotation(variants, manual, consonants) { VARIANTS = variants; MANUAL = manual; CONSONANTS = consonants || []; }
  function graphemes(s) { // a letter with its combining marks
    var out = [];
    for (var ch of nfc(s)) { if (/\p{M}/u.test(ch) && out.length) out[out.length - 1] += ch; else out.push(ch); }
    return out.map(nfc);
  }
  function rootify(stem) { // a root: ʔbd -> ʔ-b-d (hyphen between the radicals, none at the end); anything else is returned unchanged
    var s = nfc(stem);
    if (s.indexOf("-") >= 0) return s;
    var gs = graphemes(s);
    if (gs.length >= 2 && gs.length <= 5 && gs.every(function (g) { return CONSONANTS.indexOf(g) >= 0; })) return gs.join("-");
    return s;
  }
  function standardise(stem) {
    var s = nfc(stem);
    VARIANTS.forEach(function (p) { s = s.split(nfc(p[0])).join(nfc(p[1])); });
    return nfc(s);
  }

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

  var CODES = { PS: "sem-pro", PWS: "sem-wes-pro" };
  function fixText(text, mapping, generic) {
    var edits = []; // [a, b, replacement, kind, old, new]
    function target(level, stem) { // -> [new level, new stem] or null; a mapping value "PWS:ṣ́abb-" moves the term to the other level
      var v = mapping[level + "\t" + nfc(stem)];
      if (!v) { var g = lookup(level, stem); return g ? [level, g] : null; }
      var m = /^(PWS|PS):(.+)$/.exec(v), lv = m ? m[1] : level, nw = m ? m[2] : v;
      return lv === level && nw === nfc(stem) ? null : [lv, nw];
    }
    function lookup(level, stem) {
      var v = mapping[level + "\t" + nfc(stem)];
      if (!v && generic) { // any other term: its plain respelling, unless it holds a letter no rule reads
        var s = standardise(stem);
        if (!MANUAL.some(function (m) { return s.indexOf(m) >= 0; })) { if (s !== nfc(stem)) v = s; }
      }
      return v && nfc(stem) !== v ? v : null;
    }
    function termEdit(level, a, b, codeSpan) {
      var parts = termCore(text.slice(a, b));
      if (!parts) return;
      var tg = target(level, parts[1]);
      if (!tg) return;
      if (tg[0] !== level) edits.push([codeSpan[0], codeSpan[1], CODES[tg[0]], "level", level, tg[0]]);
      if (tg[1] !== nfc(parts[1])) edits.push([a, b, parts[0] + tg[1] + parts[2], "term", parts[1], tg[1]]);
    }
    var tpls = parse(text);
    tpls.forEach(function (t) {
      var name = text.slice(t.args[0][0], t.args[0][1]).trim().toLowerCase();
      var pos = positional(text, t.args);
      var li = ETY_TPL[name] ? 1 : REF_TPL[name] ? 0 : null; // index of the positional argument that names the language of the term
      if (li !== null && pos.length > li) {
        var level = LANGS[text.slice(pos[li][0], pos[li][1]).trim()];
        if (level) {
          for (var j = li + 1; j < Math.min(li + 4, pos.length); j++) { // the term, then alternative forms written *X
            var v = text.slice(pos[j][0], pos[j][1]).trim();
            if (v && (j === li + 1 || v.startsWith("*"))) termEdit(level, pos[j][0], pos[j][1], pos[li]);
          }
        }
      }
      t.args.slice(1).forEach(function (ab) { // ety chains: every sem-pro:*X inside an argument, also nested <ety:uder<sem-pro:*X>>
        var argText = text.slice(ab[0], ab[1]), em, ere = /(?<![\w-])(sem-pro|sem-wes-pro):(\*?)([^<>|{}\[\]\s]+?)(?=[<>|}\s]|$)/g;
        while ((em = ere.exec(argText)) !== null) {
          var lv = LANGS[em[1]], tg = target(lv, em[3]);
          if (!tg) continue;
          if (tg[0] !== lv) edits.push([ab[0] + em.index, ab[0] + em.index + em[1].length, CODES[tg[0]], "level", lv, tg[0]]);
          if (tg[1] !== nfc(em[3])) { var a0 = ab[0] + em.index + em[1].length + 1 + em[2].length; edits.push([a0, a0 + em[3].length, tg[1], "ety", em[3], tg[1]]); }
        }
      });
    });
    var re = /\[\[(Reconstruction:Proto-(?:West )?Semitic\/)([^\]|#]+)(\|[^\]]*)?\]\]/g, m;
    while ((m = re.exec(text)) !== null) {
      var level = m[1].indexOf("West") >= 0 ? "PWS" : "PS", stem = m[2].trim(), tg = target(level, stem);
      if (!tg) continue;
      if (tg[0] !== level) edits.push([m.index + 2, m.index + 2 + m[1].length, "Reconstruction:Proto-" + (tg[0] === "PWS" ? "West " : "") + "Semitic/", "level", level, tg[0]]);
      var nw = tg[1];
      if (nw === nfc(stem)) continue;
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

  var api = { fixText: fixText, parse: parse, standardise: standardise, rootify: rootify, setNotation: setNotation };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.WiktRespell = api;
})(typeof window !== "undefined" ? window : this);
