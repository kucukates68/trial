import sys, random, json, time, collections; sys.path.insert(0,'.')
from loc import *
from hc3 import mixfrac, dist, TARGET
from hc import evalJ
import hc
hc.PS_MIN=0.999
JMIN=float(sys.argv[1]); WM=float(sys.argv[2]); TAG=sys.argv[3]
lv,geo=load('l01'); q0=[list(q) for q in lv['hand']]; lens=[len(q) for q in q0]
def unflat(f):
    out=[];i=0
    for L in lens: out.append(f[i:i+L]); i+=L
    return out
cache={}
def score(q):
    key=json.dumps(q)
    if key in cache: return cache[key]
    res=evalJ(geo,q)
    if res is None: cache[key]=None; return None
    J,A=res
    if J<JMIN: cache[key]=None; return None
    ev=events(geo,A); s=evsum(ev); md=dist(mixfrac(A))
    obj=WM*md+0.004*s['boyut_ort']+0.1*(1-s['komsu_pay'])+0.03*s['ort_ort']
    cache[key]=(obj,J,A,s,md); return cache[key]
t0=time.time(); pool={}
for seed in range(1,9):
    rnd=random.Random(seed); f=[x for s in q0 for x in s]; rnd.shuffle(f)
    cur=None
    # geçerli bir başlangıç bul
    for _ in range(3000):
        r=score(unflat(f))
        if r: cur=r; break
        i,j=rnd.sample(range(len(f)),2); f[i],f[j]=f[j],f[i]
    if not cur: continue
    fo=cur[0]
    for it in range(4000):
        g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
        if rnd.random()<0.3: k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
        r=score(unflat(g))
        if r is None: continue
        if r[0]<=fo: f,fo=g,r[0]; pool[json.dumps(unflat(g))]=r
print('süre %.0fs'%(time.time()-t0),'havuz',len(pool))
seen=set(); best=[]
for k,v in sorted(pool.items(),key=lambda kv:kv[1][0]):
    q=json.loads(k); canon=tuple(sorted(tuple(x) for x in q))
    if canon in seen: continue
    seen.add(canon); best.append((k,v))
    if len(best)==10: break
out=[]
for k,(obj,J,A,s,md) in best:
    q=json.loads(k); out.append(dict(q=q,obj=obj,J=J,mix={'%d/%d'%a:round(100*b) for a,b in sorted(mixfrac(A).items())},ps=A['root']['ps'],ev=s,orders=A['root']['cnt'],p=A['root']['p']))
    print(round(obj,3),'yanlış/hamle %.1f%%'%(100*J),'mix',out[-1]['mix'],'boyut',s['boyut_ort'],'ort-uzaklık',s['ort_ort'],'orders %.2e'%A['root']['cnt']); print('    ',q)
json.dump(out,open('l01_cands_%s.json'%TAG,'w'))
