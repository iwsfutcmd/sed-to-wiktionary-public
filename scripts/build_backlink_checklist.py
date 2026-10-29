"""Build the Daughter Backlink Checklist page from data/wiktionary/backlink_pages.json (written by `wikt_backlink.py pages`).
usage: build_backlink_checklist.py [--saved N]   -> .artifacts/daughter-backlink-checklist.html (published as an artifact by hand)
Takes its styles from the SED Coverage Worklist page (.artifacts/sed-coverage-worklist.html), so the two look alike. --saved: how many
back-links have been saved so far, for the header (the scan only sees what is left to do)."""
import datetime, json, re, sys
from pathlib import Path
ROOT = str(Path(__file__).resolve().parent.parent)
SAVED = int(sys.argv[sys.argv.index("--saved") + 1]) if "--saved" in sys.argv else None
POSTED = len(list((Path(ROOT) / "wiktionary_drafts" / "done").glob("*.wiki")))
TODAY = datetime.date.today().isoformat()
wl = open(f"{ROOT}/.artifacts/sed-coverage-worklist.html", encoding="utf-8").read()
style = re.search(r"<style>.*?</style>", wl, re.S).group(0)
D = json.load(open(f"{ROOT}/data/wiktionary/backlink_pages.json", encoding="utf-8"))
ready = [x for x in D if "full" in x and "confirm" not in x]
confirm = [x for x in D if "confirm" in x]
manual = [x for x in D if "skip" in x]
left = [x for x in D if "left" in x]
data = json.dumps(dict(ready=ready, confirm=confirm, manual=manual, left=left), ensure_ascii=False).replace("</", "<\\/")
sys.path.insert(0, f"{ROOT}/scripts")
from wikt_langs import sections
langhash = json.dumps({x["code"]: sections(x["code"].split(",")[0])[0].replace(" ", "_") for x in D}, ensure_ascii=False)
html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Daughter Backlink Checklist</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
{style}
<style>
.senses {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: .88rem; }}
.senses > div {{ background: var(--code-bg); border-radius: 6px; padding: 8px 10px; }}
.senses b {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 500; display: block; margin-bottom: 4px; }}
.btn[aria-disabled="true"] {{ opacity: .4; pointer-events: none; }}
.reason {{ font-size: .88rem; color: var(--muted); margin: 0; }}
@media (max-width: 600px) {{ .senses {{ grid-template-columns: 1fr; }} }}
.left-list {{ margin: 0; padding-left: 1.2em; line-height: 1.9; }}
</style>
</head><body>
<main>
  <header class="panel top">
    <h1>Daughter pages that don't cite us yet</h1>
    <p class="muted">Every descendant on our {POSTED} posted reconstruction pages that has a Wiktionary page with no Proto-Semitic reference yet. Built by <code>scripts/wikt_backlink.py pages</code> from the live pages (re-downloaded {TODAY}{"; " + str(SAVED) + " saved so far" if SAVED is not None else ""}): each edit adds <code>{{{{inh|…|sem-pro|*…}}}}</code> to that language's section only — “From …” before the existing etymology, a new Etymology section if there is none, or one more step in an <code>{{{{ety}}}}</code> chain. Pages where that would be wrong are listed at the end with the reason.</p>
    <div class="counts">
      <span><b>{len(ready)}</b><span class="muted"> ready</span></span>
      <span><b>{len(confirm)}</b><span class="muted"> confirm the sense first</span></span>
      <span><b>{len(manual)}</b><span class="muted"> need a person</span></span>
      <span><b>{len(left)}</b><span class="muted"> left as is</span></span>
      <span><b id="nDone">0</b><span class="muted"> done (this browser)</span></span>
    </div>
  </header>
  <section class="panel"><div class="section-head"><h2>1 · Ready <span class="badge accent">{len(ready)}</span></h2></div>
    <p class="muted">One button copies the whole edited page and opens the editor with the summary filled in and the edit marked minor. Then: select all, paste, <b>Show changes</b> (only the lines shown here should change), save, tick. Tell me when you're done and I'll re-run the scan.</p>
    <div class="cards" id="ready"></div></section>
{"" if not confirm else f"""  <section class="panel"><div class="section-head"><h2>2 · Confirm the sense first <span class="badge accent">{len(confirm)}</span></h2></div>
    <p class="muted">The page's senses share no word with ours, so it may be a different word with the same spelling. Compare them; the button unlocks once you tick “same word”. If it isn't, leave it.</p>
    <div class="cards" id="confirm"></div></section>"""}
{"" if not manual else f"""  <section class="panel"><div class="section-head"><h2>3 · Need a person <span class="badge accent">{len(manual)}</span></h2></div>
    <p class="muted">No mechanical edit is safe here; the reason is given. The link opens the plain editor.</p>
    <div class="cards" id="manual"></div></section>"""}
  <section class="panel"><div class="section-head"><h2>Left as is <span class="badge">{len(left)}</span></h2></div>
    <p class="muted">Your calls, recorded in <code>DECISIONS</code> in <code>scripts/wikt_backlink.py</code> so later scans skip them.</p>
    <ul class="left-list" id="left"></ul></section>
</main>
<script id="data" type="application/json">{data}</script>
<script>
(function () {{
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent);
  var LANGHASH = __LANGHASH__;
  var KEY = "backlink_checklist_v2", st = {{}};
  try {{ st = JSON.parse(localStorage.getItem(KEY) || "{{}}") || {{}}; }} catch (e) {{}}
  function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(st)); }} catch (e) {{}} count(); }}
  function count() {{ document.getElementById("nDone").textContent = Object.keys(st).filter(function (k) {{ return st[k] === "done"; }}).length; }}
  function el(t, a, kids) {{ var n = document.createElement(t); for (var k in a || {{}}) n.setAttribute(k, a[k]); (kids || []).forEach(function (c) {{ if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }}); return n; }}
  function viewUrl(t, code) {{ return "https://en.wiktionary.org/wiki/" + encodeURIComponent(t.replace(/ /g, "_")) + (LANGHASH[code] ? "#" + LANGHASH[code] : ""); }}
  function recUrl(x) {{ return "https://en.wiktionary.org/wiki/Reconstruction:" + (x.level === "PWS" ? "Proto-West_Semitic" : "Proto-Semitic") + "/" + encodeURIComponent(x.title); }}
  function editUrl(t) {{ return "https://en.wiktionary.org/w/index.php?title=" + encodeURIComponent(t.replace(/ /g, "_")) + "&action=edit"; }}
  var mod = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent) ? "⌘" : "Ctrl";
  function head(x, tagText, tagCls) {{
    var tag = el("span", {{ class: "tag " + tagCls }}, [tagText]);
    return [el("div", {{ class: "card-head" }}, [el("div", {{ class: "card-title" }}, [el("a", {{ href: viewUrl(x.page, x.code), target: "_blank", rel: "noopener", title: "Open the page on Wiktionary" }}, [el("bdi", {{}}, [x.page])]), " ",
      el("span", {{ class: "muted", style: "font-weight:400;font-size:.85rem" }}, ["— " + x.lang + ", from ", el("a", {{ href: recUrl(x), target: "_blank", rel: "noopener", title: "Open the reconstruction page" }}, [(x.level === "PWS" ? "PWS" : "PS") + " *" + x.title])])]), tag]), tag];
  }}
  function card(x, needConfirm) {{
    var k = x.lang + "|" + x.page, done = st[k] === "done";
    var c = el("div", {{ class: "card" + (done ? " is-done" : "") }}), h = head(x, done ? "✓ done" : "to do", done ? "done" : "accent");
    c.appendChild(h[0]); var tag = h[1];
    if (needConfirm) {{
      c.appendChild(el("p", {{ class: "reason" }}, ["⚠ " + x.confirm]));
      c.appendChild(el("div", {{ class: "senses" }}, [el("div", {{}}, [el("b", {{}}, ["Ours"]), x.gloss || "—"]),
        el("div", {{}}, [el("b", {{}}, ["The page's senses"]), x.their_senses.join(" · ") || "—"])]));
      c.appendChild(el("div", {{ class: "row" }}, [el("a", {{ class: "btn", href: viewUrl(x.page, x.code), target: "_blank", rel: "noopener" }}, ["Open page to compare →"])]));
    }}
    if (x.note) c.appendChild(el("p", {{ class: "reason" }}, ["⚠ " + x.note]));
    if (x.reworded && !x.note) c.appendChild(el("p", {{ class: "reason" }}, ["⚠ Rewords the existing etymology: its uncited “derived from Classical Syriac … or … ?” becomes a comparison, as the SED (II 32) gives Arabic as inherited and notes no borrowing. Read the diff before saving."]));
    if (x.section) c.appendChild(el("p", {{ class: "reason" }}, ["Goes in " + x.section + ", as you chose."]));
    var pre = el("pre", {{ class: "diff" }});
    x.diff.forEach(function (l) {{ if (l.trim() !== "+" && l.trim() !== "-") pre.appendChild(el("span", {{ class: l[0] === "-" ? "del" : "add" }}, [l + "\\n"])); }});
    c.appendChild(pre);
    var go = el("a", {{ class: "btn primary big", href: editUrl(x.page) + "&summary=" + encodeURIComponent(x.summary) + "&minor=1", target: "_blank", rel: "noopener" }}, ["Copy edited page & open editor →"]);
    go.addEventListener("click", function () {{
      try {{ navigator.clipboard.writeText(x.full).then(function () {{ go.textContent = "Copied ✓ — now paste it in the editor"; go.classList.add("copied"); }},
                                                    function () {{ go.textContent = "Copy failed — use “Copy page only”"; }}); }} catch (e) {{ go.textContent = "Copy failed — use “Copy page only”"; }}
    }});
    var steps = [];
    if (needConfirm) {{
      var same = el("input", {{ type: "checkbox" }}); same.checked = st[k] === "same" || done;
      go.setAttribute("aria-disabled", same.checked ? "false" : "true");
      same.addEventListener("change", function () {{ if (!done) {{ st[k] = same.checked ? "same" : undefined; if (!same.checked) delete st[k]; save(); }} go.setAttribute("aria-disabled", same.checked ? "false" : "true"); }});
      steps.push(el("li", {{}}, [el("label", {{ style: "display:inline-flex;gap:6px;align-items:center;cursor:pointer" }}, [same, "Same word: ours is one of its senses"])]));
    }}
    var box = el("input", {{ type: "checkbox" }}); box.checked = done;
    box.addEventListener("change", function () {{ if (box.checked) st[k] = "done"; else delete st[k]; save();
      c.className = "card" + (box.checked ? " is-done" : ""); tag.className = "tag " + (box.checked ? "done" : "accent"); tag.textContent = box.checked ? "✓ done" : "to do"; }});
    steps.push(el("li", {{}}, [go]),
      el("li", {{}}, ["In the editor box: ", el("kbd", {{}}, [mod + " A"]), " then ", el("kbd", {{}}, [mod + " V"]), " to paste over everything."]),
      el("li", {{}}, ["Click ", el("b", {{}}, ["Show changes"]), ": only the lines above should change. Anything else means the page was edited since the scan: cancel and tell me."]),
      el("li", {{}}, ["“Minor edit” is pre-ticked. “Watch this page” follows your own settings."]),
      el("li", {{}}, ["Save, then ", el("label", {{ style: "display:inline-flex;gap:6px;align-items:center;cursor:pointer" }}, [box, "tick when saved"])]));
    c.appendChild(el("ol", {{ class: "steps" }}, steps));
    c.appendChild(el("div", {{ class: "summary-line" }}, ["Summary: ", el("span", {{ class: "mono" }}, [x.summary])]));
    var cp = el("button", {{ class: "btn", type: "button", style: "padding:3px 9px;font-size:.8rem" }}, ["Copy page only"]);
    cp.addEventListener("click", function () {{ navigator.clipboard.writeText(x.full).then(function () {{ cp.textContent = "Copied ✓"; }}, function () {{ cp.textContent = "Copy failed"; }}); }});
    c.appendChild(el("div", {{ class: "row" }}, [cp]));
    return c;
  }}
  D.ready.forEach(function (x) {{ document.getElementById("ready").appendChild(card(x, false)); }});
  D.confirm.forEach(function (x) {{ document.getElementById("confirm").appendChild(card(x, true)); }});
  D.left.forEach(function (x) {{
    document.getElementById("left").appendChild(el("li", {{}}, [el("a", {{ href: viewUrl(x.page, x.code), target: "_blank", rel: "noopener" }}, [el("bdi", {{}}, [x.page])]),
      el("span", {{ class: "muted" }}, [" — " + x.lang + ", from ", el("a", {{ href: recUrl(x), target: "_blank", rel: "noopener" }}, ["PS *" + x.title]), ": " + x.left])]));
  }});
  D.manual.forEach(function (x) {{
    var c = el("div", {{ class: "card" }});
    c.appendChild(head(x, "by hand", "accent")[0]);
    c.appendChild(el("p", {{ class: "reason" }}, [x.skip]));
    c.appendChild(el("div", {{ class: "row" }}, [el("a", {{ class: "btn", href: editUrl(x.page), target: "_blank", rel: "noopener" }}, ["Open editor →"]),
      el("span", {{ class: "muted mono" }}, ["{{{{inh|" + x.code + "|" + (x.level === "PWS" ? "sem-wes-pro" : "sem-pro") + "|*" + x.title + "}}}}"])]));
    document.getElementById("manual").appendChild(c);
  }});
  count();
}})();
</script>
</body></html>
"""
html = html.replace("__LANGHASH__", langhash)
open(f"{ROOT}/.artifacts/daughter-backlink-checklist.html", "w", encoding="utf-8").write(html)
print(len(ready), len(confirm), len(manual))
