#!/usr/bin/env python3
"""Writes data/stats.json (public numbers for the iPhone widget). Run from the repo root."""
import json,re,datetime
s=open('index.html',encoding='utf-8').read()
g=lambda i:json.loads(re.search(r'id="%s">(.*?)</script>'%i,s,re.S).group(1))
dec,jd=g('decdata'),g('jddata')
n=json.load(open('cvx/keys.json')).get('n',0)
today=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=3)).date().isoformat()
AR=['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
ard=lambda d:f"{int(d[8:])} {AR[int(d[5:7])-1]} {d[:4]}"
nxt=None
for d in dec:
    for dt,pct in (d.get('calc') or {}).get('ph',[]):
        if dt>today and (nxt is None or dt<nxt[0]): nxt=(dt,d['t'],pct)
out={"cvs":n,"decisions":len(dec),"jd":len(jd),
     "latest":{"t":dec[0]['t'],"start":dec[0].get('start',''),"pct":dec[0].get('pct','')},
     "next":({"date":ard(nxt[0]),"iso":nxt[0],"t":nxt[1],"pct":nxt[2]} if nxt else None),
     "updated":today}
json.dump(out,open('data/stats.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False))
