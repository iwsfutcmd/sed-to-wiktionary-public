import json,subprocess,urllib.parse,sys
def pull(prefix,out):
    titles=[];cont=None
    while True:
        u="https://en.wiktionary.org/w/api.php?action=query&list=allpages&apnamespace=118&aplimit=max&format=json&apprefix="+urllib.parse.quote(prefix)
        if cont: u+="&apcontinue="+urllib.parse.quote(cont)
        r=subprocess.run(["curl","-sS","-m","60",u],capture_output=True,text=True)
        d=json.loads(r.stdout)
        titles+=[p["title"] for p in d["query"]["allpages"]]
        cont=d.get("continue",{}).get("apcontinue")
        if not cont: break
    json.dump(titles,open(out,"w"),ensure_ascii=False)
    print(prefix,len(titles))
pull("Proto-Semitic/","wik_ps.json")
pull("Proto-West_Semitic/","wik_pws.json")
