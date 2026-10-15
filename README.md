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
- `data/vol1/sed_vol1_afras.tsv` (233 rows, 33 `Afras.` sub-entries), `data/vol2/sed_vol2_afras.tsv` (1,121 rows, 79 sub-entries) and the concatenation `data/sed_vol1_vol2_afras.tsv`: the **Afro-Asiatic comparanda** (Egyptian, Berber, Chadic, Cushitic, Omotic) cited under each reconstruction.
  - Columns: `vol, section, no` (join key), `afras_no` (an entry can have several `Afras.` sub-entries), `afras_protoform`, `afras_gloss`, `branch` (printed `[n]`; the numbering differs between volumes, use `family`), `family`, `subgroup` (N./S./E./W./C., `?` if printed `(?)`), `subgroup_proto` (a sub-group reconstruction such as `*?VrVw-`), `lang`, `form`, `note`, `gloss`, `ref`, `flags` (as for reflexes, plus `lang_inherited`: no language given, previous one assumed; `form_id`: printed as `id.`, previous form copied; `prose`: the "form" is a word of running text, probably not a cited form).
  - Same OCR caveats as the reflexes, and language/form boundaries are guessed (leading capitalised words = language name), so some rows have prose fragments in `form`/`note`. The `Sem.` line of each sub-entry is skipped.
- `data/sed_wiktionary_gaps.tsv` (`make gaps`): one row per reconstruction, sorted so the best-attested missing pages come first. `status`: `covered` (a PS/PWS title matches), `same_skeleton` (no matching title, but a page with the same consonants exists, listed in `same_skeleton`: probably a different vocalisation or reconstruction), `gap` (nothing). `n_branches` / `n_langs` count the Semitic branch groups and languages in the reflexes table (`Cf.` rows excluded), `n_afras` the Afro-Asiatic forms. Currently 524 gaps (121 of them attested in 5+ branches), 35 same-skeleton, 78 covered. Based on the 2026-10-14 title snapshot and only on page titles: it does not look at page content or at Wiktionary's descendants lists (not reachable from this environment at the moment).

## Third source: SEDonline (http://sed-online.ru/, crawled 2026-10-14)
The online Semitic Etymological Database (Kogan, Arkhipov et al.; beta) gives real-Unicode forms where the PDFs only have garbled OCR. `make sedonline-fetch` caches its reconstruction pages in `build/sedonline/` (not in git; resumable, throttled); `make sedonline` parses them and builds the comparison. Needs `beautifulsoup4` + `lxml`.
- `data/sedonline/sedonline_reconstructions.tsv` (2,053 rows): `rec_id` (site ID), `level` (PS 873, PWS 430, PCS 201, Proto-MSA 196, PES 109, PC 84, PArm 76, areal 62, PNWS 22), `form` (as printed on the site: ˀ/ˁ for glottals), `norm` (leading `*` dropped, ˀ/ˁ→ʔ/ʕ), `gloss`, `ref`, `sed_ref`, `note`, `parents` / `children` (`Level:rec_id`, other reconstruction levels linked on the page), `n_words`.
  - `sed_ref`: the printed-SED entry the site cites, as `{vol}{N|V}:{no}` (the `vol`/`section`/`no` keys of the SED tables; `1V` = Vol. 1 verbal). Only 613 reconstructions carry one; a bare "SED No. n" without volume is not resolved.
- `data/sedonline/sedonline_words.tsv` (16,499 rows): `rec_id, word_id, lang, form, gloss, ref, note`, one per word cited under a reconstruction (~60 languages, site transcription, not normalised).
- `data/sedonline/sedonline_comparison.tsv`: each SEDonline PS/PWS reconstruction against the Wiktionary title snapshot, `wikt_ps` / `wikt_pws` = `yes` (exact form after folding; `V` patterns are not expanded), `skeleton` (a page with the same consonants under another vocalisation, e.g. SEDonline `*ptḥ` vs Wiktionary `pataḥ-`; titles listed) or `no`; with the printed-SED form it cites, `n_words`, `n_langs`; Wiktionary-missing, best-attested first.
- Results: of 873 PS / 430 PWS reconstructions, 115 / 27 have an exact Wiktionary PS/PWS page and a further 87 / 30 only a page with the same consonants (a different vocalisation, or a stem where SEDonline gives a root). 576 of the 637 printed-SED entries are cited by some SEDonline reconstruction (516 by a PS/PWS one). 386 PS/PWS reconstructions with no SED number and no Wiktionary page of any kind are attested in 5+ languages: candidates beyond the two volumes.
- `data/sedonline/sed_print_vs_site_agreement.tsv` (`sedonline_agree.py`): for the 576 cited entries, whether print and site agree on form, gloss, level (PS) and the set of core languages cited (122 do); the filter for anything that is to be copied to Wiktionary. `wiktionary_drafts/` has draft pages for entries that agree (generated by `scripts/wikt_draft.py`, which looks up script forms on Wiktionary).
- `data/sedonline/sed_print_vs_site.tsv` (`sedonline_missing.py`): every printed SED entry with `status` `cited` (576: a SEDonline reconstruction cites its number), `matched` (36: same consonant skeleton and a shared gloss word, no number) or `not_found` (25: check by hand; `candidates` = closest SEDonline reconstructions by shared gloss word, ranked by skeleton similarity, as `rec_id:why`). Heuristic: it does not model root variants, so a `not_found` entry may exist under a different root.
- `site/sedonline.html` (`make sedonline-site`): self-contained browser for the above (search with diacritic/glottal folding, filters by level, Wiktionary page, printed-SED citation and language count, cited words per language, links to the site and to Wiktionary). `site/sedonline_template.html` is the template.
- GitHub Pages: `.github/workflows/pages.yml` (manual run) publishes only `site/sedonline.html`, as the Pages root. Enable once under Settings → Pages → Source: GitHub Actions. Note that Pages sites are public (and Pages on a private repo needs a paid GitHub plan); `site/index.html` is not deployed.
- The Wiktionary snapshot was refreshed the same day (PS 372, PWS 42→43: `ʔalp-`); `fetch_titles.py` now backs off on HTTP 429.

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
| Afro-Asiatic comparanda | `make afras-1 afras-2` | `data/volN/sed_volN_afras.tsv` and the concatenation |
| crops for reading | `make crops-1 crops-2` | `build/vN/crops/batch_NN.png` |

The step in between is **manual**: forms and glosses in `data/intermediate/raw_v*_*.tsv` (`n<TAB>form<TAB>gloss`, with `Q` marking each glottal) were transcribed by eye from the batch crops, because the PDFs' OCR text layer garbles diacritics. `glot_vN.json` fills the `Q` slots; the four glottals the classifier left empty (1N205, 1N243, 1V37, 1V62) are set by hand in `scripts/paths.py`.

Scripts: `locate.py`, `crops.py`, `glot.py`, `zoom.py` (650-dpi spot checks), `build_sed.py`, `fetch_titles.py`, `wikt_match.py`, `build_site.py`.
