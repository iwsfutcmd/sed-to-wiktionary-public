import json,csv,re,sys,unicodedata as ud
g=json.load(open('glot_v1.json'))
ov={'N205':'ʔ','N243':'ʕ','V37':'ʔ','V62':'ʕʕ'}
def sub(s,gl,key):
    n=s.count('Q')
    if len(gl)!=n: return None,(key,n,gl)
    it=iter(gl); return re.sub('Q',lambda m:next(it),s),None
def norm(f):
    f=f.split('◊')[0].strip().split(',')[0].strip()
    f=ud.normalize('NFC',f)
    f=f.replace('ṣ̂','ṣ́').replace('ŝ','ś').replace('ṯ̣','ṱ').replace('γ','ġ').replace('ḳ','q').replace('ʷ','ʷ')
    return f
rows=[];bad=[]
for sec,fn in (('N','raw_v1_N.tsv'),('V','raw_v1_V.tsv')):
    for l in open(fn,encoding='utf8').read().strip().split('\n'):
        n,pf,gloss=l.split('\t'); key=sec+n
        gl=ov.get(key,g.get(key,''))
        out,err=sub(pf,gl,key)
        if err: bad.append(err); out=pf
        parts=[p.strip() for p in out.split('◊')]
        rows.append(dict(vol=1,section='nominal' if sec=='N' else 'verbal',no=int(n),protoform=parts[0],affricate_variant=parts[1] if len(parts)>1 else '',gloss=gloss,wikt_norm=norm(parts[0])))
json.dump(rows,open('sed1.json','w'),ensure_ascii=False,indent=1)
with open('sed1.tsv','w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
print(len(rows),'bad:',bad)
