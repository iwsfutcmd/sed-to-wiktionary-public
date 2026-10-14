"""Render a 650-dpi strip of selected headings for manual checking.
usage: zoom.py VOL KEY...   e.g. zoom.py 1 N34 V5   (writes build/zoom_out.png)"""
import sys, json, subprocess
from PIL import Image
from paths import VOLS, heads, BUILD

v, keys = int(sys.argv[1]), sys.argv[2:]
best = {}
for a in json.loads(heads(v).read_text(encoding="utf-8")):
    k = a['sec'] + str(a['n'])
    if k not in best or len(a['text']) > len(best[k]['text']):
        best[k] = a
BUILD.mkdir(exist_ok=True)
tmp, s, tiles = BUILD / "zt", 650 / 72, []
for k in keys:
    a = best[k]
    subprocess.run(['pdftoppm', '-r', '650', '-f', str(a['page']), '-l', str(a['page']), '-png', '-singlefile',
                    str(VOLS[v]["pdf"]), str(tmp)], check=True, stderr=subprocess.DEVNULL)
    im = Image.open(str(tmp) + ".png")
    x0 = VOLS[v]["box"][0]
    tiles.append(im.crop((int(x0 * s), int((a['y0'] - 2) * s), int((x0 + 142) * s), int((min(a['y1'], a['y0'] + 11) + 2) * s))))
c = Image.new('RGB', (max(t.width for t in tiles), sum(t.height + 8 for t in tiles)), 'white')
y = 0
for t in tiles:
    c.paste(t, (0, y)); y += t.height + 8
c.save(BUILD / "zoom_out.png"); print(c.size)
