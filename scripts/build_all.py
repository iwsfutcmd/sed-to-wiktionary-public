import json,csv,re,unicodedata as ud
def norm(f):
    f=f.split('◊')[0].strip().split(',')[0].split('//')[0].strip()
    f=ud.normalize('NFC',f)
    for a,b in (('ṣ̂','ṣ́'),('ŝ','ś'),('ṯ̣','ṱ'),('γ','ġ'),('ḳ','q')): f=f.replace(a,b)
    return f
def pages(fn,pref):
    best={}
    for r in json.load(open(fn)):
        k=(r['sec'],r['n']); sc=(bool(re.match(r'^N ?o ?\. ?\d+ ?\. ?\*',r['text'])),len(r['text']))
        if k not in best or sc>best[k][0]: best[k]=(sc,r['page'])
    return {k:v[1] for k,v in best.items()}
rows=[]
for vol,glf,ov,files,hf in ((1,'glot_v1.json',{'N205':'ʔ','N243':'ʕ','V37':'ʔ','V62':'ʕʕ'},(('N','raw_v1_N.tsv'),('V','raw_v1_V.tsv')),'heads_v1.json'),
                            (2,'glot_v2.json',{},(('N','raw_v2_N.tsv'),),'heads_v2.json')):
    g=json.load(open(glf)); pg=pages(hf,vol)
    for sec,fn in files:
        for l in open(fn,encoding='utf8').read().strip().split('\n'):
            n,pf,gloss=l.split('\t'); key=sec+n; gl=ov.get(key,g.get(key,''))
            if pf.count('Q')==len(gl):
                it=iter(gl); pf=re.sub('Q',lambda m:next(it),pf)
            else: print('mismatch',vol,key,pf,gl)
            parts=[p.strip() for p in pf.split('◊')]
            rows.append(dict(vol=vol,section='nominal' if sec=='N' else 'verbal',no=int(n),protoform=parts[0],affricate_variant=parts[1] if len(parts)>1 else '',gloss=gloss,wikt_norm=norm(parts[0]),pdf_page=pg.get((sec,int(n)))))
json.dump(rows,open('sed_all.json','w'),ensure_ascii=False)
with open('sed_all.tsv','w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
print(len(rows),sum('Q' in r['protoform'] for r in rows))
