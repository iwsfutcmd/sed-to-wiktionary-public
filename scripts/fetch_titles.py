"""Snapshot every Reconstruction:Proto-Semitic/ and Proto-West_Semitic/ title via the MediaWiki API
(namespace 118). Uses urllib; honours HTTPS_PROXY. usage: fetch_titles.py"""
import json, urllib.parse, urllib.request
from paths import WIKT

API = "https://en.wiktionary.org/w/api.php"
UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}

def pull(prefix):
    titles, cont = [], None
    while True:
        q = dict(action="query", list="allpages", apnamespace=118, aplimit="max", format="json", apprefix=prefix)
        if cont:
            q["apcontinue"] = cont
        d = json.load(urllib.request.urlopen(urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers=UA), timeout=60))
        titles += [p["title"] for p in d["query"]["allpages"]]
        cont = d.get("continue", {}).get("apcontinue")
        if not cont:
            return titles

if __name__ == "__main__":
    WIKT.mkdir(parents=True, exist_ok=True)
    for prefix, name in (("Proto-Semitic/", "wik_ps.json"), ("Proto-West_Semitic/", "wik_pws.json")):
        t = pull(prefix)
        (WIKT / name).write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
        print(prefix, len(t))
