# Proto-Semitic / Proto-West Semitic pages vs. WT:ASEM (snapshot 2026-10-15)

Reproduce: `python scripts/wikt_orthography.py --scan --fresh` (scans titles, incoming links and page text through the API; output in this folder).
Standard notation (Wiktionary:Proto-Semitic entry guidelines): `p t ṭ k ḳ ʔ b d g ṯ s š ś ḫ ḥ h ṯ̣ ṣ ṣ́ ḏ z ḡ ʕ r w y l m n`, vowels `a i u ā ī ū`, `V`/`V̄`; entry name = root/stem + hyphen; East + West attestation = Proto-Semitic, West only = Proto-West Semitic.
Variants found: `q ʾ ˀ ʿ ˁ θ θ̣ ṱ ð ṣ̂ ɣ ḍ x̣ č`.

## Resurvey 2026-10-16 (after the moves done by hand)
- The three pages in §1 have been moved: `maraṣ́-` (real page), `ṯ̣aby-`, `ṣaḡir-`; the old titles are redirects. **No non-standard title is a real page any more**: 358 standard titles (385 PS + 43 PWS = 428 titles), 68 redirects from non-standard spellings, 2 redirects with an unreadable letter (`x̣arb-`, `čaʿlab-`).
- References: 187 (link, page) pairs from 185 pages (was 199 / 197). The pages that linked to `θ̣aby-` and `ṣaɣir-` have been repointed (4 → 0, 6 → 0); `maraṣ̂-` still has 10 (was 12). The other 35 non-standard titles are unchanged, including the 4 red links (`našaq-`, `ʾarṣ́-`, `ʾayyal-`, `ʿaḳrab-`).
- Levels (§3): unchanged, the same 20 PS pages without an Akkadian/Eblaite entry; PWS pages are consistent.
- Optional segments in titles (`šaḥ(a)r-`, `šu(n)bulat-`, `ʕankab(īṯ)-`): unchanged.
- Conventions (§5): unchanged (`he` 292 vs `hbo` 46, `arc-imp` 33, `arc-old` 10, `arc-pal` 10, `arc-bib` 14, `xhd` 12).

## 1. Titles (426: 383 Proto-Semitic, 43 Proto-West Semitic; 319 real pages, 107 redirects)
| | count |
|---|---|
| standard spelling | 356 |
| non-standard spelling, **already a redirect to a standard page** | 65 |
| non-standard, redirect, letter not auto-readable (`x̣arb-` → `ḥarb-`, `čaʿlab-` → `ṯaʕlab-`) | 2 |
| non-standard, **a real page: move needed** | **3** |

The three pages to move (`orthography_survey.tsv`, action `MOVE`):
1. `Reconstruction:Proto-Semitic/maraṣ̂-` → `maraṣ́-` (`maraṣ́-` is currently a redirect to it, so move over the redirect; 12 incoming links)
2. `Reconstruction:Proto-Semitic/θ̣aby-` → `ṯ̣aby-` (4 incoming links; the page we posted)
3. `Reconstruction:Proto-Semitic/ṣaɣir-` → `ṣaḡir-` (6 incoming links)

So the mass cleanup of titles has largely been done. Beware: the two pages we posted (1, 2) were wrong spellings.

## 2. References that still use a non-standard spelling
`orthography_links.tsv`: 199 (link, page) pairs from 197 distinct pages to 38 non-standard titles. 34 of those titles exist (31 redirects whose links work but go through the redirect, plus the 3 real pages of §1); **4 are red links** (no page at that spelling):
`našaq-` (1 page: ܢܫܩ), `ʾarṣ́-` (4: ardi, ارض, अर्ज़, Erd), `ʾayyal-` (1: ܐܝܠܬܐ), `ʿaḳrab-` (1: عقرب).
The heaviest redirects: `ʾil-` 22 pages, `baʿl-` 18, `ʿaśr-` 8, `ʾab-` 7, `šabʿ-` 7, `tišʿ-` 10 (`orthography_survey.tsv`, column n_links).
Some redirects lead to a *different stem* (not just a respelling): `ʾab-` → `ʔabw-`, `ʾid-` → `yad-`, `maʾ-` → `māy-`, `ʿaśr-` → `ʕaśar-`: the links there want repointing to the new stem, not only a respelling.

## 3. Level (PS vs PWS): "Proto-Semitic entries should always provide inherited reflexes in East and West Semitic"
- 278 real PS pages; **20 have no Akkadian/Eblaite descendant** (candidates for a move to PWS, or for an added Eastern reflex):
  suffix/root pages `-ay- -b -r d-b-r ʔ-b-d ʔ-b-r ʔ-d-w` (probably exempt), and `may-` (alt. form), `piry-`, `paʕala`, `ʔarnab-`, `ʔadān-`, `ʔiṣbaʕ-`, `ʔbd-`, `ʔdw-`, `ʔdm`, `ḥamaṣ́-`, `ḏV-`, `ḳudš-`, `ḥiṣ́n-`.
- **SEDonline has an Eastern reflex for several of these, so they could stay PS after adding it:** `ʔarnab-` (Akk. *arnabu*), `ʔdm` (Akk. *adamu*), `ḥamaṣ́-` (Akk. *emēṣu*; Ebla *ʔà-me-ṣu*), `ḳudš-` (Akk. *ḳuddušu*; Ebla *ga-ti-šum*), `ʔiṣbaʕ-` (Akk. *iṣbatu*; Ebla *IŠ-ba-um*; SED itself files it as PWS), `ḥiṣ́n-` (Akk. *ḫiṣnu*; SED files it as PWS). No Eastern reflex in SED for `piry- paʕala ʔadān- ʔbd- ʔdw- ḏV-` (so by the rule these are PWS).
- 41 PWS pages: none has a non-borrowed Akkadian/Eblaite entry (4 list only borrowed Akkadian: `gamal- našr- malʔak- baśar-`). Consistent.
- **Our own `gild-`** (posted at PS): the Akkadian *gildu* is, per von Soden in the SED, from Aramaic, so there is no inherited Eastern reflex: by this rule it belongs at **Proto-West Semitic** (SEDonline also files it as PWS). `baḳar-` (wanted at PWS, 2 links) is the same case.

## 4. Entry shape (root + hyphen)
Titles without a trailing hyphen (excluding particles/pronouns): root pages `ʔbd ʔdm ʔtm ʔḏn ʔḫḏ npy rpʔ ṣ́amr` (PS), `rpy rpʔ ʔdm ʔdr ʔdw ʔḏn ṣ́amr` (PWS), hyphenated roots `d-b-r ʔ-b-d ʔ-b-r ʔ-d-w ḳ-r-ʔ` (PS), `ʔ-d-r` (PWS), and `paʕala`, `ʔaḫaḏ`. Also `šaḥ(a)r-`, `šu(n)bulat-`, `ʕankab(īṯ)-` (optional segments in the title), and `V` titles (`bV- gVrān- lV- mVdr- ʔVšk- ʕVnz- ʕVṣṣūr- ḏV-`). Whether any of these should move is an editorial call.

## 5. Conventions in the existing pages that our drafts do not follow (319 pages)
Descendant language codes by frequency: `arc` 283, `he` 269 (`hbo` only 45), `ar` 225, `akk` 273, `uga` 241, `syc` 225, `gez` 183, `am`/`ti` 121, `tig` 95, `phn` 91, `tmr` 77, `xsa` 74, `jpa` 47, `xeb` 45, `arc-imp` 33 (Official/Imperial Aramaic), `myz` 31, `arc-bib` 14, `arc-old` 10, `arc-pal` 10 (Palmyrene), `xhd` 12 (Hadramitic), `sem-srb` 57, `obm` 12 (Moabite), `sam` 8.
Our generator writes Hebrew as `hbo` (WT:ASEM's tree and 85% of existing lines use `he`), and Official/Old/Palmyrene/Biblical Aramaic and Hadramitic as `arc`/`sem-srb` with a typed label, where the pages use `arc-imp`, `arc-old`, `arc-pal`, `arc-bib`, `xhd`.

## Respelling the references: `scripts/wikt_fix_refs.py`
Plan, review, apply with a person saying yes to each diff. Run from a machine that can reach en.wiktionary.org:
1. `python scripts/wikt_fix_refs.py plan` fetches the pages that link to a non-standard spelling and writes the new wikitext to `build/orth_fixes/plan.json` and a summary to `data/wiktionary/orthography_fixes.tsv` (nothing is edited). Snapshot 2026-10-16: **151 pages, 182 respellings** (165 template terms such as `{{inh|ar|sem-pro|*ʾab-}}`, 17 `{{ety|…|sem-pro:*X}}` terms); 10 pages are reached only through another page's etymology chain and follow when that page is respelled; 16 redirects lead to another stem and are left for a person (`ʾab-` → `ʔabw-`, `ʾid-` → `yad-`, `ʿaśr-` → `ʕaśar-`, …).
2. `python scripts/wikt_fix_refs.py show [PAGE …]` prints the diffs.
3. `python scripts/wikt_fix_refs.py apply --user YourName@botname` logs in with a **bot password** (Special:BotPasswords, grant "Edit existing pages"; put it in the env var `WIKT_PASSWORD` or type it at the prompt), shows each diff and asks `[y]es / [n]o / [a]ll the rest / [q]uit`. `--bot` marks edits as bot edits (only with a bot flag). Every edit is based on the revision that was shown; if the page changed since the plan, the diff is recomputed from the live text. Applied pages are logged in `build/orth_fixes/applied.tsv`, so a rerun resumes. The edit summary names the respellings and says "semi-automated".
It changes only the term of a reconstruction reference (the argument after `sem-pro` / `sem-wes-pro`, the `sem-pro:*X` of an `{{ety}}` chain, the title of a `[[Reconstruction:Proto-Semitic/X]]` link); never `tr=` / `t=`, `entry=` (a quoted source), other languages, or a PS spelling in a Proto-West Semitic reference. `python tests/test_fix_refs.py` tests all of this offline, including the editing loop against a fake API.

### The manual route (no bot): `site/orthography_fix.html` + `site/wikt_respell.user.js`
`python scripts/wikt_fix_refs.py checklist` (after `plan`) writes both. Open the checklist page, install the script once into `Special:MyPage/common.js` (the page has a copy button), then press **Open next page** (or `N`) repeatedly: each page opens in your edit form with the respelling already in the box, an edit summary filled in and "Show changes" pressed; you read the diff and press Save. The script acts only on edit links ending in `&respell=1`, works on the live text of the page (so it cannot overwrite someone else's later edit), and shares its code with the tested Python (`scripts/respell_core.js`; `tests/test_respell_js.py` compares the two on 20 real pages and on edge cases, and runs the script against a stub of MediaWiki's edit page). Progress is kept in the browser (localStorage).
