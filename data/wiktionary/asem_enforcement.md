# Keeping Proto-Semitic references in the WT:ASEM notation (draft proposal and tested pieces)

Status 2026-10-17. The detector, the filter pattern and their tests are in this repository; nothing has been installed on Wiktionary. Wiktionary's own rules and the people who maintain the modules decide what is adopted.

## What the problem looks like (measured)
- Of 426 Proto-Semitic / Proto-West Semitic titles, 70 were typed in a variant spelling (`ʾ ʿ q θ θ̣ ṱ ð ṣ̂ ŝ ɣ ḍ x̣ č`); all are now redirects or moved (`data/wiktionary/orthography_survey.md`).
- 197 pages referenced a variant spelling in a `{{inh}}`, `{{cog}}`, `{{m}}`, `{{ety}}` or `[[Reconstruction:…]]`; those were respelled by hand with `site/orthography_fix.html`.
- In a sample of the 1,329 pages that link to Proto-Semitic pages (`build/asem_corpus.json`), 25 (1.9 %) still held a variant character after that clean-up, including terms inside nested etymology chains and alternative forms (`*šabʿum`) that a link table does not show. They are the 25 pages on the current checklist.

## What can be done (least to most intrusive)
1. **Tracking category.** The module that handles `sem-pro` / `sem-wes-pro` terms (or the Proto-Semitic templates) adds a maintenance category when the term holds a variant character, for example "Proto-Semitic terms in non-standard notation". Pages still render; the category is the to-do list. Cheapest to adopt, no false alarms on pages.
2. **Edit filter that warns.** One AbuseFilter rule on added text, action "warn" (not "disallow"): the editor sees "WT:ASEM writes ʔ, not ʾ" and can save anyway. The pattern is in `asem_edit_filter_regex.txt` and is tested here.
3. **Hard error from the module.** Not recommended: it breaks pages that quote a source's own transcription, and a missing character is not worth a red error.
4. **Link normalisation.** Map the variants to the standard spelling when the link is made, so `*ʾab-` still reaches `*ʔab-`. Fixes the target, not what the page shows.

## The pattern for option 2 (and what it was tested on)
`asem_edit_filter_regex.txt` (PCRE, for `added_lines`; AbuseFilter's string escaping for backslashes may need one more level). It fires on:
- the term of a reference to `sem-pro` or `sem-wes-pro` in `{{inh}} {{inh+}} {{der}} {{der+}} {{bor}} {{cal}} {{m}} {{m+}} {{l}} {{l+}} {{cog}} {{noncog}} {{desc}} {{desctree}} {{syn}} {{ant}}` (the language of the term is read from the right argument: `{{inh|ar|sem-pro|*ʾab-}}` is a Proto-Semitic term, `{{inh|sem-pro|afa-pro|*ʾab-}}` is not);
- an alternative form written `*X` in the same template;
- `sem-pro:*X` in an `{{ety}}` chain, also nested (`<ety:uder<sem-pro:*X>>`);
- `[[Reconstruction:Proto-Semitic/X]]` and the Proto-West Semitic equivalent.
It does not fire on `tr=`, `t=`, `entry=` (a quoted source), other languages, Proto-Afroasiatic terms, or the standard notation. Known limit: a term built inside another template (`*{{foo|ʾab-}}`) cannot be seen by a regular expression.

Tests (`python3 tests/test_asem_check.py`): 23 bad and 22 good examples; the pattern run through Perl (PCRE) agrees with the Python form; on the 1,329-page sample the pattern and the parser-based detector agree on every page (25 flagged, 1,304 clean, no false positives or misses).

## Suggested warning text
"This reference spells a Proto-Semitic term with a character that Wiktionary:Proto-Semitic entry guidelines (WT:ASEM) does not use: ʔ (not ʾ ˀ), ʕ (not ʿ ˁ), ḳ (not q), ṯ (not θ), ṯ̣ (not θ̣ ṱ), ḏ (not ð δ), ṣ́ (not ṣ̂ ḍ), ś (not ŝ), ḡ (not ɣ ġ). You can still save."

## A sketch for option 1 (untested; no Lua engine here)
In the module that renders `sem-pro` terms: if `mw.ustring.find(term, "[ʾʿˀˁʼʻθðδɣγġ]")` or the term contains `q`, or `ṣ̂`, `ŝ`, `θ̣`, `ṱ`, add the category. Treat it as a starting point for whoever maintains that module.

## Things to settle with the community first
- Which characters count as variants. `ḍ`, `x̣` and `č` have no automatic reading; `sₓ` and `ḏ̣` (used on a few pages) are deliberately not flagged.
- Whether Proto-Semitic as the inheriting language (`{{inh|sem-pro|afa-pro|*…}}`) should be held to the notation of the other term.
- Whether a warning is enough or a tracking category is preferred.
