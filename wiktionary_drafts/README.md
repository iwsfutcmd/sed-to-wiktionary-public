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
| `θ̣aby-` | II no. 242 | 624 | 14 |
| `mrṣ́` | I no. 42 (verbal) | 894 | 13 |
| `ṣ́rṭ` | I no. 71 (verbal) | 1023 | 8 |
| `baḳḳ-` | II no. 58 | 667 | 7 |
| `nyk` | I no. 53 (verbal) | 995 | 5 |
| `ḫrš` | I no. 31 (verbal) | 960 | 14 |
| `šiʔr-` | I no. 238 | 691 | 4 |
| `śaḥm-` | I no. 263 | 698 | 4 |

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

## Is a draft good to go?
`make test` (offline) and `ONLINE=1 make test` (also checks the live wiki; not yet run) run `tests/test_drafts.py` over every draft: well-formed wikitext, SED reference,
print/site agreement, every SEDonline word present, script matches language, English glosses, tr= conventions, generator reproducibility;
online: title free and not linked under another spelling, language codes (no parse check: pages are pasted in by hand). Mutation-checked: 19 of 19 seeded mistakes are caught.

## Titles
Checked against incoming links (`list=backlinks`), because Wiktionary's Proto-Semitic titles mix `ḳ`/`q` and `ṯ̣`/`θ̣`:
`baḳḳ-` is already linked from the Arabic entry بق ("from Proto-Semitic *baḳḳ-"), `θ̣aby-` from ظبي (`{{ety|ar|:inh|sem-pro:*θ̣aby-}}`).
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
     `ethiopic.refresh()`). Amharic, Tigrinya, Tigre and the Gurage group. Gemination (doubled letter in the source) is not written.
     Not for Ge'ez (its source writes `a` for the first order, so it depends on the word) or word-initial vowels (unwritten ʾ).
   - `abjad`: consonantal Hebrew/Aramaic, Samaritan, Syriac, Ugaritic, Phoenician, Old South Arabian. Unpointed; final ā is written
     as alef; Ugaritic ʾ is always 𐎀 (Wiktionary's 𐎛 for *ʾimr-* is in `CURATED`).
3. **`CURATED`** (`wikt_draft.py`): what no converter can derive: Arabic, pointed Hebrew, Ugaritic ʾi.
4. **Latin as the term** (Wiktionary accepts it, and these are cited in Latin): Mehri, Shehri/Jibbali, Harsusi, Bathari, Soqotri,
   Eblaite, Turoyo, Western Neo-Aramaic.
5. Still "[script needed]": Mandaic and Ge'ez (no converter), and forms with variants. `θ̣aby-` has one (Mandaic).

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
