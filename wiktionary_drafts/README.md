# Wiktionary drafts

Draft `Reconstruction:Proto-Semitic/…` pages for printed-SED entries that Wiktionary lacks. One file per page: the file name is
the page title without the namespace. **None has been saved to the wiki.** Regenerate with `python3 scripts/wikt_draft.py`
(network; caches Wiktionary pages in `build/wikt_pages/`).

## Selection rule
Only entries where the printed SED and SEDonline agree (`data/sedonline/sed_print_vs_site_agreement.tsv`, `agree = 1`):
same form, same gloss, the same set of core languages cited (Akk, Ebl, Ugr, Hbr, Pho, Arb, Sab, Gez, Tgr, Tna, Amh, Har, Mhr,
Jib, Hrs, Soq, Syr, Mnd, Jewish Aramaic), and filed as PS on the site. 107 of the 523 gaps pass. Entries with schematic
`V`, `/` variants or mixed meanings were left for later (e.g. `*ṯarb-` is "fat" in some languages and "calf of leg" in others;
`*laḳlaḳ-`: the site itself allows an Akkadian-to-Arabic borrowing), best-attested first. Titles were checked live on en.wiktionary.org (none exists).
Dropped: `ḥupn-`, `šit-`, `wšn`, `śyb` (site differs from the print), `ʔimmar-` (Wiktionary's Akkadian `immerum` lists the West
Semitic "lamb" words as borrowings from Akkadian, which conflicts with an inherited PS entry).

| page | SED | SEDonline id | cited words |
|---|---|---|---|
| `warik-` | I no. 288 | 758 | 27 |
| `ṯ̣aby-` | II no. 242 | 624 | 14 |
| `maraṣ́-` | I no. 42 (verbal) | 894 | 13 |
| `ṣ́araṭ-` | I no. 71 (verbal) | 1023 | 8 |
| `baḳḳ-` | II no. 58 | 667 | 7 |
| `gild-` | I no. 78 | 704 | 17 (from the print) |
| `pan-` | I no. 215 | 347 | 7 (from the print) |
| `kišād-` | I no. 147 | 707 | 8 (from the print) |
| `pagr-` | I no. 209 | 688 | 9 (from the print) |
| `ʕakbar-` | II no. 30 | 504 | 6 (from the print) |
| `nayak-` | I no. 53 (verbal) | 995 | 5 |
| `ḫaraš-` | I no. 31 (verbal) | 960 | 14 |
| `šiʔr-` | I no. 238 | 691 | 4 |
| `śaḥm-` | I no. 263 | 698 | 4 |

## Wanted pages (red links on Wiktionary)
Special:WantedPages is capped at 5,000 results (down to 55 incoming links) and contains no Semitic reconstruction, so `make wanted`
(`scripts/wikt_wanted.py`) goes the other way: for each SED entry without a matching page it generates the plausible titles (Wiktionary's mixed
spellings; for verbs the root and the vocalised stems CaCaC-/CaCiC-/CaCuC-) and asks, in batches, which of them are missing but linked
(`prop=linkshere`). Output: `data/wiktionary/wanted_semitic.tsv` (title, number of linking pages, some of them, SED entry, `agree` flag).
Writing a page at a title Wiktionary already links to also settles the spelling questions (ḳ/q, ṯ̣/θ̣, ṣ́/ṣ̂).

## Pages written from the printed entry
`gild-` (SED I no. 78 *gi/ald-) is built from the printed cognate set, because SEDonline differs from the print: it files the entry as
Proto-West Semitic (treating Akkadian and Hebrew as Aramaisms), lacks Official Aramaic, Palmyrene, Neo-Aramaic and Soqotri, and adds Turoyo
and Bathari, which the print does not have. Wiktionary's own Hebrew, Aramaic, Syriac and Arabic pages already say they inherit `*gild-` (13 pages
link it), which agrees with the print's Proto-Semitic reading. The comparison is in `form_check.tsv`; left out and why is in `wikt_draft.py`.
Tests: the SED reference must resolve and every printed word must be on the page, but the page does not have to match the site.

## Verbs: vocalised stems
Verbs are titled by their perfect stem, as on `pataḥ-`, `našaḳ-`, `patal-` (`maraṣ́-`, `nayak-`, `ḫaraš-`, `ṣ́araṭ-`), with the SED root
(`*mrṣ̂`, `*nyk`, ...) in the reference. The SED gives only roots, so the vowels come from evidence, not from the source:
- `maraṣ́-`: the printed Akkadian *marāṣu* is marked `(a/a)` -> `{{sem-pro-conj/*paʕala-*yipʕal}}`; three Wiktionary pages already link `*maraṣ̂-`.
- `nayak-`: medial y (hollow) -> `*payala-*yipīl`; two Wiktionary pages already link `*nayak-`.
- `ḫaraš-`: Ge'ez *ḫarasa*, Akkadian *ḫarāšu*; no class marker in the print, so no conjugation table.
- `ṣ́araṭ-`: Akkadian `(u/u)`, Arabic `(u)` = u-class, but Wiktionary has no plain u-class template, so no table.
  Where the print differs from SEDonline the draft follows the print (`override` in `wikt_draft.py`, documented in `form_check.tsv`, tested): Harsusi `ẑerōṭ`, Soqotri `ẑerót`, Syriac gloss "flatulence". The print's Amharic forms (noted there as possible Arabisms) are not included.
`vn=` is the CaCC verbal noun, as on the existing pages. Titles and conjugation blocks write the lateral emphatic as `ṣ́` (WT:ASEM); `ṣ̂` is SED's notation and stays only in the quoted `entry=`. A test checks each conjugation block against its title.

## Pages already on Wiktionary (`done/`)
Move a page to `done/` once you have saved it. `python3 scripts/wikt_draft.py` and `make done-check` rebuild every `done/` page
and compare it with your saved copy. The saved copy is never overwritten: a changed page is written to `updates/` with a diff printed
(delete the file in `updates/` after applying it, or it disappears by itself once the saved copy matches). `make test` prints a
`FLAG` line for the same changes and for convention problems in saved pages (not a failure). All the content checks below also run
on `done/`.

## Conflicts with existing Wiktionary pages
`make conflicts` (`scripts/wikt_conflicts.py`) reads the Wiktionary page behind every descendant and reports, in that language's section:
CONFLICT (etymology names a different Proto-Semitic form; the page lists other descendants of ours as *borrowed* from it, as Akkadian
`immerum` does for the Hebrew/Aramaic "lamb" words), WARN (the word is said to be borrowed; our gloss shares no word with the page's
definitions; the page names our consonants with other vowels, so the page may be expected at that title), INFO (agrees, or no page).
`make test` runs it on the cached pages and fails on any CONFLICT. A word can be left out of a draft with a documented reason
(`exclude` in `wikt_draft.py`; currently Amharic *arräsä* under `ḫrš`: Wiktionary's አረሰ is "to plough", from *ḥaraṯ-).

## Updates to pages that are not ours (`merges/`)
`make enrich` (`scripts/wikt_enrich.py`) compares every existing reconstruction page that a SED entry covers with SEDonline's languages for
the same entry and ranks them by how many the page lacks (`data/wiktionary/enrich_candidates.tsv`; the worklist's section 2b). The counts
are an upper bound: SEDonline has some words the print does not. A page is then filled out from the *printed* entry by adding lines to the
live text, never removing or rewording anything, and saved as `merges/<title>.wiki` (first: `ʕaṯ̣m-` "bone", SED I 25).
Before a card is made, `make merge-check` (`scripts/wikt_merge.py`) confirms that no language we add is already on the page, whether on a
line of its own or through a `{{desctree}}`, which shows another page's whole descendant list (on `ʕayn-`, `{{desctree|tmr|עַיְנָא}}` already
shows Syriac, Mandaic, Turoyo and Assyrian). `tests/test_merge.py` replays that case offline.
`tests/test_sed_refs.py` checks every page in `done/` and `merges/`: each `{{R:sem-pro:SED}}` has `id=` (links to SEDonline), and the page is
at the level SEDonline gives that record, unless `LEVEL_EXCEPTIONS` records why not (pages that follow the print, or a decision).
`scripts/wikt_sed_ids.py` finds SED references elsewhere on Wiktionary without `id=` and works out the record, checked against the page.

## Back-links from the daughter pages
`make backlink` re-downloads every daughter page that does not cite its reconstruction yet and writes whole-page edits
(`data/wiktionary/backlink_pages.json`), then the checklist page (`scripts/build_backlink_checklist.py`). What a person decided is kept in
`scripts/wikt_backlink.py`: `DECISIONS` (leave a page alone, write into a chosen Etymology section, or apply a given rewording), `EXTRA`
(pages the scan cannot find: a lemma we link only through one of its forms, a page whose Etymology 1 is another word) and `NOTES`
(an order to keep, e.g. فرس only after our page names its etymon with `id=horse`). Two languages of one page become one card.

## Language codes
Aramaic varieties use Wiktionary's etymology-only codes, which name themselves and need no label: `arc-old` (Old), `arc-imp` (Official =
Imperial), `arc-pal` (Palmyrene), `arc-nab` (Nabataean), `arc-bib` (Biblical). Their period scripts (Phoenician, Imperial Aramaic,
Palmyrene, Nabataean) are detected and, except Nabataean, transliterated by Wiktionary, so `sc=`/`tr=` are left out. Hadramitic is `xhd`
(Hadrami), Qatabanian `xqt`. Old South Arabian `s₁ s₂ s₃` is written `s¹ s² s³` in `tr=`, as Wiktionary does. There is no `oar`.

## Is a draft good to go?
`make test` (offline) and `ONLINE=1 make test` (also checks the live wiki; not yet run) run `tests/test_drafts.py` over every draft: well-formed wikitext, SED reference,
print/site agreement, every SEDonline word present, script matches language, English glosses, tr= conventions, generator reproducibility;
online: title free and not linked under another spelling, language codes (no parse check: pages are pasted in by hand). Mutation-checked: 19 of 19 seeded mistakes are caught.

## Form-level check against the printed page
The agreement test only compares which languages are cited. `data/sedonline/form_check.tsv` records a by-eye comparison of every cited
form with the printed entry (200-dpi crops from `scripts/entry_crop.py VOL KEY`, e.g. `entry_crop.py 1 N238`). Done so far:
`šiʔr-` (all forms agree; the print has a few extras) and `ṣ́araṭ-` (the print differs from the site for Soqotri and Harsusi and glosses Syriac
*ʕurṭē* "crepitus ventris"; the draft now follows the print). The other drafts have not been compared by eye.

## Titles
Checked against incoming links (`list=backlinks`), because Wiktionary's Proto-Semitic titles mix `ḳ`/`q` and `ṯ̣`/`θ̣`:
`baḳḳ-` is already linked from the Arabic entry بق ("from Proto-Semitic *baḳḳ-"), `ṯ̣aby-` from ظبي (`{{ety|ar|:inh|sem-pro:*θ̣aby-}}`).
Where nothing links in, the SED's own spelling is used with Wiktionary's `ś ṣ́ ʔ`. In descendants, `tr=` follows Wiktionary (`q`).
Pages already saved to Wiktionary are moved to `done/` (`warik-`, 2026-10-15); `wikt_draft.py` does not regenerate them.

## Contents
Every word SEDonline lists under the reconstruction is included (nothing is selected), grouped by branch as on `kalb-`/`pataḥ-`.
Each page passed `action=parse` on en.wiktionary.org (no Lua errors, no missing templates). Language codes were checked by
rendering them (e.g. `agj` = Argobba, `bhm` = Bathari, `tmr` = Jewish Babylonian Aramaic, `jpa` = Jewish Palestinian Aramaic).
The reference is `{{R:sem-pro:SED|volume=…|id=<SEDonline id>|entry=…}}`.

## Where the script forms come from
1. **Akkadian cuneiform** is copied from the `{{cunsp}}` block (`phon=`) of the Wiktionary lemma page. Missing lemma pages
   (`ṣabītum`, `ṣarātum`, `baqqum`) get no cuneiform.
2. **Converters** in `scripts/tr2script/` (tests: `make test`, no network). They return nothing instead of guessing.
   - `ethiopic`: the exact inverse of Wiktionary's `Module:Ethi-translit` (snapshot in `data/scripts/ethi_translit.json`, refresh with
     `ethiopic.refresh()`). Amharic, Tigrinya, Tigre, the Gurage group and Ge'ez (Leslau's a = ä, ā = a; 118 of 645 SEDonline Ge'ez words exist on Wiktionary at the spelling produced, one under another letter). Gemination (doubled letter in the source) is not written.
     Not for word-initial vowels (unwritten ʾ). Harari long vowels are written as the short ones (Wiktionary ሙዝ = mūz).
   - Forms with variants (`šuš(š)`, `nāˀ/nā`), for every converter: each reading is converted, and the script is used only when all of them
     give the same spelling (`tr2script.same_spelling`); `(a)dāmäsä` or `mwt/myt` are still refused.
   - `mandaic`: one letter to one letter, since Wiktionary's `Module:Mand-translit` reads the script letter by letter and the SED's Macuch-style forms write the vowel letters a, i, u. Refuses ḥ ġ ˀ (merged in the script), doubled consonants and bare roots; the page's tr is omitted when Wiktionary's own transliteration gives the same. 37 of 368 convertible SEDonline Mandaic words are Wiktionary Classical Mandaic entries at exactly the spelling produced.
   - `abjad`: consonantal Hebrew/Aramaic, Samaritan, Syriac, Ugaritic, Phoenician, Old South Arabian. Unpointed; final ā is written
     as alef; Ugaritic ʾ is always 𐎀 (Wiktionary's 𐎛 for *ʾimr-* is in `CURATED`).
3. `arabic`: vocalised stems (warik- → وَرِك). Refuses bare roots, hamza, and word-final ā/ī. Checked against Wiktionary's own
   transliteration (`ONLINE=1 make test`: the spelling is rendered by `{{desc|ar|…}}` and its automatic transliteration compared).
4. **`CURATED`** (`wikt_draft.py`): what no converter can derive: Arabic verbs given by root only, pointed Hebrew, Ugaritic ʾi, Turoyo.
5. **Latin as the term** (Wiktionary accepts it, and these are cited in Latin): Mehri, Shehri/Jibbali, Harsusi, Bathari, Soqotri,
   Eblaite, Turoyo, Western Neo-Aramaic.
6. Akkadian lemmas with no Wiktionary page (`ṣabītum`, `ṣarātum`, `ḫarāšum`, `šēmum`, `akbarum`) get a NORMALISED plene spelling (`ṣa-bi-i-tu`), built by `cuneiform.normalise` and converted with eBL: the nominative without mimation. It is not an attestation. Against Wiktionary's own spellings of 420 lemmas it agrees 312 times up to mimation and plene writing (tests/test_cuneiform.py). Delete the `alt=` if you prefer none.
6. Still "[script needed]": forms the converters refuse (see the refusal lists in each module), bare roots and forms with variants. Ge'ez is converted, but the SED sometimes writes s for a graphic ś (`kəsād` = ክሣድ): such words need the ś by hand.

`python3 scripts/wikt_draft.py --verify` lists every script form with how it was made and whether Wiktionary has an entry for it:
35 of 56 do not (red links; mostly Aramaic dialects, Sabaic, Gurage and Tigre, which Wiktionary covers thinly). Generated Ethiopic
is the least certain output: compare it with a lexicon before saving.

## Check before saving
- The language comparison behind "agree" is coarse (core languages only; the print reflexes are OCR text). Compare the
  descendants with the printed page.
- Hebrew, Syriac, Ugaritic, Phoenician and South Arabian spellings were written from the SEDonline consonants and are not
  vocalised unless Wikt has the lemma; verify against lexica where a page is missing.
- `ŝ`/`ṣ̂`/`ḳ` in SED are `ś`/`ṣ́`/`q` on Wiktionary; `ṯ̣` is written with a dot below.
- Roots (`mrṣ́`, `ṣ́rṭ`) carry no `{{sem-pro-conj}}`: the SED gives no stem vowels.
- `warik-`: Wiktionary's Akkadian `warkatum` already says "cognate with Arabic وَرِك and Hebrew יָרֵךְ". Akkadian `warki`
  ("after, behind") is a different sense, and Ugaritic *yrk* "hips (?)" is queried in the source.
- `nyk`: the Arabic gloss "to marry a woman" is the source's (Kazimirski), while Arabic ناك is vulgar "to have sex with"; check it.
- `šiʔr-`: Wiktionary's Akkadian `šīrum` already lists Hebrew שְׁאֵר and Ugaritic 𐎌𐎛𐎗 as cognates (the spellings here are copied from it).
- `śaḥm-`: only Akkadian, Arabic and one Jibbali form (glossed "temple", with a note that it is cut to judge the fat of a carcass).
- `ḫrš`: Ge'ez has no converter; Tigre and Argobba Ethiopic are generated. The Arabic forms are two different words (`ḫarūs-`, `ḫrs` II).


Print-sourced pages (`gild-`, `pan-`, `kišād-`, `pagr-`, `ʕakbar-`) list only the words of the printed entry; what the site adds or changes is recorded in
`data/sedonline/form_check.tsv`. Not drafted from the wanted-pages list: `ʔay-` (the two links are the interrogative "where", e.g. Ge'ez ኢ, Phoenician 𐤀𐤉,
not the bird of prey, which Wiktionary has at `*ʔayy-`), `ḏbb` and `mny` (the links use the bare root; no vowel evidence for a stem title), `baḳar-`
(the links go to Proto-West Semitic, not Proto-Semitic) and `bVʕVr-` (print and site disagree).
