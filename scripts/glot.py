import json,numpy as np,cv2,sys
from scipy import ndimage as ndi
s=400/72
best={}
for a in json.load(open('heads_v1.json')):
    k=(a['sec'],a['n'])
    if k not in best or len(a['text'])>len(best[k]['text']): best[k]=a
def comps(a):
    im=cv2.imread(f"../v1/crops/p{a['page']}.png",0)
    y0=int((a['y0']-3)*s); y1=int((min(a['y1'],a['y0']+11)+3)*s)
    sub=im[y0:y1,int(58*s):int(328*s)]
    bw=(sub<140)
    lab,n=ndi.label(bw,structure=np.ones((3,3)))
    out=[]
    for i,sl in enumerate(ndi.find_objects(lab),1):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        out.append((sl[1].start,sl[0].start,w,h,sl[0].stop,(lab[sl]==i).sum()))
    return sub,lab,out
if __name__=='__main__':
    for n in (1,28):
        a=best[('N',n)]
        sub,lab,out=comps(a)
        print(n,sub.shape)
        for c in sorted(out)[:14]: print(c)

def glyphs(a):
    sub,lab,out=comps(a)
    # baseline: median bottom of x-height-ish letters (h 28..37, w>=24) 
    xs=[c for c in out if 28<=c[3]<=37 and c[2]>=24]
    if not xs: return []
    base=np.median([c[4] for c in xs])
    res=[]
    for i,sl in enumerate(ndi.find_objects(lab),1):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if 13<=w<=24 and 27<=h<=38 and abs((sl[0].stop)-(base-8))<=3:
            g=(lab[sl]==i)
            ys,xs_=np.nonzero(g)
            top=xs_[ys<h*0.45].mean(); bot=xs_[ys>h*0.7].mean()
            res.append((sl[1].start,round(float(top-bot),2)))
    return sorted(res)
