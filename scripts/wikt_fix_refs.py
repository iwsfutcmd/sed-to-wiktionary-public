"""Respell references to Proto-Semitic / Proto-West Semitic reconstructions to the WT:ASEM notation, page by page, with a human saying yes to each diff.

  python wikt_fix_refs.py plan                 fetch the pages that link to a non-standard spelling and work out the new wikitext (touches nothing on Wiktionary)
  python wikt_fix_refs.py show [PAGE ...]      print the planned diffs
  python wikt_fix_refs.py apply --user NAME    log in (bot password), show each diff, ask y/n, edit.  Password: env WIKT_PASSWORD or a prompt.
  python wikt_fix_refs.py checklist            the MANUAL route (no bot): site/orthography_fix.html + site/wikt_respell.user.js, see data/wiktionary/orthography_survey.md

What it changes, and only this: the TERM of a reconstruction reference. A term is the positional argument after `sem-pro` / `sem-wes-pro` in a template
({{inh|ar|sem-pro|*ʾab-}}, {{cog|sem-pro|*ʾab-}}, {{m|sem-pro|*ʾab-}}, {{l|..}}, {{desc|..}}), the `sem-pro:*ʾab-` of an {{ety}} chain, and the title of a
[[Reconstruction:Proto-Semitic/ʾab-]] link. Never: tr=/t= text, entry= (that quotes a source), anything of another language, named parameters.

Which respellings: a non-standard title that is a redirect to the standard spelling of the same stem (ʾ->ʔ ʿ->ʕ q->ḳ θ->ṯ ṣ̂->ṣ́ ...), a redirect to ANOTHER stem
of the same level (ʾab- -> ʔabw-: the reference follows the redirect, which someone already decided), and non-standard spellings with no page whose standard
spelling exists. A redirect to the other level (PS -> PWS) would need the language code changed too: listed by `plan` as "needs a person", no edit.  A planned page where a link was not found in a recognised place is listed as "unmatched": it is left alone.

Everything that decides what is edited is in fix_text(), which is pure and tested offline (tests/test_fix_refs.py)."""
from pathlib import Path
import csv, difflib, getpass, http.cookiejar, json, os, re, sys, time, unicodedata as U, urllib.error, urllib.parse, urllib.request
from paths import BUILD, ROOT, WIKT
from wikt_orthography import standardise, PFX, MANUAL, VARIANTS, CONSONANTS

API = "https://en.wiktionary.org/w/api.php"
UA = {"User-Agent": "sed-to-wiktionary/1.0 (orthography respelling, supervised; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
OUT = BUILD / "orth_fixes"
LANGS = {"sem-pro": "PS", "sem-wes-pro": "PWS"}
# templates whose terms are looked at: the first group names the term's language in its 2nd positional argument ({{inh|ar|sem-pro|*X}}: the 1st is the
# language that inherits, so {{inh|sem-pro|afa-pro|*X}} is a Proto-Afroasiatic term and is left alone), the second in its 1st ({{m|sem-pro|*X}})
ETY_TPL = {"inh", "inh+", "der", "der+", "bor", "bor+", "lbor", "slbor", "cal", "calque", "pcal", "psm"}
REF_TPL = {"m", "m+", "l", "l+", "cog", "noncog", "ncog", "desc", "desctree", "syn", "ant", "cf", "cognate", "mention", "link", "nc"}
nfc = lambda s: U.normalize("NFC", s)

# ---------------------------------------------------------------- parsing
def parse(text):
    """-> [dict(start, end, args=[(a, b), ...])] for every {{...}} (nested ones too); text[a:b] is one argument without its pipe, args[0] is the name.
    A pipe inside a nested {{ }} or a [[link]] does not split."""
    res, stack, i, n = [], [], 0, len(text)
    while i < n:
        if text.startswith("{{", i):
            stack.append(dict(start=i, starts=[i + 2], links=0)); i += 2; continue
        if text.startswith("}}", i) and stack:
            t = stack.pop(); st = t["starts"]
            args = [(st[k], (st[k + 1] - 1) if k + 1 < len(st) else i) for k in range(len(st))]
            res.append(dict(start=t["start"], end=i + 2, args=args)); i += 2; continue
        if text.startswith("[[", i) and stack:
            stack[-1]["links"] += 1; i += 2; continue
        if text.startswith("]]", i) and stack:
            stack[-1]["links"] = max(0, stack[-1]["links"] - 1); i += 2; continue
        if text[i] == "|" and stack and stack[-1]["links"] == 0:
            stack[-1]["starts"].append(i + 1)
        i += 1
    return res

def positional(text, args):
    """The positional arguments (no top-level `name=`) of a template after the name: [(a, b)]"""
    out = []
    for a, b in args[1:]:
        v = text[a:b]
        if re.match(r"\s*[\w-]+\s*=", v) and not v.lstrip().startswith("["):
            continue
        out.append((a, b))
    return out

# ---------------------------------------------------------------- the edit
def term_core(value):
    """'*ʾab-<t:x>' -> (prefix, stem, suffix) so that prefix+stem+suffix == value"""
    m = re.fullmatch(r"(\s*\*?)([^<>|{}\[\]]+?)(\s*(?:<[^>]*>)*\s*)", value)
    return m.groups() if m else None

CODES = {v: k for k, v in LANGS.items()}
def target(mapping, level, stem):
    """-> (new level, new stem) or None. A mapping value "PWS:ṣ́abb-" moves the term to the other level (the language code changes too)."""
    new = mapping.get((level, nfc(stem)))
    if not new:
        return None
    m = re.match(r"^(PWS|PS):(.+)$", new)
    lv, new = (m.group(1), m.group(2)) if m else (level, new)
    return (lv, new) if (lv, new) != (level, nfc(stem)) else None

def fix_text(text, mapping):
    """text, {(level, stem): standard stem, or "LEVEL:stem" to move it to the other level} -> (new text, [(kind, old, new)]).  Pure; idempotent."""
    edits = []                                                   # (a, b, replacement, kind)
    def term_edit(level, a, b, kind, code_span):
        parts = term_core(text[a:b])
        if not parts:
            return
        pre, stem, suf = parts
        tg = target(mapping, level, stem)
        if not tg:
            return
        if tg[0] != level:
            edits.append((*code_span, CODES[tg[0]], "level", level, tg[0]))
        if tg[1] != nfc(stem):
            edits.append((a, b, pre + tg[1] + suf, kind, stem, tg[1]))
    for t in parse(text):
        name = text[t["args"][0][0]:t["args"][0][1]].strip().lower()
        pos = positional(text, t["args"])
        li = 1 if name in ETY_TPL else 0 if name in REF_TPL else None      # index of the positional argument that names the language of the term
        if li is not None and len(pos) > li:
            level = LANGS.get(text[pos[li][0]:pos[li][1]].strip())
            if level:
                for j in range(li + 1, min(li + 4, len(pos))):             # the term, then alternative forms written *X ({{l|sem-pro||*X}} too)
                    a2, b2 = pos[j]
                    if text[a2:b2].strip() and (j == li + 1 or text[a2:b2].strip().startswith("*")):
                        term_edit(level, a2, b2, "term", pos[li])
        for a, b in t["args"][1:]:                                         # ety chains: every sem-pro:*X inside an argument, also nested <ety:uder<sem-pro:*X>>
            for m in re.finditer(r"(?<![\w-])(sem-pro|sem-wes-pro):(\*?)([^<>|{}\[\]\s]+?)(?=[<>|}\s]|$)", text[a:b]):
                level = LANGS[m.group(1)]
                tg = target(mapping, level, m.group(3))
                if tg and tg[0] != level:
                    edits.append((a + m.start(1), a + m.end(1), CODES[tg[0]], "level", level, tg[0]))
                if tg and tg[1] != nfc(m.group(3)):
                    edits.append((a + m.start(3), a + m.end(3), tg[1], "ety", m.group(3), tg[1]))
    for m in re.finditer(r"\[\[(Reconstruction:Proto-(?:West )?Semitic/)([^\]|#]+)(\|[^\]]*)?\]\]", text):
        level = "PWS" if "West" in m.group(1) else "PS"
        stem = m.group(2).strip()
        tg = target(mapping, level, stem)
        if not tg:
            continue
        if tg[0] != level:
            edits.append((m.start(1), m.end(1), "Reconstruction:Proto-" + ("West " if tg[0] == "PWS" else "") + "Semitic/", "level", level, tg[0]))
        new = tg[1]
        if nfc(stem) != new:
            edits.append((m.start(2), m.end(2), new, "link", stem, new))
            disp = (m.group(3) or "")[1:]
            if disp.strip() in ("*" + stem, stem):                # the shown text is the old spelling too
                edits.append((m.start(3) + 1, m.end(3), ("*" if disp.startswith("*") else "") + new, "link-text", stem, new))
    seen, uniq = set(), []
    for e in sorted(edits, key=lambda e: (e[0], e[1])):
        if (e[0], e[1]) not in seen:
            seen.add((e[0], e[1])); uniq.append(e)
    for e1, e2 in zip(uniq, uniq[1:]):
        assert e1[1] <= e2[0], "overlapping edits"
    out = text
    for a, b, rep, *_ in reversed(uniq):
        out = out[:a] + rep + out[b:]
    return out, [(e[3], e[4], e[5]) for e in uniq]

def editable(title):
    """Entries, appendices and reconstruction pages. Not talk pages, user pages, archives, project pages or templates: those are other people's words."""
    return (title.split(":", 1)[0] if ":" in title else "") in ("", "Appendix", "Reconstruction")

class GenericMap:
    """The mapping fix_text() is given: the explicit (level, stem) -> stem pairs of the survey (redirects to another stem included), and for every other term its
    plain respelling into the ASEM notation (standardise(): ʾ->ʔ q->ḳ θ->ṯ ...) unless it holds a letter no rule reads (x̣, č).
    WT:ASEM says nothing about writing a root with hyphens between the radicals, so a bare root (ʔbd) is NOT rewritten (ʔ-b-d)."""
    def __init__(self, explicit):
        self.explicit = explicit
    def get(self, key, default=None):
        v = self.explicit.get(key)
        if v:
            return v
        std, dev, man = standardise(key[1])
        if any(m in std for m in MANUAL):
            return default
        return std if std != nfc(key[1]) else default

# ---------------------------------------------------------------- what to respell
def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def load_mapping():
    """-> ({(level, stem): standard stem}, [needs a person], {title: [linking pages]})  from the orthography survey."""
    survey, links = read_tsv(WIKT / "orthography_survey.tsv"), read_tsv(WIKT / "orthography_links.tsv")
    exists = {(r["level"], nfc(r["title"])) for r in survey}
    mapping, person = {}, []
    for r in survey:
        if r["action"] == "MANUAL" and r["redirect_to"] and "/" not in r["redirect_to"] and ":" not in r["redirect_to"]:     # x̣arb- -> ḥarb-: a letter no rule reads, a redirect that does
            mapping[(r["level"], nfc(r["title"]))] = nfc(r["redirect_to"])
            continue
        if r["action"] != "redirect ok":
            continue
        std = nfc(standardise(r["title"])[0])
        dest = nfc(r["redirect_to"])
        if dest == std:
            mapping[(r["level"], nfc(r["title"]))] = std
        elif "/" in dest or ":" in dest:                                       # leads to the other level (PS -> PWS needs the language code changed too): a person
            person.append((r["level"], r["title"], r["redirect_to"]))
        else:                                                                    # a redirect to another stem of the same level: references follow the redirect
            mapping[(r["level"], nfc(r["title"]))] = dest
    for r in read_tsv(WIKT / "orthography_refs.tsv"):                          # variants of standard titles
        key = (r["level"], nfc(r["variant"]))
        if key not in mapping and key not in exists:
            mapping[key] = nfc(r["standard"])
    for r in links:                                                         # every link row names a (nonstandard, standard) pair for a page that is not a stem change
        key = (r["level"], nfc(r["nonstandard_title"]))
        if r["standard_title"] and key not in mapping and key not in {(l, nfc(t)) for l, t, _ in person} and (r["level"], nfc(r["standard_title"])) in exists:
            mapping[key] = nfc(r["standard_title"])
    pages = {}
    for r in links:
        if (r["level"], nfc(r["nonstandard_title"])) in mapping:
            pages.setdefault(r["linking_page"], set()).add((r["level"], nfc(r["nonstandard_title"])))
    return mapping, person, pages

# ---------------------------------------------------------------- Wiktionary API
class Api:
    def __init__(self, opener=None):
        self.jar = http.cookiejar.CookieJar()
        self.opener = opener or urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
    def call(self, post=None, **q):
        data = urllib.parse.urlencode(dict(format="json", formatversion=2, maxlag=5, **(post or q))).encode()
        for i in range(8):
            try:
                r = json.load(self.opener.open(urllib.request.Request(API, data=data, headers=UA), timeout=60))
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(min(float(e.headers.get("Retry-After") or 10), 60)); continue
            if r.get("error", {}).get("code") == "maxlag":
                time.sleep(5); continue
            return r
        raise RuntimeError("API busy")
    def pages(self, titles):
        """-> {title: (revid, timestamp, text)} for existing pages, 50 titles a request"""
        out = {}
        titles = list(dict.fromkeys(titles))
        for i in range(0, len(titles), 40):
            r = self.call(action="query", prop="revisions", rvprop="ids|timestamp|content", rvslots="main", titles="|".join(titles[i:i + 40]))
            for p in r["query"]["pages"]:
                if "revisions" in p:
                    rv = p["revisions"][0]
                    out[nfc(p["title"])] = (rv["revid"], rv["timestamp"], rv["slots"]["main"]["content"])
            time.sleep(2)
        return out
    def login(self, user, password):
        tok = self.call(action="query", meta="tokens", type="login")["query"]["tokens"]["logintoken"]
        r = self.call(post=dict(action="login", lgname=user, lgpassword=password, lgtoken=tok))
        if r.get("login", {}).get("result") != "Success":
            raise SystemExit("login failed: " + json.dumps(r.get("login", r))[:200])
    def edit(self, title, text, summary, baserevid, bot=False):
        tok = self.call(action="query", meta="tokens")["query"]["tokens"]["csrftoken"]
        post = dict(action="edit", title=title, text=text, summary=summary, baserevid=baserevid, nocreate=1, token=tok, assert_="user")
        post["assert"] = post.pop("assert_")
        if bot:
            post["bot"] = 1
        return self.call(post=post)

def summary_for(changes):
    pairs = sorted({(o, n) for _, o, n in changes})
    shown = ", ".join(f"*{o} → *{n}" for o, n in pairs[:4]) + (" …" if len(pairs) > 4 else "")
    return f"update Proto-Semitic reference to its current WT:ASEM title ({shown}) (semi-automated)"

# ---------------------------------------------------------------- commands
def plan(api=None):
    api = api or Api()
    mapping, person, pages = load_mapping()
    gmap = GenericMap(mapping)
    corpus = BUILD / "asem_corpus.json"
    if corpus.exists():                                                  # pages that use sem-pro with a variant character or a bare root, found by wikt_asem_check.py
        for t, text in json.loads(corpus.read_text(encoding="utf-8")).items():
            if t not in pages and editable(t) and fix_text(text, gmap)[1]:
                pages[t] = {("?", "(notation)")}
    OUT.mkdir(parents=True, exist_ok=True)
    got = api.pages(list(pages))
    items, unmatched = [], []
    for title, want in sorted(pages.items()):
        if title not in got:
            unmatched.append((title, "page not found")); continue
        revid, ts, text = got[title]
        new, changes = fix_text(text, gmap)
        if changes:
            items.append(dict(title=title, revid=revid, timestamp=ts, old=text, new=new, changes=changes))
        missing = sorted({w[1] for w in want if w[0] != "?"} - {nfc(o) for _, o, _ in changes})
        # a corpus-only candidate, refetched and found already standard, is simply done -- except when it holds
        # an x̣/č: GenericMap deliberately declines those, so an empty `changes` there means "still needs a
        # person", not "already fixed", and stays visible rather than risk hiding it.
        if not changes and not any(w[0] != "?" for w in want) and not any(m in text for m in MANUAL):
            continue
        if not changes or missing:
            via = "<ety:" in text or "sem-pro" not in text and "sem-wes-pro" not in text
            unmatched.append((title, ("linked through another page's etymology chain ({{ety|..<ety:inh<ar:term>>}}); follows when that page is respelled: " if via else
                                      "no recognised reference to ") + ", ".join(missing)))
    moves = []                                                           # root page moves (ʔbd -> ʔ-b-d) are not ASEM: see data/wiktionary/root_notation.md
    (OUT / "plan.json").write_text(json.dumps(dict(mapping=[[lv, b, g] for (lv, b), g in mapping.items()], items=items, moves=moves), ensure_ascii=False), encoding="utf-8")
    with open(WIKT / "orthography_fixes.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["page", "status", "changes"])
        for it in items:
            w.writerow([it["title"], "planned", "; ".join(f"{k}: {o} → {n}" for k, o, n in it["changes"])])
        for t, why in unmatched:
            w.writerow([t, "unmatched", why])
        for lv, t, d in person:
            w.writerow([f"{lv}/{t}", "needs a person", f"redirect leads to another stem: {d}"])
    print(f"root pages: {sum(m['action'] == 'move' for m in moves)} to move, {sum(m['action'] == 'merge' for m in moves)} to merge, {sum(m['action'] == 'redirect' for m in moves)} already redirects")
    print(f"{len(items)} pages planned ({sum(len(i['changes']) for i in items)} respellings), {len(unmatched)} unmatched, {len(person)} redirects to another stem (needs a person)")
    print("see data/wiktionary/orthography_fixes.tsv; diffs: show")
    return items, unmatched, person

def extend_corpus_for_roots(api, corpus_file, log=print):
    """Add to the corpus the pages that link to a root, bare or hyphenated (ʔbd, ʔ-b-d), found through the link tables of every root the corpus mentions."""
    from wikt_wanted import scan
    corpus = json.loads(corpus_file.read_text(encoding="utf-8"))
    class Rec:
        def __init__(self): self.k = set()
        def get(self, key, default=None): self.k.add(key); return None
    rec = Rec()
    for text in corpus.values():
        fix_text(text, rec)
    probe = set()
    for lv, stem in rec.k:
        std = standardise(stem)[0]
        bare = std.replace("-", "")
        r = rootify(bare)
        if r != bare and "-" not in std or r == std and "-" in std:         # a root, in either spelling
            for form in {std, bare, r, stem}:
                probe.add(PFX[lv] + form)
    cache = scan(sorted(probe), log=lambda *_: None)
    linkers = {l for t in probe for l in ((cache.get(t) or {}).get("links") or [])} - set(corpus)
    linkers = {l for l in linkers if editable(l)}
    got = api.pages(sorted(linkers))
    corpus.update({t: v[2] for t, v in got.items()})
    corpus_file.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    log(f"  corpus: {len(got)} more pages through {len(probe)} root titles")

def root_moves(api):
    """The Proto-Semitic / Proto-West Semitic titles that are bare roots (ʔdm, npy, rpy ...): each should be the hyphenated root (ʔ-d-m, n-p-y, r-p-y).
    -> [dict(level, title, target, action: move | merge | redirect, target_state)] with the live state of both pages."""
    from wikt_orthography import load_titles
    pairs = []
    for lv, st in load_titles():
        new = rootify(standardise(st)[0])
        if new != nfc(st) and "-" not in st:
            pairs.append((lv, nfc(st), new))
    live = api.pages([PFX[lv] + t for lv, t, _ in pairs] + [PFX[lv] + n for lv, _, n in pairs])
    out = []
    for lv, t, n in pairs:
        src, dst = live.get(nfc(PFX[lv] + t)), live.get(nfc(PFX[lv] + n))
        sk = "redirect" if src and re.match(r"\s*#REDIRECT", src[2], re.I) else "page" if src else "absent"
        dk = "absent" if not dst else "redirect" if re.match(r"\s*#REDIRECT", dst[2], re.I) else "page"
        if sk != "page":
            action = "redirect" if sk == "redirect" else "absent"
        elif dk == "absent":
            action = "move"
        elif dk == "redirect" and nfc(t) in nfc(dst[2]):                          # the target is a redirect back to this page: a move over it is allowed
            action = "move"
        else:
            action = "merge"
        out.append(dict(level=lv, title=t, target=n, action=action, target_state=dk))
    return out

def diff_of(item):
    a, b = item["old"].splitlines(), item["new"].splitlines()
    return "\n".join(l for l in difflib.unified_diff(a, b, "current", "proposed", n=0, lineterm="") if not l.startswith(("---", "+++")))

def apply(user, bot=False, api=None, ask=input, pause=6.0, out=print):
    plan_f = OUT / "plan.json"
    if not plan_f.exists():
        raise SystemExit("run `plan` first")
    saved = json.loads(plan_f.read_text(encoding="utf-8"))
    items, mapping = saved["items"], {(lv, b): g for lv, b, g in saved["mapping"]}      # the mapping the plan was made with
    api = api or Api()
    api.login(user, os.environ.get("WIKT_PASSWORD") or getpass.getpass(f"bot password for {user}: "))
    log = OUT / "applied.tsv"
    done = {r.split("\t")[0] for r in log.read_text(encoding="utf-8").splitlines()} if log.exists() else set()
    everything = False
    for n, it in enumerate(items, 1):
        if it["title"] in done:
            continue
        cur = api.pages([it["title"]]).get(it["title"])
        if cur is None:
            continue
        if cur[0] != it["revid"]:                                  # edited since the plan: recompute from the live text
            new, changes = fix_text(cur[2], GenericMap(mapping))
            it = dict(it, revid=cur[0], old=cur[2], new=new, changes=changes)
        if not it["changes"]:
            continue
        out(f"\n[{n}/{len(items)}] {it['title']}   https://en.wiktionary.org/wiki/{urllib.parse.quote(it['title'])}\n{diff_of(it)}")
        ans = "y" if everything else ask("apply? [y]es / [n]o / [a]ll the rest / [q]uit: ").strip().lower()[:1]
        if ans == "q":
            break
        if ans == "a":
            everything, ans = True, "y"
        if ans != "y":
            continue
        r = api.edit(it["title"], it["new"], summary_for(it["changes"]), it["revid"], bot=bot)
        ok = r.get("edit", {}).get("result") == "Success"
        out("  done" if ok else "  FAILED: " + json.dumps(r)[:200])
        if ok:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"{it['title']}\t{r['edit'].get('newrevid', '')}\n")
        time.sleep(pause)

# ---------------------------------------------------------------- manual route: a user script + a checklist page
SITE = BUILD.parent / "site"
LOADER = r"""
(function () {
  var MAP = __MAP__;
  var CLOSE_FLAG = "asemRespellPending";                                      // sessionStorage: the exact title a respell save is in flight for, in this tab
  WiktRespell.setNotation(__VARIANTS__, __MANUAL__, __CONSONANTS__);
  // Runs on EVERY page load (not just edit pages): if this tab just saved the page it was flagged for (we have
  // landed somewhere that is not the edit form any more), tell the checklist tab which page is done and close --
  // no manual tab-switching. Keyed by the exact title, not just a boolean, so several tabs open at once each
  // report their own result without tripping over each other's flag.
  try {
    var pending = sessionStorage.getItem(CLOSE_FLAG);
    if (pending && mw.config.get("wgAction") !== "edit") {
      sessionStorage.removeItem(CLOSE_FLAG);                                 // stale either way: consume it regardless of what follows
      if (pending === mw.config.get("wgPageName").replace(/_/g, " ")) {      // only report/close if this really is the page we saved
        if (window.opener) { try { window.opener.postMessage({ asemRespellSaved: pending }, "*"); } catch (e) {} }
        window.close();                                                      // no-op if the tab was not opened by script; never errors
      }
    }
  } catch (e) {}
  mw.loader.using(["jquery.textSelection"]).then(function () { $(function () {
    if (mw.config.get("wgAction") !== "edit" || !/[?&]respell=1(&|$)/.test(location.search)) return;   // only for the links of the checklist page
    var $ta = $("#wpTextbox1");
    if (!$ta.length) { mw.notify("Respell: no plain edit box here (turn CodeMirror off).", { type: "error", autoHide: false }); return; }
    var rt = /[?&]retarget=([^&]+)/.exec(location.search), rtm = rt && /^(PWS?|PS):(.+)>(.+)$/.exec(decodeURIComponent(rt[1])), one = {};   // &retarget=PS:ṯ-ḳ-l>ṯḳl: point that one term elsewhere (root -> verb), nothing else
    if (rtm) one[rtm[1] + "\t" + rtm[2]] = rtm[3];
    var r = WiktRespell.fixText($ta.textSelection("getContents"), rtm ? one : MAP, !rtm);
    if (!r.changes.length) { mw.notify("Respell: nothing to change on this page (already fixed?).", { type: "warn", autoHide: false }); return; }
    $ta.textSelection("setContents", r.text);
    var seen = {}, pairs = [];
    r.changes.forEach(function (c) { var k = "*" + c[1] + " → *" + c[2]; if (!seen[k]) { seen[k] = 1; pairs.push(k); } });
    if (rtm) $("#wpSummary").val("point the Proto-Semitic reference at the verb *" + rtm[3] + ", not the root *" + rtm[2] + " (script-assisted)");
    else $("#wpSummary").val("update Proto-Semitic reference to its current WT:ASEM title (" + pairs.slice(0, 4).join(", ") + (pairs.length > 4 ? " …" : "") + ") (script-assisted)");
    $("#wpMinoredit").prop("checked", true);                                  // minor edit
    $("#wpWatchthis").prop("checked", false);                                 // and do not add the page to the watchlist
    mw.notify("Respell: " + r.changes.length + " change(s). Check the diff, then Save.", { autoHide: false });
    setTimeout(function () { $("#wpDiff").trigger("click"); }, 400);
    var form = document.getElementById("editform");
    if (form) form.addEventListener("submit", function (e) {
      // #editform has three submit buttons (Save, Show changes, Preview); "Show changes" is auto-clicked above
      // and must NOT arm the close-and-report -- only a real Save should.
      if (!(e.submitter && e.submitter.id === "wpSave")) return;
      try { sessionStorage.setItem(CLOSE_FLAG, mw.config.get("wgPageName").replace(/_/g, " ")); } catch (e2) {}
    });
  }); });
})();
"""
def userscript(mapping):
    variants = json.dumps([[nfc(a), nfc(b)] for a, b in VARIANTS], ensure_ascii=False)
    manual = json.dumps([nfc(m) for m in MANUAL], ensure_ascii=False)
    consonants = json.dumps(CONSONANTS, ensure_ascii=False)
    core = (Path(__file__).resolve().parent / "respell_core.js").read_text(encoding="utf-8")
    m = {f"{lv}\t{b}": g for (lv, b), g in sorted(mapping.items())}
    return "// ASEM respeller (https://github.com/iwsfutcmd/sed-to-wiktionary, scripts/respell_core.js). Acts only on edit links ending in &respell=1.\n" + core.strip() + "\n" + \
        LOADER.replace("__MAP__", json.dumps(m, ensure_ascii=False, indent=1)).replace("__VARIANTS__", variants).replace("__MANUAL__", manual).replace("__CONSONANTS__", consonants)

def checklist():
    """Write site/orthography_fix.html (the page you click through) and site/wikt_respell.user.js from build/orth_fixes/plan.json."""
    saved = json.loads((OUT / "plan.json").read_text(encoding="utf-8"))
    mapping = {(lv, b): g for lv, b, g in saved["mapping"]}
    rows = read_tsv(WIKT / "orthography_fixes.tsv")
    survey = {(r["level"], nfc(r["title"])): r for r in read_tsv(WIKT / "orthography_survey.tsv")}
    items = []
    for it in saved["items"]:
        agg = {}
        for _, o, n in it["changes"]:
            agg[(o, n)] = agg.get((o, n), 0) + 1
        items.append(dict(title=it["title"], changes=[f"*{o} → *{n}" + (" (new stem)" if nfc(standardise(o)[0]) != nfc(n) else "") + (f" ×{c}" if c > 1 else "") for (o, n), c in agg.items()]))
    person = []
    for r in rows:
        if r["status"] == "needs a person":
            lv, t = r["page"].split("/", 1)
            sv = survey.get((lv, nfc(t)), {})
            person.append(dict(from_=t, to=r["changes"].split(": ", 1)[-1], page=PFX[lv] + t, n=int(sv.get("n_links") or 0)))
    for p in person:
        p["from"] = p.pop("from_")
    indirect = [r["page"] for r in rows if r["status"] == "unmatched" and r["changes"].startswith("linked through")]
    moves = [m for m in saved.get("moves", []) if m["action"] in ("move", "merge", "redirect")]
    new = []                                                   # drafts not yet on Wiktionary (wiktionary_drafts/*.wiki; posted ones are moved to done/)
    for f in sorted((ROOT / "wiktionary_drafts").glob("Proto-*Semitic_*.wiki")):
        m = re.match(r"Proto-(West_)?Semitic_(.+)\.wiki$", f.name)
        new.append(dict(title=("PWS " if m.group(1) else "") + m.group(2), page="Reconstruction:Proto-" + ("West " if m.group(1) else "") + "Semitic/" + m.group(2), text=f.read_text(encoding="utf-8")))
    rv = json.loads((OUT / "root_verb.json").read_text(encoding="utf-8")) if (OUT / "root_verb.json").exists() else []
    data = json.dumps(dict(items=items, person=person, indirect=indirect, moves=moves, new=new, rootverb=rv, pfx=PFX), ensure_ascii=False).replace("</", "<\\/")
    us = userscript(mapping)
    html = (Path(__file__).resolve().parent / "respell_checklist.template.html").read_text(encoding="utf-8")
    html = html.replace("__DATA__", data).replace("__TOTAL__", str(len(items))).replace("__NPERSON__", str(len(person))).replace("__NINDIRECT__", str(len(indirect))).replace("__NMOVES__", str(sum(m["action"] != "redirect" for m in moves)))
    html = html.replace("__USERSCRIPT__", us.replace("&", "&amp;").replace("<", "&lt;"))
    SITE.mkdir(exist_ok=True)
    (SITE / "orthography_fix.html").write_text(html, encoding="utf-8")
    (SITE / "wikt_respell.user.js").write_text(us, encoding="utf-8")
    print(f"site/orthography_fix.html ({len(html) // 1024} KB, {len(items)} pages, {len(person)} to decide, {len(indirect)} indirect) and site/wikt_respell.user.js")

def main(argv):
    if not argv or argv[0] not in ("plan", "show", "apply", "checklist"):
        print(__doc__); return 2
    if argv[0] == "plan":
        plan()
    elif argv[0] == "checklist":
        checklist()
    elif argv[0] == "show":
        items = json.loads((OUT / "plan.json").read_text(encoding="utf-8"))["items"]
        for it in items:
            if len(argv) == 1 or it["title"] in argv[1:]:
                print(f"\n== {it['title']}\n{diff_of(it)}")
    else:
        user = argv[argv.index("--user") + 1] if "--user" in argv else os.environ.get("WIKT_USER")
        if not user:
            raise SystemExit("give --user NAME (or env WIKT_USER)")
        apply(user, bot="--bot" in argv)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
