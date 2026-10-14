"""Classify each glottal glyph in a heading as ʔ or ʕ from the direction of its hook.
The OCR text layer cannot tell them apart, so the page raster is analysed instead.
usage: glot.py VOL [OUT]   (default OUT = data/intermediate/glot_vN.json; keys 'N<n>' / 'V<n>')"""
import json, sys
import numpy as np, cv2
from scipy import ndimage as ndi
from paths import VOLS, heads, glot, crops
from crops import page_img   # renders build/vN/crops/p<page>.png on demand

S = 400 / 72
THRESH = 4      # hook score > THRESH -> ʔ, otherwise ʕ

def best_heads(v):
    best = {}
    for a in json.loads(heads(v).read_text(encoding="utf-8")):
        k = (a['sec'], a['n'])
        if k not in best or len(a['text']) > len(best[k]['text']):
            best[k] = a
    return best

def glyphs(v, a):
    x0, x1 = VOLS[v]["box"]
    crops(v).mkdir(parents=True, exist_ok=True)
    page_img(v, a['page'])
    im = cv2.imread(str(crops(v) / f"p{a['page']}.png"), 0)
    y0, y1 = int((a['y0'] - 3) * S), int((min(a['y1'], a['y0'] + 11) + 3) * S)
    sub = im[y0:y1, int(x0 * S):int(x1 * S)]
    lab, _ = ndi.label(sub < 140, structure=np.ones((3, 3)))
    boxes = ndi.find_objects(lab)
    dims = [(sl[1].start, sl[1].stop - sl[1].start, sl[0].stop - sl[0].start, sl[0].stop) for sl in boxes]
    xs = [d for d in dims if 28 <= d[2] <= 37 and d[1] >= 24]          # x-height letters
    if not xs:
        return []
    base = np.median([d[3] for d in xs])
    res = []
    for i, sl in enumerate(boxes, 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if 13 <= w <= 24 and 27 <= h <= 38 and abs(sl[0].stop - (base - 8)) <= 3:
            ys, xs_ = np.nonzero(lab[sl] == i)
            res.append((sl[1].start, float(xs_[ys < h * 0.45].mean() - xs_[ys > h * 0.7].mean())))
    return sorted(res)

def run(v, out):
    calls = {sec + str(n): ''.join('ʔ' if sc > THRESH else 'ʕ' for _, sc in glyphs(v, a))
             for (sec, n), a in best_heads(v).items()}
    out.write_text(json.dumps(calls, ensure_ascii=False), encoding="utf-8")
    return calls

if __name__ == "__main__":
    v = int(sys.argv[1])
    from pathlib import Path
    run(v, Path(sys.argv[2]) if len(sys.argv) > 2 else glot(v))
