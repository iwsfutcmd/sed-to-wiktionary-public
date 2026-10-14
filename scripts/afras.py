"""Extract the Afro-Asiatic comparanda listed under each SED entry (the 'Afras.' sub-entries).
usage: afras.py VOL     (reads build/vN/bbl.html from `make bbox-N`, writes data/volN/sed_volN_afras.tsv)

Per sub-entry: the Afras. reconstruction and gloss, then one row per cited form, with the family branch
(Egyp. / Berb. / Chad. / Cush. / Omot.), the sub-group (N. S. E. W. C.) and the language name. The Semitic line
of each sub-entry ('Sem.: above') is skipped (those reflexes are in the reflexes tables). Forms are raw
text-layer OCR, as in reflexes.py."""
import re, sys, csv
from paths import DATA
from reflexes import entry_blocks, split_items, GLOSS, BRANCH, AFRAS, is_running_header

FAMILIES = {'Egyp.': 'Egyp.', 'Berb.': 'Berb.', 'Chad.': 'Chad.', 'Cush.': 'Cush.', 'Omot.': 'Omot.'}
SUBGROUP = re.compile(r'(?:\(\?\)\s*)?(?:[NSEWC]\.\s*){1,2}(?:\*[^\s:]*)?\s*:')
MODS = {'pl.', 'pi.', 'sg.', 'fem.', 'masc.', 'du.', 'f.', 'm.', 'id.', 'redupl.'}
COLS = ['vol', 'section', 'no', 'afras_no', 'afras_protoform', 'afras_gloss', 'branch', 'family', 'subgroup',
        'subgroup_proto', 'lang', 'form', 'note', 'gloss', 'ref', 'flags']

def afras_parts(lines):
    """Split an entry's lines into Afras. sub-entries: [(head_text, [(branch, text)])]."""
    subs, mode, textx, cur = [], None, None, None      # mode: None | 'comment' | 'footnote'
    for x, l in lines:
        t = l.strip()
        if not t or is_running_header(t):
            continue
        if AFRAS.match(t):
            cur = dict(head=re.sub(r'^\S{0,3}\s*Afras\.\s*', '', t), brs=[]); subs.append(cur)
            mode, textx = None, None
            continue
        if cur is None:
            continue
        if t.startswith(('||', '=>', '^')):
            mode = 'comment'; continue
        if mode == 'comment':
            continue
        m = BRANCH.match(t)
        if m:
            mode, textx = None, x + 14
            cur['brs'].append([int(m.group(1)), t[m.end():]])
            continue
        deep = textx is not None and x > textx + 5
        if re.match(r'^[0OoQ]\s', t) and not deep:
            mode = 'footnote'; continue
        if mode == 'footnote':
            if deep:
                continue
            mode = None
        if cur['brs']:
            cur['brs'][-1][1] += ' ' + t
        else:
            cur['head'] += ' ' + t
    return subs

def head_parts(head):
    head = head.strip().rstrip(':').strip()
    m = re.match(r"^([^\s'’‘]*)\s*(.*)$", head)
    return m.group(1), m.group(2).strip().strip("'’‘ ").strip()

def parse_item(it, last_lang):
    fl = []
    m = GLOSS.match(it)
    if m:
        pre, gloss, post = m['pre'].strip(), m['g'].strip(), m['post'].strip()
    else:
        pre, gloss, post = it, '', ''
        mm = re.search(r'\s*([\[(][^\[(]*\d[^\[(]*[\])][.]?)$', it)
        if mm:
            pre, post = it[:mm.start()].strip(), mm.group(1)
    toks = pre.split()
    if toks and toks[0] == '(?)':
        fl.append('uncertain'); toks = toks[1:]
    if toks and toks[0] in ('cf.', 'Cf.'):
        fl.append('cf'); toks = toks[1:]
    lang = []
    while len(toks) > 1 and re.match(r'^[A-Z][^\s]*$', toks[0]):
        lang.append(toks.pop(0))
    note = []
    while len(toks) > 1 and (toks[0] in MODS or re.match(r'^\([A-Za-z.\s]{1,8}\)$', toks[0])):
        note.append(toks.pop(0))
    form = toks[0] if toks else ''
    note += toks[1:]
    if not lang and form:
        lang = [last_lang] if last_lang else []
        if last_lang:
            fl.append('lang_inherited')
    return ' '.join(lang), form, ' '.join(note), gloss, post.rstrip('.').strip(), fl

def parse_branch(num, text, afr):
    text = text.strip()
    m = re.match(r'^([^\s:]+)\s*:?\s*(.*)$', text)
    fam = m.group(1) if m else ''
    if fam.startswith('Egyp'):
        fam = 'Egyp.'
    if fam not in FAMILIES:
        return []                                       # 'Sem.' or unrecognised: skipped
    rest = m.group(2)
    # segments by sub-group marker
    marks = list(SUBGROUP.finditer(rest))
    segs = [('', '', rest[:marks[0].start()] if marks else rest)]
    for i, mk in enumerate(marks):
        end = marks[i+1].start() if i + 1 < len(marks) else len(rest)
        sg = mk.group(0).rstrip(':').strip()
        proto = (re.search(r'\*[^\s:]*', sg) or [''])[0]
        grp = re.sub(r'\*[^\s:]*', '', sg).replace('(?)', '').replace(' ', '')
        segs.append((grp + ('?' if '(?)' in sg else ''), proto, rest[mk.end():end]))
    rows = []
    for grp, proto, seg in segs:
        its = split_items(seg) or split_items(seg, track_quotes=False)
        lang, run = '', []
        for it in its:
            lg, form, note, gloss, ref, fl = parse_item(it, lang)
            if not form:
                continue
            lang = lg or lang
            r = dict(branch=num, family=fam, subgroup=grp, subgroup_proto=proto, lang=lg, form=form,
                     note=note, gloss=gloss, ref=ref, flags=list(fl))
            if "'" in (form + note + ref) and not gloss:
                r['flags'].append('quote_garbled')
            rows.append(r)
        # a gloss given once after a run of forms applies to all of them
        for i in range(len(rows) - 1, -1, -1):
            r = rows[i]
            if (r['subgroup'], r['subgroup_proto']) == (grp, proto) and not r['gloss'] and not r['ref'] \
               and i + 1 < len(rows) and rows[i+1]['gloss'] and rows[i+1]['branch'] == num \
               and (rows[i+1]['subgroup'], rows[i+1]['subgroup_proto']) == (grp, proto):
                r['gloss'] = rows[i+1]['gloss']; r['flags'].append('shared_gloss')
    return rows

def run(v):
    out, nent, nsub = [], 0, 0
    for h, sec, body in entry_blocks(v):
        nent += 1
        for i, sub in enumerate(afras_parts(body), 1):
            nsub += 1
            proto, agloss = head_parts(sub['head'])
            for num, text in sub['brs']:
                for r in parse_branch(num, text, sub):
                    r['flags'] = ';'.join(dict.fromkeys(r['flags']))
                    out.append(dict(vol=v, section=sec, no=h['n'], afras_no=i, afras_protoform=proto,
                                    afras_gloss=agloss, **r))
    dest = DATA / f"vol{v}" / f"sed_vol{v}_afras.tsv"
    with dest.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS, delimiter='\t', lineterminator='\n', extrasaction='ignore')
        w.writeheader(); w.writerows(out)
    print(v, nent, 'entries,', nsub, 'Afras. sub-entries,', len(out), 'forms ->', dest)
    both = [DATA / f"vol{i}" / f"sed_vol{i}_afras.tsv" for i in (1, 2)]
    if all(p.exists() for p in both):
        a, b = (p.read_text(encoding='utf-8') for p in both)
        (DATA / "sed_vol1_vol2_afras.tsv").write_text(a + b.split('\n', 1)[1], encoding='utf-8')

if __name__ == '__main__':
    run(int(sys.argv[1]))
