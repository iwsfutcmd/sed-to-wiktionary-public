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
2. **Curated spellings** (Arabic, Hebrew, Aramaic, Syriac, Ugaritic, Phoenician, Old South Arabian; `CURATED` in `wikt_draft.py`).
   `python3 scripts/wikt_draft.py --verify` checks each against a live Wiktionary entry and against the consonants of the
   SEDonline transliteration. All consonants match; **18 of 35 have no Wiktionary entry yet** (they will be red links): Old and
   Official Aramaic, all Jewish Palestinian/Babylonian Aramaic, Syriac `mǝraˁ`/`ˁrṭ`, Phoenician `ˀmr`, Ugaritic `yrk`, all Sabaic.
3. **Ethiopic is generated** from the transliteration (regular syllabary, Amharic/Tigrinya/Gurage only; marked in the generator's
   output). Not done for Tigre or Ge'ez, whose source transliteration does not follow the regular `ä`/`a` convention.
4. Everything else renders "[script needed]" (`-` + `tr=`): Tigre, Eblaite, Biblical Aramaic, Modern South Arabian, and forms with
   variants. SEDonline has no script for these.

## Check before saving
- The language comparison behind "agree" is coarse (core languages only; the print reflexes are OCR text). Compare the
  descendants with the printed page.
- Hebrew, Syriac, Ugaritic, Phoenician and South Arabian spellings were written from the SEDonline consonants and are not
  vocalised unless Wikt has the lemma; verify against lexica where a page is missing.
- `ŝ`/`ṣ̂`/`ḳ` in SED are `ś`/`ṣ́`/`q` on Wiktionary; `ṯ̣` is written with a dot below.
- Roots (`mrṣ́`, `ṣ́rṭ`) carry no `{{sem-pro-conj}}`: the SED gives no stem vowels.
- `warik-`: Wiktionary's Akkadian `warkatum` already says "cognate with Arabic وَرِك and Hebrew יָרֵךְ". Akkadian `warki`
  ("after, behind") is a different sense, and Ugaritic *yrk* "hips (?)" is queried in the source.
