"""Repo-relative paths shared by every script (no absolute paths anywhere)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "pdf"                    # vol1.pdf, vol2.pdf (not in git)
BUILD = ROOT / "build"                # scratch: bbox layouts, page rasters, crops (not in git)
DATA = ROOT / "data"
INTER = DATA / "intermediate"         # committed: heads, glottal calls, hand-transcribed raw TSVs
WIKT = DATA / "wiktionary"            # committed: dated snapshot of Wiktionary titles
SITE = ROOT / "site"

# Per-volume parameters. Pages are PDF page indices (not printed page numbers).
# box = x-range (pt) of the headword column used when cropping a heading.
VOLS = {
    1: dict(pdf=PDF / "vol1.pdf", first=155, last=488, vstart=424, box=(58, 328),
            raw=[("N", INTER / "raw_v1_N.tsv"), ("V", INTER / "raw_v1_V.tsv")],
            overrides={"N205": "ʔ", "N243": "ʕ", "V37": "ʔ", "V62": "ʕʕ"}),
    2: dict(pdf=PDF / "vol2.pdf", first=94, last=440, vstart=10**9, box=(25, 400),
            raw=[("N", INTER / "raw_v2_N.tsv")], overrides={}),
}
def bbox(v): return BUILD / f"v{v}" / "bbl.html"
def heads(v): return INTER / f"heads_v{v}.json"
def glot(v): return INTER / f"glot_v{v}.json"
def crops(v): return BUILD / f"v{v}" / "crops"
