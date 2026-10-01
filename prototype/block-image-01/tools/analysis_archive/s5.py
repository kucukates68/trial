import sys, random, json, time; sys.path.insert(0,'.')
from loc import *
from hc3 import mixfrac, dist
from hc import evalJ
import hc
hc.PS_MIN=0.999
lv,geo=load('l01'); cand=json.load(open('l01_cands.json'))[0]['q']; lens=[len(q) for q in cand]
def unflat(f):
    out=[];i=0
    for L in lens: out.append(f[i:i+L]); i+=L
    return out
def sc(q,wJ):
    res=evalJ(geo,q)
    if res is None: return None
    J,A=res; ev=evsum(events(geo,A)); md=dist(mixfrac(A))
    # amaç: yanlış oranı yüksek, 3/1 aşırı olmasın (md), kapanan alan küçük ve komşu
    return (-wJ*J+0.5*md+0.004*ev['boyut_ort']+0.1*(1-ev['komsu_pay'])+0.03*ev['ort_ort']),J,A,ev,md
for wJ in (1.0,2.0):
    pool={}
    for seed in range(1,7):
        rnd=random.Random(seed); f=[x for s in cand for x in s]; cur=sc(unflat(f),wJ); fo=cur[0]
        for it in range(3000):
            g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
            if rnd.random()<0.3: k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
            r=sc(unflat(g),wJ)
            if r is None: continue
            if r[0]<=fo: f,fo=g,r[0]; pool[json.dumps(unflat(g))]=r
    seen=set(); print('wJ',wJ,'havuz',len(pool))
    for k,v in sorted(pool.items(),key=lambda kv:kv[1][0]):
        q=json.loads(k); canon=tuple(sorted(tuple(x) for x in q))
        if canon in seen: continue
        seen.add(canon); obj,J,A,ev,md=v
        print('  yanlış/hamle %.1f%%'%(100*J),'mix',{'%d/%d'%a:round(100*b) for a,b in sorted(mixfrac(A).items())},'boyut',ev['boyut_ort'],'ort-uzak',ev['ort_ort'],'komşu',ev['komsu_pay'],'orders %.1e'%A['root']['cnt']); print('     ',q)
        if len(seen)==4: break
