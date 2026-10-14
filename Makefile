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
.PHONY: all tables site titles
reflexes-%: bbox-%       # Semitic reflexes per entry from the PDFs' text layer -> data/volN/sed_volN_reflexes.tsv
	cd scripts && $(PY) reflexes.py $*
afras-%: bbox-%         # Afro-Asiatic comparanda per entry -> data/volN/sed_volN_afras.tsv
	cd scripts && $(PY) afras.py $*
gaps: tables             # Wiktionary gap report from the committed tables + title snapshot
	cd scripts && $(PY) gaps.py
