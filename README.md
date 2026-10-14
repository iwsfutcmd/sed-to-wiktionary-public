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

- `data/vol1/sed_vol1_reflexes.tsv` (6,419 rows), `data/vol2/sed_vol2_reflexes.tsv` (3,637 rows) and their concatenation `data/sed_vol1_vol2_reflexes.tsv`: the **Semitic reflexes** listed under each reconstruction (the block before the `Afras.` sub-entry; `||` comments and `0` footnotes are skipped).
  - Columns: `vol, section, no` (join key to the reconstruction tables), `branch` (the `[1]`-`[9]` group number as printed), `lang` (SED siglum, e.g. `Arb.`, `Gog. Sod.`), `form`, `note` (qualifier after the form, e.g. `(redupl.)`), `gloss`, `ref` (bibliographic reference as printed), `flags`.
  - `flags`: `uncertain` (`(?)` before the siglum), `cf` (`Cf.`), `shared_gloss` (gloss given once after a comma-run of forms, copied to each), `quote_garbled` (an opening or closing quote was lost in OCR, so form/gloss/ref boundaries are unreliable: check against the page).
  - **Forms are raw text-layer OCR, not normalised**: diacritics are lost or garbled and glottals appear as `?`, `H`, `f` etc. (ʔ/ʕ were only recovered for the reconstructions, from image crops). Treat them as search keys for locating the form on the page, not as transcriptions. Roughly 10% of rows carry `quote_garbled`; rows may also be missing where a line was mis-segmented. Not yet extracted: the Afro-Asiatic comparanda.

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

## Reproducing
Everything is repo-relative (`scripts/paths.py`); no absolute paths.

```
make            # tables + site from the committed intermediates (no PDFs, no network)
make titles     # refresh data/wiktionary/*.json from the MediaWiki API (network), then `make`
```
`make` rebuilds `data/**/*.tsv`, `data/intermediate/sed_all.{json,tsv}` and `site/index.html` byte-identically to what is committed (checked).

Regenerating the intermediates from the books needs `pdf/vol1.pdf` and `pdf/vol2.pdf` (the SED scans, tracked in this private repo; poppler-utils, Pillow, OpenCV, SciPy required):

| step | command | produces |
|---|---|---|
| heading positions | `make heads-1 heads-2` | `data/intermediate/heads_vN.json` (verified identical to the committed files) |
| glottal calls | `make glot-1 glot-2` | `data/intermediate/glot_vN.json` (hook-direction classifier, threshold 4; verified identical to the committed files) |
| Semitic reflexes | `make reflexes-1 reflexes-2` | `data/volN/sed_volN_reflexes.tsv` and the concatenation (needs only poppler; not part of plain `make`) |
| crops for reading | `make crops-1 crops-2` | `build/vN/crops/batch_NN.png` |

The step in between is **manual**: forms and glosses in `data/intermediate/raw_v*_*.tsv` (`n<TAB>form<TAB>gloss`, with `Q` marking each glottal) were transcribed by eye from the batch crops, because the PDFs' OCR text layer garbles diacritics. `glot_vN.json` fills the `Q` slots; the four glottals the classifier left empty (1N205, 1N243, 1V37, 1V62) are set by hand in `scripts/paths.py`.

Scripts: `locate.py`, `crops.py`, `glot.py`, `zoom.py` (650-dpi spot checks), `build_sed.py`, `fetch_titles.py`, `wikt_match.py`, `build_site.py`.
