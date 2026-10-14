"""Where are the Wiktionary gaps? One row per SED reconstruction with its Wiktionary status, how widely it is
attested in SED (Semitic branches / languages, Afro-Asiatic comparanda) and whether Wiktionary has a page with the
same consonantal skeleton under another vocalisation. Sorted by attestation, so well-attested missing pages come first.
usage: gaps.py     (reads data/*.tsv and data/wiktionary/*.json, writes data/sed_wiktionary_gaps.tsv)"""
import csv, json, re, unicodedata as U
from collections import defaultdict
from paths import DATA, WIKT
from wikt_match import fold, expand      # reuses the matcher's folding (runs it once as a side effect)

VOWELS = 'aiuāīūēōeo'
def skeleton(form):
    f = fold(form)
    f = re.sub(r'\([^()]*\)', '', f)
    f = U.normalize('NFC', f)
    f = re.sub('[' + VOWELS + r'VQ\-/\s]', '', f)
    return re.sub(r'(.)\1', r'\1', f)           # geminates collapse

def read(p):
    return list(csv.DictReader(open(p, encoding='utf-8'), delimiter='\t'))

recs = read(DATA / 'sed_vol1_vol2_reconstructions.tsv')
refl, afr = defaultdict(list), defaultdict(int)
for r in read(DATA / 'sed_vol1_vol2_reflexes.tsv'):
    refl[(r['vol'], r['section'], r['no'])].append(r)
for r in read(DATA / 'sed_vol1_vol2_afras.tsv'):
    afr[(r['vol'], r['section'], r['no'])] += 1

titles = [('PS', t.split('/', 1)[1]) for t in json.loads((WIKT / 'wik_ps.json').read_text(encoding='utf-8'))] + \
         [('PWS', t.split('/', 1)[1]) for t in json.loads((WIKT / 'wik_pws.json').read_text(encoding='utf-8'))]
by_skel = defaultdict(list)
for kind, t in titles:
    by_skel[skeleton(t)].append(f'{kind}:{t}')

out = []
for r in recs:
    key = (r['vol'], r['section'], r['no'])
    rows = [x for x in refl.get(key, []) if 'cf' not in x['flags']]
    langs = {(x['lang'].split() or [''])[0] for x in rows if x['lang']}
    branches = {x['branch'] for x in rows if x['branch']}
    covered = r['wikt_ps'] in ('yes', 'pattern') or r['wikt_pws'] in ('yes', 'pattern')
    skels = {skeleton(v) for v in expand(r['wikt_norm']) if v}
    near = sorted({t for s in skels if len(s) >= 3 for t in by_skel.get(s, [])})
    status = 'covered' if covered else ('same_skeleton' if near else 'gap')
    out.append(dict(vol=r['vol'], section=r['section'], no=r['no'], protoform=r['protoform'], gloss=r['gloss'],
                    status=status, wikt_ps=r['wikt_ps'], wikt_pws=r['wikt_pws'], same_skeleton=';'.join(near),
                    n_branches=len(branches), n_langs=len(langs), n_afras=afr.get(key, 0), pdf_page=r['pdf_page']))
order = {'gap': 0, 'same_skeleton': 1, 'covered': 2}
out.sort(key=lambda d: (order[d['status']], -d['n_branches'], -d['n_langs'], -d['n_afras'], d['vol'], int(d['no'])))
cols = list(out[0])
with open(DATA / 'sed_wiktionary_gaps.tsv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, cols, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter(d['status'] for d in out))
print('gaps attested in >=5 branches:', sum(1 for d in out if d['status'] == 'gap' and d['n_branches'] >= 5))
