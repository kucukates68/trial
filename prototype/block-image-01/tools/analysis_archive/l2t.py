import sys, json, random, time, collections; sys.path.insert(0,'.')
from l2 import *
T=float(sys.argv[1]); iters=int(sys.argv[2]); wA=float(sys.argv[3]); tag=sys.argv[4]
order=valid_order(cv,geo); n=len(order); q0=[[],[],[]]
for k in range(n): q0[k%3].append(order[k])
lens=[len(x) for x in q0]
ARM=lambda s: s.startswith('ARM_') or s in('FLOWER_L','FLOWER_R','SPINE_7','SPINE_8')
def unflat(f):
    out=[];i=0
    for L in lens: out.append(f[i:i+L]); i+=L
    return out
cache={}
def cls(ev):
    tot=sum(e['w'] for e in ev); arm=sum(e['w'] for e in ev if ARM(e['p']) or any(ARM(v) for v in e['vict']))/tot
    spine_only=sum(e['w'] for e in ev if all(v.startswith('SPINE') for v in e['vict']))/tot
    byc=collections.Counter()
    for e in ev: byc[e['p']]+=e['w']
    herf=sum((v/tot)**2 for v in byc.values())
    return arm,spine_only,herf
def score(q):
    key=json.dumps(q)
    if key in cache: return cache[key]
    res=evalq(q)
    if res is None: cache[key]=None; return None
    J,A=res; ev=events(geo,A); s=evsum(ev); mf=mixfrac(A); md=dist(mf); arm,sp,herf=cls(ev)
    obj=3*abs(J-T)+0.5*md+0.1*(1-s['komsu_pay'])+wA*max(0,0.5-arm)+0.5*max(0,sp-0.25)+0.3*herf+0.002*s['boyut_ort']
    cache[key]=(obj,J,A,s,md,arm,sp,herf,mf); return cache[key]
pool={}; t0=time.time()
for seed in range(1,11):
    rnd=random.Random(seed); f=[x for s in q0 for x in s]
    for _ in range(0 if seed==1 else 2):
        i,j=rnd.sample(range(len(f)),2); f[i],f[j]=f[j],f[i]
    cur=None
    for _ in range(800):
        cur=score(unflat(f))
        if cur: break
        i,j=rnd.sample(range(len(f)),2); f[i],f[j]=f[j],f[i]
    if not cur: continue
    fo=cur[0]
    for it in range(3000):
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
    seen.add(canon); obj,J,A,s,md,arm,sp,herf,mf=v
    print('yanlış/hamle %.1f%%'%(100*J),'mix',{'%d/%d'%a:round(100*b) for a,b in sorted(mf.items())},'kol-olay %.0f%% sivri-cep %.0f%% yoğunluk %.2f'%(100*arm,100*sp,herf),'boyut',s['boyut_ort'],'ort-uzak',s['ort_ort'],'komşu',s['komsu_pay'],'orders %.1e'%A['root']['cnt']); print('    ',q); out.append(q)
    if len(seen)==4: break
json.dump(out,open('l02v2_c_%s.json'%tag,'w'))
