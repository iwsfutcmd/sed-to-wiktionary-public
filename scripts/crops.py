"""Render 400-dpi page rasters and stack heading crops into batch_NN.png for visual transcription.
usage: crops.py VOL [PER_BATCH=10]   (writes build/vN/crops/)"""
import json, subprocess, sys, re
from PIL import Image, ImageDraw
from paths import VOLS, heads, crops

DPI = 400

def best_heads(v):
    best = {}
    score = lambda r: (bool(re.match(r'^N ?o ?\. ?\d+ ?\. ?\*', r['text'])), len(r['text']))
    for r in json.loads(heads(v).read_text(encoding="utf-8")):
        k = (r['sec'], r['n'])
        if k not in best or score(r) > score(best[k]):
            best[k] = r
    return sorted(best.values(), key=lambda r: (r['sec'], r['n']))

def page_img(v, p):
    f = crops(v) / f"p{p}.png"
    if not f.exists():
        subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(p), '-l', str(p), '-png', '-singlefile',
                        str(VOLS[v]["pdf"]), str(f.with_suffix(''))], check=True, stderr=subprocess.DEVNULL)
    return Image.open(f).convert('RGB')

def run(v, per):
    crops(v).mkdir(parents=True, exist_ok=True)
    recs, s = best_heads(v), DPI / 72
    x0, x1 = VOLS[v]["box"]
    batches = []
    for bi in range(0, len(recs), per):
        chunk = recs[bi:bi + per]
        cs = [page_img(v, r['page']).crop((int(x0 * s), int((r['y0'] - 3) * s), int(x1 * s), int((r['y1'] + 3) * s)))
              for r in chunk]
        canvas = Image.new('RGB', (max(c.width for c in cs), sum(c.height + 10 for c in cs)), 'white')
        d, y = ImageDraw.Draw(canvas), 0
        for c in cs:
            canvas.paste(c, (0, y)); y += c.height
            d.line([(0, y + 4), (canvas.width, y + 4)], fill=(200, 200, 200), width=1); y += 10
        fn = crops(v) / f"batch_{bi // per + 1:02d}.png"
        canvas.save(fn)
        batches.append((fn.name, [(r['sec'], r['n'], r['page']) for r in chunk]))
    (crops(v) / "manifest.json").write_text(json.dumps(batches), encoding="utf-8")
    print(len(recs), 'headings,', len(batches), 'batches')

if __name__ == "__main__":
    run(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 10)
