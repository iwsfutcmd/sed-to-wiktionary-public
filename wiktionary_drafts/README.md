# Wiktionary drafts

Draft `Reconstruction:Proto-Semitic/…` pages for printed-SED entries that Wiktionary lacks. One file per page: the file name is
the page title without the namespace. **None has been saved to the wiki.**

## Selection rule
Only entries where the printed SED and SEDonline agree (`data/sedonline/sed_print_vs_site_agreement.tsv`, `agree = 1`):
same form, same gloss, the same set of core languages cited (Akk, Ebl, Ugr, Hbr, Pho, Arb, Sab, Gez, Tgr, Tna, Amh, Har, Mhr,
Jib, Hrs, Soq, Syr, Mnd, Jewish Aramaic), and filed as PS on the site. 107 of the 523 gaps pass; the first five without schematic
`V` or `/` variants were taken, best-attested first. Four earlier drafts (`ḥupn-`, `šit-`, `wšn`, `śyb`) were dropped: the site
differs from the print in form, gloss or cited languages. Titles were checked live on en.wiktionary.org (none exists).
Forms and glosses come from the SEDonline reconstruction that cites the printed entry; the reference is
`{{R:sem-pro:SED|volume=…|id=<SEDonline id>|entry=…}}`. Each draft passed `action=parse` (no Lua errors, no missing templates).

| page | SED | SEDonline id |
|---|---|---|
| `warik-` | I no. 288 | 758 |
| `ṯ̣aby-` | II no. 242 | 624 |
| `mrṣ́` | I no. 42 (verbal) | 894 |
| `ʔimmar-` | II no. 5 | 363 |
| `baqq-` | II no. 58 | 667 |

## Check before saving
- Native-script spellings are written from the SEDonline transliterations. `-` with `tr=` renders "[script needed]" (Arabic `ʔimmar-`,
  Mehri, Harsusi): fill in or drop. Hebrew, Syriac, Ugaritic, Phoenician and South Arabian spellings are from memory: verify.
- The language comparison is coarse (core languages only; print reflexes are OCR text). "Agree" does not mean every cited form
  is identical: compare the descendants with the printed page before saving.
- `ŝ`/`ṣ̂`/`ḳ` in SED are `ś`/`ṣ́`/`q` on Wiktionary; `ṯ̣` is written with a dot below.
- Roots (`mrṣ́`) carry no `{{sem-pro-conj}}`: the SED gives no stem vowels.
- `warik-`: Akkadian *warkatum* "rear side" is marked `unc=1` (meaning: it may belong to the root "to be behind"); Ugaritic *yrk*
  "hips (?)" is queried in the source.
