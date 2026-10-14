import sys,json,subprocess
from PIL import Image
vol=sys.argv[1]; items=sys.argv[2:]   # like N34 V5
heads=f'heads_{vol}.json'; pdf=f'../{"v1" if vol=="v1" else "v2"}/vol{vol[1]}.pdf'
best={}
for a in json.load(open(heads)):
    k=a['sec']+str(a['n'])
    if k not in best or len(a['text'])>len(best[k]['text']): best[k]=a
tiles=[]
for k in items:
    a=best[k]
    subprocess.run(['pdftoppm','-r','650','-f',str(a['page']),'-l',str(a['page']),'-png','-singlefile',pdf,'zt'],stderr=subprocess.DEVNULL)
    im=Image.open('zt.png'); s=650/72
    tiles.append(im.crop((int(58*s),int((a['y0']-2)*s),int(200*s),int((min(a['y1'],a['y0']+11)+2)*s))))
W=max(t.width for t in tiles); H=sum(t.height+8 for t in tiles)
c=Image.new('RGB',(W,H),'white'); y=0
for t in tiles: c.paste(t,(0,y)); y+=t.height+8
c.save('zoom_out.png'); print(c.size)
