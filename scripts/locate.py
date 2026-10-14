import re, json, sys, html
src=sys.argv[1]; first_page=int(sys.argv[2]); out=sys.argv[3]; vstart=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
t=open(src,encoding='utf-8').read()
pages=re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>',t,re.S)
recs=[]
for i,(w,h,body) in enumerate(pages):
    pno=first_page+i
    lines=[]
    for lm in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>',body,re.S):
        x0,y0,x1,y1=map(float,lm.groups()[:4])
        words=[html.unescape(x) for x in re.findall(r'>([^<]*)</word>',lm.group(5))]
        lines.append((y0,x0,y1,x1,words))
    lines.sort()
    for k,(y0,x0,y1,x1,words) in enumerate(lines):
        s=''.join(words)
        m=re.match(r'^No\.(\d+)\.',s)
        if not m or y0<35: continue
        # reject running header: page number as last word far right
        if words[-1].isdigit() and x1>330 and len(words)>3: continue
        # extent: include gloss on same y (other line) and continuation lines starting with quote
        ymax=y1
        for (a0,b0,a1,b1,w2) in lines:
            if abs(a0-y0)<4 and (a0,b0)!=(y0,x0): ymax=max(ymax,a1)
        for (a0,b0,a1,b1,w2) in lines:
            if y1-1<=a0<=y1+16 and w2 and w2[0][:1] in "'’‘" : ymax=max(ymax,a1)
        recs.append(dict(page=pno,n=int(m.group(1)),y0=y0,y1=ymax,sec='V' if pno>=vstart else 'N',pw=float(w),ph=float(h),text=' '.join(words)))
json.dump(recs,open(out,'w'),ensure_ascii=False,indent=0)
from collections import Counter
for sec in 'NV':
    ns=sorted(r['n'] for r in recs if r['sec']==sec)
    c=Counter(ns)
    print(sec,len(ns),'unique',len(c),'max',max(ns) if ns else None,'dups',[k for k,v in c.items() if v>1][:20],'missing',[k for k in range(1,(max(ns) if ns else 0)+1) if k not in c][:30])
