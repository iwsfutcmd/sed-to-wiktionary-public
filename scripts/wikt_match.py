import csv,json,re,unicodedata as U,itertools,sys
ps=json.load(open('wik_ps.json'));pw=json.load(open('wik_pws.json'))
def fold(s):
    s=U.normalize('NFC',s)
    for a,b in [('ʾ','ʔ'),('ˀ','ʔ'),('ʿ','ʕ'),('ʻ','ʕ'),('ð','ḏ'),('θ','ṯ'),('ḳ','q'),('γ','ġ'),('ŝ','ś'),('ḡ','ġ'),('δ','ḏ')]:
        s=s.replace(a,b)
    s=U.normalize('NFC',s).replace('-','').replace('*','').strip()
    return s
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
rows=list(csv.reader(open('sed_all.tsv',encoding='utf-8'),delimiter='\t'))
h=rows[0]+['wikt_ps','wikt_ps_title','wikt_pws','wikt_pws_title']
out=[h]
for r in rows[1:]:
    d=dict(zip(rows[0],r))
    vs=expand(d['protoform'])+expand(d['wikt_norm'])+expand(d['affricate_variant'])
    vs=list(dict.fromkeys(vs))
    a=status(*match(IPS,vs));b=status(*match(IPW,vs))
    out.append(r+[a[0],a[1],b[0],b[1]])
json.dump(out,open('wikt_merged.json','w'),ensure_ascii=False)
from collections import Counter
for vol in '12':
    for sec in ('nominal','verbal'):
        rs=[o for o in out[1:] if o[0]==vol and o[1]==sec]
        if rs: print(vol,sec,len(rs),'PS',Counter(o[-4] for o in rs),'PWS',Counter(o[-2] for o in rs))
