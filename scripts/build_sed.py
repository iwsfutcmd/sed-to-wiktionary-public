"""Merge the hand-transcribed raw TSVs with the glottal calls -> data/intermediate/sed_all.{json,tsv}
(no Wiktionary columns yet; wikt_match.py adds them)."""
import json, csv, re, unicodedata as ud
from paths import VOLS, heads, glot, INTER

def norm(f):
    """SED -> Wiktionary spelling of the first variant."""
    f = f.split('◊')[0].strip().split(',')[0].split('//')[0].strip()
    f = ud.normalize('NFC', f)
    for a, b in (('ṣ̂', 'ṣ́'), ('ŝ', 'ś'), ('ṯ̣', 'ṱ'), ('γ', 'ġ'), ('ḳ', 'q')):
        f = f.replace(a, b)
    return f

def pages(v):
    """(section, no) -> pdf page, preferring the candidate that looks like a real 'No. n. *' heading."""
    best = {}
    for r in json.loads(heads(v).read_text(encoding="utf-8")):
        k = (r['sec'], r['n'])
        sc = (bool(re.match(r'^N ?o ?\. ?\d+ ?\. ?\*', r['text'])), len(r['text']))
        if k not in best or sc > best[k][0]:
            best[k] = (sc, r['page'])
    return {k: x[1] for k, x in best.items()}

rows = []
for v, P in VOLS.items():
    g, pg = json.loads(glot(v).read_text(encoding="utf-8")), pages(v)
    for sec, fn in P["raw"]:
        for l in fn.read_text(encoding="utf8").strip().split('\n'):
            n, pf, gloss = l.split('\t')
            key = sec + n
            gl = P["overrides"].get(key, g.get(key, ''))
            if pf.count('Q') == len(gl):
                it = iter(gl)
                pf = re.sub('Q', lambda m: next(it), pf)
            else:
                print('mismatch', v, key, pf, gl)
            parts = [p.strip() for p in pf.split('◊')]
            rows.append(dict(vol=v, section='nominal' if sec == 'N' else 'verbal', no=int(n),
                             protoform=parts[0], affricate_variant=parts[1] if len(parts) > 1 else '',
                             gloss=gloss, wikt_norm=norm(parts[0]), pdf_page=pg.get((sec, int(n)))))
(INTER / "sed_all.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
with open(INTER / "sed_all.tsv", 'w', encoding='utf8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    w.writeheader(); w.writerows(rows)
print(len(rows), 'rows;', sum('Q' in r['protoform'] for r in rows), 'with unresolved Q')
