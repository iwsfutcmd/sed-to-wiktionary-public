# Proto-Semitic / Proto-West Semitic pages vs. WT:ASEM (snapshot 2026-10-15)

Reproduce: `python scripts/wikt_orthography.py --scan --fresh` (scans titles, incoming links and page text through the API; output in this folder).
Standard notation (Wiktionary:Proto-Semitic entry guidelines): `p t ṭ k ḳ ʔ b d g ṯ s š ś ḫ ḥ h ṯ̣ ṣ ṣ́ ḏ z ḡ ʕ r w y l m n`, vowels `a i u ā ī ū`, `V`/`V̄`; entry name = root/stem + hyphen; East + West attestation = Proto-Semitic, West only = Proto-West Semitic.
Variants found: `q ʾ ˀ ʿ ˁ θ θ̣ ṱ ð ṣ̂ ɣ ḍ x̣ č`.

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
