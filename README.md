# sed-to-wiktionary

Reconstructed Proto-Semitic forms extracted from Militarev & Kogan, *Semitic Etymological Dictionary* (SED), Vol. 1 *Anatomy of Man and Animals* (AOAT 278.1, 2000) and Vol. 2 *Animal Names* (AOAT 278.2, 1995), compared against English Wiktionary's Proto-Semitic (PS) and Proto-West Semitic (PWS) reconstruction pages.

## Data
- `data/vol1/sed_vol1_reconstructions.tsv` (382 rows: 298 nominal, 84 verbal) and `data/vol2/sed_vol2_reconstructions.tsv` (255 fauna nominals); `data/sed_vol1_vol2_reconstructions.tsv` is the concatenation.
- Columns: `vol, section, no, protoform, affricate_variant, gloss, wikt_norm, pdf_page, wikt_ps, wikt_ps_title, wikt_pws, wikt_pws_title`.
  - `protoform`: as printed in SED (ʔ/ʕ classified from 400-dpi crops; OCR text layer is unreliable). `affricate_variant`: the ◊ variant.
  - `wikt_norm`: first variant respelled to Wiktionary conventions (ŝ→ś, ṣ̂→ṣ́, ṯ̣→ṱ, γ→ġ, ḳ→q).
  - `wikt_ps` / `wikt_pws`: `yes` (a page title matches some variant of the form), `pattern` (the SED form is schematic, with V for an unspecified vowel, and a title fits it: check by hand), `no`. `*_title` lists the matching title(s).
  - `pdf_page`: page of the PDF file (not the printed page number).
- `data/wiktionary/wik_ps.json`, `wik_pws.json`: snapshot of all `Reconstruction:Proto-Semitic/` (372) and `Reconstruction:Proto-West Semitic/` (42) titles, taken 2026-10-14.

## Method and limits
Matching is on the form only, after folding spelling variants (ʔ/ʾ, ʕ/ʿ, ḏ/ð, ṯ/θ, ḳ/q), expanding `(optional)` material and `a/b` alternations. A word may exist on Wiktionary under a different reconstruction. Ten entries have glyphs flagged "to verify" (see `docs/notation-and-verification-notes.md` and the browser page).

## Results (2026-10-14)
| | entries | in PS | in PWS |
|---|---|---|---|
| Vol. 1 nominal | 298 | 33 | 6 |
| Vol. 1 verbal | 84 | 1 | 0 |
| Vol. 2 fauna | 255 | 27 | 5 |

## Browser
`site/index.html` is the self-contained browsing page (search, filters, PS/PWS badges); `site/template.html` has a `__DATA__` placeholder filled from `data/intermediate/sed_all.json`.

## Scripts
`scripts/` holds the extraction and build pipeline as run (paths assume a working directory with the PDFs, which are not included for copyright reasons): `locate.py`, `crops*.py`, `glot*.py`, `build_all.py`, `fetch_titles.py` (MediaWiki API, namespace 118), `wikt_match.py`.
