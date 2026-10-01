import sys, json, random, time, collections; sys.path.insert(0,'.')
from l2 import *
T=float(sys.argv[1]); iters=int(sys.argv[2]); wP=float(sys.argv[3])
order=valid_order(cv,geo); n=len(order); q0=[[],[],[]]
for k in range(n): q0[k%3].append(order[k])
lens=[len(x) for x in q0]
def unflat(f):
    out=[];i=0
    for L in lens: out.append(f[i:i+L]); i+=L
    return out
cache={}
def score(q):
    key=json.dumps(q)
    if key in cache: return cache[key]
    res=evalq(q)
    if res is None: cache[key]=None; return None
    J,A=res; ev=events(geo,A); s=evsum(ev); mf=mixfrac(A); md=dist(mf)
    W_=sum(e['w'] for e in ev); psh=sum(e['w'] for e in ev if e['nvict']>=2)/W_ if W_ else 0
    obj=3*abs(J-T)+0.5*md+0.1*(1-s['komsu_pay'])+wP*(1-psh)+0.002*s['boyut_ort']
    cache[key]=(obj,J,A,s,md,psh,mf); return cache[key]
pool={}; t0=time.time()
for seed in range(1,9):
    rnd=random.Random(seed); f=[x for s in q0 for x in s]
    if seed>1: 
        for _ in range(30):
            i,j=rnd.sample(range(len(f)),2); f[i],f[j]=f[j],f[i]
    cur=None
    for _ in range(500):
        cur=score(unflat(f))
        if cur: break
        i,j=rnd.sample(range(len(f)),2); f[i],f[j]=f[j],f[i]
    if not cur: continue
    fo=cur[0]
    for it in range(2500):
        g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
        if rnd.random()<0.3: k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
        r=score(unflat(g))
        if r is None: continue
        if r[0]<=fo: f,fo=g,r[0]; pool[json.dumps(unflat(g))]=r
print('süre %.0fs havuz %d'%(time.time()-t0,len(pool)))
seen=set(); out=[]
for k,v in sorted(pool.items(),key=lambda kv:kv[1][0]):
    q=json.loads(k); canon=tuple(sorted(tuple(x) for x in q))
    if canon in seen: continue
    seen.add(canon); obj,J,A,s,md,psh,mf=v
    print('yanlış/hamle %.1f%%'%(100*J),'mix',{'%d/%d'%a:round(100*b) for a,b in sorted(mf.items())},'geçiş-olay payı %.0f%%'%(100*psh),'boyut',s['boyut_ort'],'en-yakın',s['yakin_ort'],'ort-uzak',s['ort_ort'],'med',s['ort_med'],'kurban parça',s['kurban_say'],'komşu',s['komsu_pay'],'orders %.1e'%A['root']['cnt']); print('    ',q); out.append(q)
    if len(seen)==5: break
json.dump(out,open('l02v2_c_T%d_P%d.json'%(int(100*T),int(10*wP)),'w'))
