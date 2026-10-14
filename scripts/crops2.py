import json,subprocess,os,sys,re
from PIL import Image, ImageDraw
pdf=sys.argv[1]; heads=sys.argv[2]; outdir=sys.argv[3]; per=int(sys.argv[4]); dpi=400
os.makedirs(outdir,exist_ok=True)
allr=json.load(open(heads))
best={}
for r in allr:
    k=(r['sec'],r['n'])
    sc=lambda r:(bool(re.match(r'^N ?o ?\. ?\d+ ?\. ?\*',r['text'])),len(r['text']))
    if k not in best or sc(r)>sc(best[k]): best[k]=r
recs=sorted(best.values(),key=lambda r:(r['sec'],r['n']))
print(len(recs))
cache={}
def page_img(p):
    f=f'{outdir}/p{p}.png'
    if not os.path.exists(f):
        subprocess.run(['pdftoppm','-r',str(dpi),'-f',str(p),'-l',str(p),'-png','-singlefile',pdf,f[:-4]],stderr=subprocess.DEVNULL)
    return Image.open(f).convert('RGB')
s=dpi/72
batches=[]
for bi in range(0,len(recs),per):
    chunk=recs[bi:bi+per]; crops=[]
    for r in chunk:
        im=page_img(r['page'])
        box=(int(25*s),int((r['y0']-3)*s),int(400*s),int((r['y1']+3)*s))
        crops.append(im.crop(box))
    W=max(c.width for c in crops); H=sum(c.height+10 for c in crops)
    canvas=Image.new('RGB',(W,H),'white'); y=0
    d=ImageDraw.Draw(canvas)
    for c in crops:
        canvas.paste(c,(0,y)); y+=c.height
        d.line([(0,y+4),(W,y+4)],fill=(200,200,200),width=1); y+=10
    fn=f'{outdir}/batch_{bi//per+1:02d}.png'; canvas.save(fn)
    batches.append((fn,[(r['sec'],r['n'],r['page']) for r in chunk]))
json.dump(batches,open(f'{outdir}/manifest.json','w'))
print(len(batches),'batches')
