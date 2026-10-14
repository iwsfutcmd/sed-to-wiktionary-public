"""Locate 'No. n.' headings (and their y-extent) in a pdftotext -bbox-layout dump.
usage: locate.py VOL     (reads build/vN/bbl.html, writes data/intermediate/heads_vN.json)"""
import re, json, sys, html
from collections import Counter
from paths import VOLS, bbox, heads

def run(v):
    P = VOLS[v]
    t = bbox(v).read_text(encoding="utf-8")
    pages = re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', t, re.S)
    recs = []
    for i, (w, h, body) in enumerate(pages):
        pno = P["first"] + i
        lines = []
        for lm in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', body, re.S):
            x0, y0, x1, y1 = map(float, lm.groups()[:4])
            words = [html.unescape(x) for x in re.findall(r'>([^<]*)</word>', lm.group(5))]
            lines.append((y0, x0, y1, x1, words))
        lines.sort()
        for (y0, x0, y1, x1, words) in lines:
            s = ''.join(words)
            m = re.match(r'^No\.(\d+)\.', s)
            if not m or y0 < 35:
                continue
            if words[-1].isdigit() and x1 > 330 and len(words) > 3:   # running header
                continue
            ymax = y1
            for (a0, b0, a1, b1, w2) in lines:                        # gloss on the same baseline
                if abs(a0 - y0) < 4 and (a0, b0) != (y0, x0):
                    ymax = max(ymax, a1)
            for (a0, b0, a1, b1, w2) in lines:                        # quoted continuation lines
                if y1 - 1 <= a0 <= y1 + 16 and w2 and w2[0][:1] in "'’‘":
                    ymax = max(ymax, a1)
            recs.append(dict(page=pno, n=int(m.group(1)), y0=y0, y1=ymax,
                             sec='V' if pno >= P["vstart"] else 'N',
                             pw=float(w), ph=float(h), text=' '.join(words)))
    heads(v).write_text(json.dumps(recs, ensure_ascii=False, indent=0), encoding="utf-8")
    for sec in 'NV':
        ns = sorted(r['n'] for r in recs if r['sec'] == sec)
        c = Counter(ns)
        if ns:
            print(sec, len(ns), 'unique', len(c), 'max', max(ns),
                  'dups', [k for k, n in c.items() if n > 1][:20],
                  'missing', [k for k in range(1, max(ns) + 1) if k not in c][:30])

if __name__ == "__main__":
    run(int(sys.argv[1]))
