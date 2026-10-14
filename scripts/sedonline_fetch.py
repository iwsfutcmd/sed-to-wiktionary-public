"""Crawl SEDonline (http://sed-online.ru/, the Kogan et al. Semitic Etymological Database) into build/sedonline/.

  list/NNN.html   /reconstructions?reconstructions_page=NNN   (index of all reconstructions)
  rec/ID.html     /reconstructions/ID                          (a reconstruction + its cited words)

Resumable: files already on disk are skipped. Polite: a short pause between requests, a few threads, an
identifying User-Agent, retries with backoff. Only the reconstruction pages are fetched; each already lists
its words (language, form, gloss, reference), so /words/ID pages add nothing for this project.
usage: sedonline_fetch.py [--workers 4] [--delay 0.3] [--limit N]"""
import argparse, re, time, threading, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from paths import BUILD

BASE = "http://sed-online.ru"
UA = {"User-Agent": "sed-to-wiktionary/1.0 (research; https://github.com/iwsfutcmd/sed-to-wiktionary)"}
OUT = BUILD / "sedonline"
_lock = threading.Lock()

def get(path, dest, delay, tries=5):
    if dest.exists() and dest.stat().st_size:
        return False
    for i in range(tries):
        try:
            time.sleep(delay)
            raw = urllib.request.urlopen(urllib.request.Request(BASE + path, headers=UA), timeout=60).read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(dest)
            return True
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text("<!-- 404 -->", encoding="utf-8")
                return True
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"giving up on {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--limit", type=int, default=0, help="only fetch the first N reconstruction pages (testing)")
    a = ap.parse_args()

    first = OUT / "list" / "001.html"
    get("/reconstructions", first, a.delay)
    npages = max(int(n) for n in re.findall(r"reconstructions_page=(\d+)", first.read_text(encoding="utf-8")))
    print("list pages:", npages)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(lambda n: get(f"/reconstructions?reconstructions_page={n}", OUT / "list" / f"{n:03d}.html", a.delay),
                    range(2, npages + 1)))

    ids = set()
    for f in sorted((OUT / "list").glob("*.html")):
        ids |= {int(i) for i in re.findall(r'href="/reconstructions/(\d+)"', f.read_text(encoding="utf-8"))}
    ids = sorted(ids)[: a.limit or None]
    print("reconstructions:", len(ids))
    done = 0
    def one(i):
        nonlocal done
        get(f"/reconstructions/{i}", OUT / "rec" / f"{i}.html", a.delay)
        with _lock:
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(ids)}", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, ids))
    print("done")

if __name__ == "__main__":
    main()
