# Wiktionary drafts

Draft `Reconstruction:Proto-Semitic/…` pages for printed-SED entries that Wiktionary lacks (best-attested first, from
`data/sed_wiktionary_gaps.tsv`). One file per page: the file name is the page title without the namespace.
Forms and glosses come from the SEDonline reconstruction that cites the printed entry (`data/sedonline/`); the reference is
`{{R:sem-pro:SED|volume=…|id=<SEDonline id>|entry=…}}` as on `npy` and `ʔdm`. Each draft passed `action=parse` on
en.wiktionary.org (no template errors, no missing templates) on 2026-10-15; none has been saved to the wiki.

| page | SED | SEDonline id |
|---|---|---|
| `warik-` | I no. 288 | 758 |
| `ḥupn-` | I no. 125 | 836 |
| `šit-` | I no. 255 | 734 |
| `wšn` | I no. 82 (verbal) | 1001 |
| `śyb` | I no. 66 (verbal) | 1207 |

Check before saving:
- Native-script spellings are written from the SEDonline transliterations. `-` with `tr=` renders "[script needed]": fill these in
  (Mehri, Harsusi, Tigre, Ge'ez `śeba`) or drop the line. Ethiopic/Syriac/Hebrew spellings of Amharic `əffəñ`, Ge'ez `ḥəfn`,
  Hebrew `śāḇ` are from memory: verify against the lexica.
- `ŝ` in SED is `ś` on Wiktionary; `ṯ̣` is written with a combining dot below.
- `wšn` and `śyb` carry no `{{sem-pro-conj}}`: the SED gives roots only, so the stem vowels are not known.
- `šit-` uses `{{sem-noun|?}}` (gender unknown); `warik-` follows the `ʕaṯ̣m-` convention (`m`, `g2=f`) for SED's `(-at)`.
- Semantically loose cognates are marked `unc=1` or left out; check the Akkadian and Ugaritic items on `warik-`.
