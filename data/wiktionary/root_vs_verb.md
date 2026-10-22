# Bare `*ʔbd` vs hyphenated `*ʔ-b-d`: two different things (audit, 2026-10-22)

Written so a later chat (e.g. on a phone) can pick this up cold.

## Conclusion
- **WT:ASEM has no rule for writing a root with hyphens between the radicals.** Hyphenating roots was our own proposal (`root_notation.md`, 2026-10-19), so it is NOT an "ASEM respelling". Corrected by the user on 2026-10-21.
- **Bare and hyphenated forms are semantically distinct entries on the live wiki**, so rewriting one as the other changes which entity a reference points to:
  - `Reconstruction:Proto-Semitic/ʔbd` = the **verb** (`{{head|sem-pro|verb}}`, `{{sem-pro-conj/*paʕala-*yipʕal|ʔ|b|d}}`, gloss "to perish, destroy", verb descendants). Same for `ʔdm` (verb "to be red", derived term noun `*ʔadam-`) and PWS `ʔdr`.
  - `Reconstruction:Proto-Semitic/ʔ-b-d` = the **root** (`{{head|sem-pro|root}}`, no real gloss, only `{{non-gloss|Forming words pertaining to destruction}}`; Derived terms list `*ʔbd` and `*ʔbd-`; descendants are root-box templates `{{ar-root}}`, `{{syc-root}}`, `א־ב־ד`). Its SED citation is `*ˀ-b-d` (id 1992), a separate SED entry from the verb. Same for `ʔ-d-w` (root; derived terms point to verb `*ʔdw` and stem `*ʔdw-`).
  - So: bare = an attested verb; hyphenated = the abstract radical set behind it.
- Not yet known: whether every bare/hyphenated pair on the wiki follows this; I only read `ʔbd`, `ʔ-b-d`, `ʔdm`, `ʔ-d-w`, PWS `ʔdr`.

## What was changed in the repo (commit 402c55d)
`wikt_fix_refs.py` and `respell_core.js` no longer turn a bare consonant-only term into a hyphenated root, and no longer plan root-page moves (`ʔbd` -> `ʔ-b-d`) or extend the corpus for roots. Letters are still respelled (ʾ->ʔ, q->ḳ ...). A term already hyphenated keeps its hyphens. `rootify()` / `root_moves()` remain in the code, unused. Tests updated (`test_bare_roots_are_not_hyphenated`).

## Audit of the live wiki (read-only, 2026-10-22)
Method: Wiktionary search for pages with a hyphenated 3-radical `sem-pro`/`sem-wes-pro` term (38 pages), then each page's last 30 revisions for "WT:ASEM" respell summaries (27 edits, listed in `root_hyphenation_audit.tsv`), then diffed each against its parent revision.
Result: the respell sweep (user Iwsfutcmd, 2026-10-19) turned exactly **three bare roots into hyphenated ones**:

| Page | Change |
|---|---|
| ע־מ־ד | `*ʕmd` -> `*ʕ-m-d` |
| ܕܕܒܐ | `*ḏbb` -> `*ḏ-b-b` |
| ܕܚܠܬ | `*ḏḥl` -> `*ḏ-ḥ-l` |

None of `ʕmd`, `ʕ-m-d`, `ḏbb`, `ḏ-b-b`, `ḏḥl`, `ḏ-ḥ-l` exists as a PS or PWS page, so nothing was repointed between two existing pages. The other 24 edits only changed letters (hyphens were already there, e.g. `q-n-y` -> `ḳ-n-y`).
Caveat: relies on the search index, so a missed page is missed here. Not exhaustive.

## Open
1. Decide for each of the three pages whether the reference meant the verb (bare) or the root (hyphenated); probably revert to bare unless the context is about the root. Edits are done by hand (no bot); I can prepare the exact text.
2. Consider re-checking the other `.tsv` survey outputs (`orthography_survey.*`, `orthography_fixes.tsv`) that still describe bare roots as "to be moved".
3. Possible guideline line for WT:ASEM: how to title a root entry vs a verb entry.
