# Default target rebuilds all tables and the site from the committed intermediates (no PDFs, no network).
PY ?= python3
all: tables site
tables:           # raw transcriptions + glottal calls -> sed_all.tsv -> Wiktionary match -> per-volume TSVs
	$(PY) scripts/build_sed.py
	$(PY) scripts/wikt_match.py
site: tables
	$(PY) scripts/build_site.py
titles:           # refresh the Wiktionary title snapshot (network); re-run `make` afterwards
	$(PY) scripts/fetch_titles.py

# --- Only needed to regenerate the intermediates from the PDFs (put them in pdf/vol1.pdf, pdf/vol2.pdf) ---
bbox-%:
	mkdir -p build/v$*
	pdftotext -bbox-layout -f $(FIRST$*) -l $(LAST$*) pdf/vol$*.pdf build/v$*/bbl.html
FIRST1=155
LAST1=488
FIRST2=94
LAST2=440
heads-%: bbox-%
	$(PY) scripts/locate.py $*
crops-%: heads-%
	$(PY) scripts/crops.py $*
glot-%: heads-%
	$(PY) scripts/glot.py $* $(or $(OUT),data/intermediate/glot_v$*.json)
.PHONY: all tables site titles sedonline-fetch sedonline sedonline-site test
reflexes-%: bbox-%       # Semitic reflexes per entry from the PDFs' text layer -> data/volN/sed_volN_reflexes.tsv
	cd scripts && $(PY) reflexes.py $*
afras-%: bbox-%         # Afro-Asiatic comparanda per entry -> data/volN/sed_volN_afras.tsv
	cd scripts && $(PY) afras.py $*
gaps: tables             # Wiktionary gap report from the committed tables + title snapshot
	cd scripts && $(PY) gaps.py
sedonline-fetch:         # crawl http://sed-online.ru/ into build/sedonline/ (network, resumable, ~2,260 requests)
	cd scripts && $(PY) sedonline_fetch.py
sedonline: tables        # parse the cached crawl -> data/sedonline/*.tsv, then compare with the printed SED and Wiktionary
	cd scripts && $(PY) sedonline_parse.py && $(PY) sedonline_compare.py && $(PY) sedonline_missing.py
sedonline-site: sedonline # self-contained browsing page for the SEDonline tables -> site/sedonline.html
	cd scripts && $(PY) build_sedonline_site.py
test:                    # converter and draft tests (no network; ONLINE=1 make test also checks the live wiki)
	$(PY) tests/test_tr2script.py
	$(PY) tests/test_drafts.py
	$(PY) tests/test_cuneiform.py
