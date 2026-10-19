# Roots in Proto-Semitic: `p-ʕ-l`

Proposal (decided 2026-10-19): a root is written with a hyphen between the radicals and none at the end, `ʔ-b-d`, `p-ʕ-l`. A stem keeps its trailing hyphen (`paʕl-`), a vocalised verb stem is `paʕal-`. Radicals are written as they are reconstructed: a two-radical root is two (`b-n`, `ʔ-š`), a root with a doubled radical keeps both (`ḏ-b-b`, `m-d-d`). Nothing is merged or duplicated by the tools.

## What exists now (measured 2026-10-19, 1,580 pages + 426 titles)
- 61 distinct roots mentioned 161 times: 79 bare (`ʔbd`, `ṯql`, `ʿṯn`), 82 hyphenated (`q-n-y` on 41 pages, `q-d-m` on 14). Five roots are written both ways.
- 19 root-like titles in two styles. Hyphenated already: `d-b-r`, `ʔ-b-d`, `ʔ-b-r`, `ʔ-d-w`, `ḳ-r-ʔ` (PS), `ʔ-d-r` (PWS). Bare: `npy`, `ʔbd`, `ʔdm`, `ʔtm`, `ʔḏn`, `ʔḫḏ`, `rpʔ` (PS) and `rpy`, `rpʔ`, `ʔdm`, `ʔdr`, `ʔdw`, `ʔḏn` (PWS).

## What the tools do
- **References** (`scripts/wikt_fix_refs.py`, `scripts/respell_core.js`): any `sem-pro` / `sem-wes-pro` term made only of 2 to 5 consonants, no hyphen, becomes the hyphenated root after the ordinary respelling (`ṯql` → `ṯ-ḳ-l`, `ʿṯn` → `ʕ-ṯ-n`, `ʾš` → `ʔ-š`). Terms with a vowel, a `V`, a trailing hyphen, `x̣` or `č`, or of another language, are left alone. The pages go through the checklist, so a consonant-only word that is not a root can be skipped. 35 distinct roots on 113 mentions in the current plan.
- **Titles**: the checklist lists the root pages to move with a prefilled move form (10 moves). Where the hyphenated page already exists (`ʔbd` → `ʔ-b-d`, PWS `ʔdr` → `ʔ-d-r`) the two pages have to be merged by hand or by an administrator. `rpʔ` and `rpˀ` at Proto-Semitic are redirects to the Proto-West Semitic page and should be pointed at its new title (`r-p-ʔ`) after that move.

## For the guidelines
ASEM's "Entry name: nominal, adjectival and verbal entries should just be the root followed by a hyphen" means the stem. A line is needed that defines a root entry as `C-C-C` with hyphens between radicals and no trailing hyphen, and that quadriliteral roots take four (`b-r-ḳ-r`).

## Not checked
How `{{root}}`, the Hebrew root-box template and the Arabic root appendices display roots, and whether any of them expect a different title for the Proto-Semitic root page.
