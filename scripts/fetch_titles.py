"""Snapshot every Reconstruction:Proto-Semitic/ and Proto-West_Semitic/ title via the MediaWiki API
(namespace 118). Uses urllib; honours HTTPS_PROXY. usage: fetch_titles.py"""
import json, time, urllib.error, urllib.parse, urllib.request
from paths import WIKT

API = "https://en.wiktionary.org/w/api.php"
UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}

def get(url, tries=6):
    """GET + parse JSON; back off on 429/5xx (honouring Retry-After)."""
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or i == tries - 1:
                raise
            time.sleep(float(e.headers.get("Retry-After") or 0) or 2 ** (i + 2))

def pull(prefix):
    titles, cont = [], None
    while True:
        q = dict(action="query", list="allpages", apnamespace=118, aplimit="max", format="json", apprefix=prefix)
        if cont:
            q["apcontinue"] = cont
        d = get(API + "?" + urllib.parse.urlencode(q))
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
