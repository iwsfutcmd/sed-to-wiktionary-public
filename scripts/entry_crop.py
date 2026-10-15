"""Render one printed SED entry (from its heading to the next heading, across a page break) as one image, to read it by eye.
usage: entry_crop.py VOL KEY [DPI]   e.g. entry_crop.py 1 N238   -> build/crops/entry_v1_N238.png
Needs the PDF (pdf/volN.pdf) and data/intermediate/heads_vN.json. Pages and positions are PDF-page based (see paths.py)."""
import json, subprocess, sys
from PIL import Image
from paths import VOLS, heads, BUILD

def main(v, key, dpi=200):
    hs = json.loads(heads(v).read_text(encoding="utf-8"))
    best = {}
    for a in hs:
        k = a["sec"] + str(a["n"])
        if k not in best or len(a["text"]) > len(best[k]["text"]):
            best[k] = a
    a = best[key]
    order = sorted(best.values(), key=lambda b: (b["page"], b["y0"]))
    nxt = order[order.index(a) + 1] if order.index(a) + 1 < len(order) else None
    s = dpi / 72
    out = BUILD / "crops"; out.mkdir(parents=True, exist_ok=True)
    segs = []
    pages = range(a["page"], (nxt["page"] if nxt else a["page"]) + 1)
    for p in pages:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(p), "-l", str(p), "-png", "-singlefile", str(VOLS[v]["pdf"]), str(out / "pg")],
                       check=True, stderr=subprocess.DEVNULL)
        im = Image.open(out / "pg.png")
        top = a["y0"] - 3 if p == a["page"] else 40                      # skip the running head on continuation pages
        bot = (nxt["y0"] - 3) if nxt and p == nxt["page"] else a["ph"] - 20
        segs.append(im.crop((int(20 * s), int(top * s), im.width - int(20 * s), int(bot * s))))
    canvas = Image.new("RGB", (max(g.width for g in segs), sum(g.height + 12 for g in segs)), "white")
    y = 0
    for g in segs:
        canvas.paste(g, (0, y)); y += g.height + 12
    dest = out / f"entry_v{v}_{key}.png"
    canvas.save(dest)
    print(dest, canvas.size)

if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 200)
