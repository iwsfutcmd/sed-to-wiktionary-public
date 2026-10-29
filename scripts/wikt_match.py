"""Match every SED form against the Wiktionary title snapshots; write the per-volume and combined TSVs."""
import csv,json,re,unicodedata as U
from collections import Counter
from paths import DATA,INTER,WIKT
ps=json.loads((WIKT/'wik_ps.json').read_text(encoding='utf-8'));pw=json.loads((WIKT/'wik_pws.json').read_text(encoding='utf-8'))
def canon(s):
    """NFC, with each run of combining marks sorted, so ṯ+dot-below and dot-below+ṯ compare equal."""
    out, run = [], []
    for ch in U.normalize('NFD', s):
        if U.combining(ch):
            run.append(ch)
        else:
            out += sorted(run); run = []; out.append(ch)
    out += sorted(run)
    return U.normalize('NFC', ''.join(out))
def fold(s):
    s=U.normalize('NFC',s)
    for a,b in [('ʾ','ʔ'),('ˀ','ʔ'),('ʿ','ʕ'),('ʻ','ʕ'),('ð','ḏ'),('θ','ṯ'),('ḳ','q'),('γ','ġ'),('ŝ','ś'),('ḡ','ġ'),('δ','ḏ')]:
        s=s.replace(a,b)
    s=s.replace('ṱ','ṯ̣')          # U+1E71 (t + circumflex below) is the same sound as ṯ̣; Wiktionary mostly writes ṯ + dot below
    return canon(s).replace('-','').replace('*','').strip()
def idx(titles):
    d={}
    for t in titles:
        form=t.split('/',1)[1]
        d.setdefault(fold(form),[]).append(form)
    return d
IPS,IPW=idx(ps),idx(pw)
VOW='[aiuāīūēō]'
def expand(f):
    """yield (variant, schematic?) strings"""
    f=f.strip().lstrip('*')
    alts=[x.strip() for x in re.split(r'\s*\(or\s+|\)\s*$|\s+or\s+|,\s*|//',f) if x.strip()]
    out=[]
    for a in alts:
        a=a.strip().lstrip('*').rstrip(')').strip()
        a=a.replace('(-)','')
        vs=[a]
        for _ in range(4):
            nv=[]
            for v in vs:
                m=re.search(r'\(([^()]*)\)',v)
                if m and m.group(1)!='V':
                    nv+= [v[:m.start()]+v[m.end():], v[:m.start()]+m.group(1)+v[m.end():]]
                else: nv.append(v)
            vs=nv
        vs2=[]
        for v in vs:
            m=re.search(r'(.)/(.)',v)
            if m: vs2+=[v[:m.start()]+m.group(1)+v[m.end():], v[:m.start()]+m.group(2)+v[m.end():]]
            else: vs2.append(v)
        out+=vs2
    return [o.replace('(V)','V') for o in out if o]
def match(idxd,variants):
    exact=set();pat=set()
    for v in variants:
        fv=fold(v)
        if 'V' in fv or 'S' in fv:
            if len(re.sub('[Vaiuāīūēō]','',fv))<3: continue
            rx=re.compile('^'+re.escape(fv).replace('V',VOW).replace('S','[sšśṣzž]')+'$')
            for k,ts in idxd.items():
                if rx.match(k): pat.update(ts)
        elif fv in idxd: exact.update(idxd[fv])
    return exact,pat
def status(ex,pa):
    if ex: return 'yes',';'.join(sorted(ex))
    if pa: return 'pattern',';'.join(sorted(pa))
    return 'no',''
# SEDonline's form of the same entry (sed_ref 1N:25 = vol 1, nominal, no. 25): the PDF text loses some diacritics (*ʕaṯ̣m- came out as
# *ʕaṯm-), so a page under the correct spelling was missed and the entry counted as a gap
# SEDonline's sed_ref is not unique (1N:44 also tags *nhḳ, *dbr ...), so its form is used only when it is the same entry: the same letters once
# diacritics are stripped, and a gloss word in common
SITE={}
for r in csv.DictReader(open(DATA/'sedonline'/'sedonline_reconstructions.tsv',encoding='utf-8'),delimiter='\t'):
    if r.get('sed_ref'): SITE.setdefault(r['sed_ref'],[]).append((r['norm'],r['gloss']))
def bare(f):
    f=re.sub(r'\([^()]*\)','',fold(f))                              # optional parts: *ʕaṯm(-at)-
    f=''.join(c for c in U.normalize('NFD',f) if not U.combining(c))
    return re.sub(r'[aiueoāīūēōV/,\-*\s]','',f)
def gwords(g): return set(re.findall(r'[a-z]{3,}',g.lower()))-{'the','and','kind','with'}
def site_forms(key,d):
    alts=set()
    for part in d['protoform'].split(','):                           # *ṗVrγVṯ-, *ṗVrṯaγ-: each form; *maʕay/w-: each letter of an alternation
        alts|={re.sub(r'(\S)/(\S)',lambda m:m.group(i),part) for i in (1,2)}
    return [n for n,g in SITE.get(key,[]) if bare(n) in {bare(a) for a in alts} and gwords(g)&gwords(d['gloss'])]
rows=list(csv.reader(open(INTER/'sed_all.tsv',encoding='utf-8'),delimiter='\t'))
h=rows[0]+['wikt_ps','wikt_ps_title','wikt_pws','wikt_pws_title']
out=[h]
for r in rows[1:]:
    d=dict(zip(rows[0],r))
    key=f"{d['vol']}{d['section'][0].upper()}:{d['no']}"
    vs=list(dict.fromkeys(expand(d['protoform'])+expand(d['wikt_norm'])+expand(d['affricate_variant'])+[v for f in site_forms(key,d) for v in expand(f)]))
    a=status(*match(IPS,vs));b=status(*match(IPW,vs))
    out.append(r+[a[0],a[1],b[0],b[1]])
def write(path,rs):
    with open(path,'w',encoding='utf-8',newline='') as f:
        csv.writer(f,delimiter='\t',lineterminator='\n').writerows([h]+rs)
(DATA/'vol1').mkdir(exist_ok=True);(DATA/'vol2').mkdir(exist_ok=True)
write(DATA/'vol1'/'sed_vol1_reconstructions.tsv',[r for r in out[1:] if r[0]=='1'])
write(DATA/'vol2'/'sed_vol2_reconstructions.tsv',[r for r in out[1:] if r[0]=='2'])
write(DATA/'sed_vol1_vol2_reconstructions.tsv',out[1:])
# JSON for the browser page: typed copy of the combined table
recs=[dict(zip(h,r)) for r in out[1:]]
for d in recs:
    d['vol']=int(d['vol']);d['no']=int(d['no']);d['pdf_page']=int(d['pdf_page']) if d['pdf_page'] else ''
(INTER/'sed_all.json').write_text(json.dumps(recs,ensure_ascii=False),encoding='utf-8')
for vol in '12':
    for sec in ('nominal','verbal'):
        rs=[o for o in out[1:] if o[0]==vol and o[1]==sec]
        if rs: print(vol,sec,len(rs),'PS',dict(Counter(o[-4] for o in rs)),'PWS',dict(Counter(o[-2] for o in rs)))
