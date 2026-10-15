# Wiktionary drafts

Draft `Reconstruction:Proto-Semitic/…` pages for printed-SED entries that Wiktionary lacks. One file per page: the file name is
the page title without the namespace. **None has been saved to the wiki.** Regenerate with `python3 scripts/wikt_draft.py`
(network; caches Wiktionary pages in `build/wikt_pages/`).

## Selection rule
Only entries where the printed SED and SEDonline agree (`data/sedonline/sed_print_vs_site_agreement.tsv`, `agree = 1`):
same form, same gloss, the same set of core languages cited (Akk, Ebl, Ugr, Hbr, Pho, Arb, Sab, Gez, Tgr, Tna, Amh, Har, Mhr,
Jib, Hrs, Soq, Syr, Mnd, Jewish Aramaic), and filed as PS on the site. 107 of the 523 gaps pass; the first five without schematic
`V` or `/` variants were taken, best-attested first. Titles were checked live on en.wiktionary.org (none exists).
Dropped: `ḥupn-`, `šit-`, `wšn`, `śyb` (site differs from the print), `ʔimmar-` (Wiktionary's Akkadian `immerum` lists the West
Semitic "lamb" words as borrowings from Akkadian, which conflicts with an inherited PS entry).

| page | SED | SEDonline id | cited words |
|---|---|---|---|
| `warik-` | I no. 288 | 758 | 27 |
| `ṯ̣aby-` | II no. 242 | 624 | 14 |
| `mrṣ́` | I no. 42 (verbal) | 894 | 13 |
| `ṣ́rṭ` | I no. 71 (verbal) | 1023 | 8 |
| `baqq-` | II no. 58 | 667 | 7 |

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
5. Still "[script needed]": Mandaic and Ge'ez (no converter), and forms with variants. `ṯ̣aby-` has one (Mandaic).

`python3 scripts/wikt_draft.py --verify` lists every script form with how it was made and whether Wiktionary has an entry for it:
27 of 40 do not (red links; mostly Aramaic dialects, Sabaic, Gurage and Tigre, which Wiktionary covers thinly). Generated Ethiopic
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
