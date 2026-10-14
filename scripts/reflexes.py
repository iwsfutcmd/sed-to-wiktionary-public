"""Extract the Semitic reflexes listed under each SED entry (language, form, gloss, reference).
usage: reflexes.py VOL     (reads build/vN/bbl.html from `make bbox-N`, writes data/volN/sed_volN_reflexes.tsv)

The PDFs' OCR text layer garbles diacritics and glottals (ʔ -> ? / H / f, ʕ -> 9, ...), so forms are kept
exactly as the text layer has them (`form`) and are NOT normalised. Only the Semitic block of each entry is
read (heading up to the 'Afras.' sub-entry); '||' comment paragraphs and '0' footnotes are skipped."""
import re, json, sys, csv, html
from paths import VOLS, heads, DATA, BUILD

HEAD = r'^\s*N\s?o\s?\.\s*{n}\s*\.'
SIGLUM = re.compile(r'^((?:\(\?\)\s*)?)((?:Cf\.\s*)?)((?:(?:[A-Z][A-Za-z]{1,5}|pB)\.\s+)+)')
AFRAS = re.compile(r'^\s*\S{0,3}\s*Afras\.\s*\*')
BRANCH = re.compile(r'^\s*\[(\d)\]\s?')

def bbox_lines(v):
    """(page, indent_pt, text) per printed line from pdftotext -bbox-layout; letter-spaced runs are rejoined
    (inside such runs letter gaps are < 2.7 pt, word gaps >= 3.6 pt)."""
    P = VOLS[v]
    t = (BUILD / f"v{v}" / "bbl.html").read_text(encoding='utf-8')
    out = []
    for i, (_, _, body) in enumerate(re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', t, re.S)):
        for lm in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)"[^>]*>(.*?)</line>', body, re.S):
            if float(lm.group(2)) < 35:
                continue
            ws = [(float(a), float(b), html.unescape(w)) for a, b, w in
                  re.findall(r'<word xMin="([\d.]+)" yMin="[\d.]+" xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>', lm.group(3))]
            if not ws:
                continue
            s = ws[0][2]
            for (a0, b0, w0), (a1, b1, w1) in zip(ws, ws[1:]):
                s += ('' if a1 - b0 < 2.7 else ' ') + w1
            out.append((P['first'] + i, float(lm.group(1)), s))
    return out

def is_running_header(l):
    s = l.strip()
    return bool(re.search(r'\s{3,}\d+$', s) or re.match(r'^\d+\s{3,}', s))

def semitic_lines(lines):
    """lines: (x_pt, text). Yield (branch, is_continuation, text) for lines that can hold reflexes."""
    branch, mode, textx = None, None, None      # mode: None | 'comment' | 'footnote'
    for x, l in lines:
        t = l.strip()
        if not t:
            continue
        if AFRAS.match(t) or t.startswith(('=>', '^ ')):
            break
        if is_running_header(t):
            continue
        if t.startswith('||'):
            mode = 'comment'; continue
        m = BRANCH.match(t)
        if m:
            branch, mode = int(m.group(1)), None
            textx = x + 14                         # where text after '[n] ' starts
            yield branch, False, t[m.end():]
            continue
        deep = textx is not None and x > textx + 5
        if mode == 'comment':
            if not deep and SIGLUM.match(t) and x < (textx or 0) - 8:
                mode = None                       # paragraph ended (text back at the left margin)
            else:
                continue
        if re.match(r'^[0OoQ]\s', t) and not deep:   # footnote marker
            mode = 'footnote'; continue
        if mode == 'footnote':
            if not deep and SIGLUM.match(t):
                mode = None
            else:
                continue
        yield branch, deep, t

def records(lines):
    """Join continuation lines into one record per line that starts a new language group."""
    cur = None
    for br, deep, t in semitic_lines(lines):
        if not deep and (SIGLUM.match(t) or cur is None):
            if cur: yield cur
            cur = [br, t]
        elif cur:
            cur[1] += ' ' + t
    if cur: yield cur

def split_items(s, track_quotes=True):
    """Split at depth-0 ',' / ';', ignoring separators inside brackets and 'gloss' quotes."""
    out, buf, depth, inq = [], [], 0, False
    for i, ch in enumerate(s):
        prev = s[i-1] if i else ' '
        nxt = s[i+1] if i + 1 < len(s) else ' '
        if not track_quotes:
            pass
        elif ch in "'’‘" and not inq and (prev.isspace() or prev in '(['):
            inq = True
        elif ch in "'’" and inq and not nxt.isalnum():
            inq = False
        elif not inq and ch in '([':
            depth += 1
        elif not inq and ch in ')]':
            depth = max(0, depth - 1)
        if ch in ',;' and depth == 0 and not inq:
            out.append(''.join(buf)); buf = []
        else:
            buf.append(ch)
    out.append(''.join(buf))
    if inq and track_quotes:             # a quote opened and never closed: delimit without quotes instead
        return None
    return [x.strip() for x in out if x.strip()]

GLOSS = re.compile(r"""^(?P<pre>.*?)(?:\s|^)(?P<q>['’‘])(?P<g>.*?)['’](?=$|[\s\)\]\.,;])(?P<post>.*)$""")
def parse_item(it):
    m = GLOSS.match(it)
    if m:
        pre, gloss, post = m['pre'].strip(), m['g'].strip(), m['post'].strip()
    else:
        pre, gloss, post = it, '', ''
        mm = re.search(r'\s*([\[(][^\[(]*\d[^\[(]*[\])][.]?)$', it)     # trailing reference group
        if mm:
            pre, post = it[:mm.start()].strip(), mm.group(1)
        mi = re.search(r'\bid\.$', pre)
        if mi:
            pre, gloss = pre[:mi.start()].strip(), 'id.'
    parts = pre.split(None, 1)
    return (parts[0] if parts else ''), (parts[1] if len(parts) > 1 else ''), gloss, post.rstrip('.').strip()

def parse_record(branch, text):
    rows, lang, flags0 = [], '', ''
    its = split_items(text)
    garbled = its is None
    for it in its or split_items(text, track_quotes=False):
        m = SIGLUM.match(it)
        fl = []
        if m:
            lang = m.group(3).strip()
            fl += (['uncertain'] if m.group(1) else []) + (['cf'] if m.group(2) else [])
            it = it[m.end():]
            flags0 = ';'.join(fl)
        else:
            fl = flags0.split(';') if flags0 else []
        form, note, gloss, ref = parse_item(it)
        if garbled or (not gloss and "'" in (note + ref + form)):
            fl.append('quote_garbled')       # an opening/closing quote was lost to OCR
        if not form:
            continue
        if re.search(r'(?:\b\w ){5,}', gloss + ' '):
            fl.append('spaced_ocr')
        rows.append(dict(branch=branch, lang=lang, form=form, note=note, gloss=gloss, ref=ref, flags=fl))
    # a gloss given once after a comma-run of forms applies to the whole run
    for i in range(len(rows) - 1, -1, -1):
        r = rows[i]
        if not r['gloss'] and not r['ref'] and not r['note'] and i + 1 < len(rows) \
           and rows[i+1]['lang'] == r['lang'] and rows[i+1]['gloss'] and 'cf' not in r['flags']:
            r['gloss'] = rows[i+1]['gloss']; r['flags'].append('shared_gloss')
    for r in rows:
        r['flags'] = ';'.join(dict.fromkeys(x for x in r['flags'] if x))
    return rows

COLS = ['vol', 'section', 'no', 'branch', 'lang', 'form', 'note', 'gloss', 'ref', 'flags']

def run(v):
    P = VOLS[v]
    hs = json.loads(heads(v).read_text(encoding='utf-8'))
    best = {}
    for h in hs:      # the heads file also holds running headers; keep the candidate that looks like a real heading
        sc = (bool(re.match(r'^N ?o ?\. ?\d+ ?\. ?\*', h['text'])), len(h['text']))
        k = (h['sec'], h['n'])
        if k not in best or sc > best[k][0]:
            best[k] = (sc, h)
    hs = sorted((x[1] for x in best.values()), key=lambda h: (h['page'], h['y0']))
    flat = bbox_lines(v)
    cursor, marks = 0, []
    for h in hs:
        pat = re.compile(HEAD.format(n=h['n']))
        for k in range(cursor, len(flat)):
            page, x, l = flat[k]
            if page == h['page'] and pat.match(l) and not is_running_header(l):
                marks.append((k, h)); cursor = k + 1; break
        else:
            print('heading not found', v, h['sec'], h['n'], h['page'], file=sys.stderr)
    out = []
    for j, (k, h) in enumerate(marks):
        end = marks[j+1][0] if j + 1 < len(marks) else len(flat)
        body = [(x, l) for _, x, l in flat[k+1:end]]
        sec = 'verbal' if h['sec'] == 'V' else 'nominal'
        for br, text in records(body):
            if br is None:                      # heading continuation (gloss / variants), before the first [n]
                continue
            for r in parse_record(br, text):
                out.append(dict(vol=v, section=sec, no=h['n'], **r))
    dest = DATA / f"vol{v}" / f"sed_vol{v}_reflexes.tsv"
    with dest.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS, delimiter='\t', lineterminator='\n', extrasaction='ignore')
        w.writeheader(); w.writerows(out)
    print(v, len(marks), 'entries,', len(out), 'reflexes ->', dest)
    both = [DATA / f"vol{i}" / f"sed_vol{i}_reflexes.tsv" for i in (1, 2)]
    if all(p.exists() for p in both):       # concatenation, like sed_vol1_vol2_reconstructions.tsv
        a, b = (p.read_text(encoding='utf-8') for p in both)
        (DATA / "sed_vol1_vol2_reflexes.tsv").write_text(a + b.split('\n', 1)[1], encoding='utf-8')

if __name__ == '__main__':
    run(int(sys.argv[1]))
