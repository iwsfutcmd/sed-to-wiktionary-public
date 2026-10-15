"""Collect the {{cunsp}} phonetic spellings (cuneiform + transliteration) of Wiktionary's Akkadian lemma pages -> tests/data/akk_cunsp_gold.tsv.
These are the gold pairs for tr2script/cuneiform.py. Patient with the API: honours Retry-After on HTTP 429 (up to ~15 min), pauses
between batches and writes after every batch. usage: akk_gold.py [first N lemmas of Category:Akkadian lemmas, default 500]"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
from paths import ROOT

UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
OUT = ROOT / "tests" / "data" / "akk_cunsp_gold.tsv"

def api(**q):
    data = urllib.parse.urlencode(dict(format="json", formatversion=2, **q)).encode()
    waited = 0
    while True:
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php", data=data, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429 or waited > 900: raise
            w = min(float(e.headers.get("Retry-After") or 20), 60); print(f"429, waiting {w:.0f}s", flush=True); time.sleep(w); waited += w

def main(n=500):
    titles = [m["title"] for m in api(action="query", list="categorymembers", cmtitle="Category:Akkadian lemmas", cmlimit=500,
                                      cmnamespace=0)["query"]["categorymembers"]][:n]
    pairs = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(titles), 50):
        time.sleep(3)
        for p in api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))["query"]["pages"]:
            if "revisions" not in p: continue
            c = p["revisions"][0]["slots"]["main"]["content"]; a = c.find("==Akkadian=="); sec = c[a:] if a >= 0 else ""
            m = re.search(r"\{\{cunsp(.*?)\n\}\}", sec, flags=re.S)
            if m:
                pairs += [(p["title"], k, cun.strip(), tr.strip()) for k, cun, tr in re.findall(r"\|(phon\d*)=([^<\n|]+)<tr:([^>]+)>", m.group(1))]
        OUT.write_text("lemma\tkey\tcuneiform\ttransliteration\n" + "".join("\t".join(t) + "\n" for t in pairs), encoding="utf-8")
        print(f"{min(i + 50, len(titles))}/{len(titles)} lemmas, {len(pairs)} spellings", flush=True)

def from_cache():
    """Add the spellings of Akkadian pages already cached by wikt_draft.py (build/wikt_pages) to the gold file (no network)."""
    from urllib.parse import unquote
    from paths import BUILD
    pairs = []
    for f in sorted((BUILD / "wikt_pages").glob("*.txt")):
        c = f.read_text(encoding="utf-8"); a = c.find("==Akkadian==")
        m = re.search(r"\{\{cunsp(.*?)\n\}\}", c[a:], flags=re.S) if a >= 0 else None
        if m:
            pairs += [(unquote(f.stem), k, cun.strip(), tr.strip()) for k, cun, tr in re.findall(r"\|(phon\d*)=([^<\n|]+)<tr:([^>]+)>", m.group(1))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    have = [tuple(l.split("\t")) for l in OUT.read_text(encoding="utf-8").splitlines()[1:]] if OUT.exists() else []
    merged = have + [p for p in pairs if p not in have]           # merge: never drop what a fuller download collected
    OUT.write_text("lemma\tkey\tcuneiform\ttransliteration\n" + "".join("\t".join(t) + "\n" for t in merged), encoding="utf-8")
    print(len(merged), "spellings (", len(merged) - len(have), "new from", len({p[0] for p in pairs}), "cached lemma pages)")

if __name__ == "__main__":
    if "--from-cache" in sys.argv:
        from_cache()
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 500)
