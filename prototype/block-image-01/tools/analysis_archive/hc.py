import sys, random, time, json, collections; sys.path.insert(0,'.')
from an2 import *
PS_MIN=0.9
def evalJ(geo, queues):
    A=analyse(geo,queues)
    if not A['root']['win']: return None
    if A['root']['ps']<PS_MIN: return None
    r=run(A,'rand'); J=sum(e['hz'] for k,t,e in r)/sum(t for k,t,e in r)
    return J,A
def mix(A):
    w=run(A,'win'); T=collections.Counter(); W=0
    for k,t,e in w:
        for kk,v in e.items():
            if isinstance(kk,tuple): T[(kk[1],kk[2])]+=v
        W+=e['w']
    return {k:round(100*v/W) for k,v in sorted(T.items())}
def climb(key, iters, seed=1):
    lv,geo=load(key); q0=[list(q) for q in lv['hand']]; names=[p['id'] for p in lv['pieces']]
    rnd=random.Random(seed); J0,A0=evalJ(geo,q0); best=(J0,q0,A0); cur=(J0,q0)
    lens=[len(q) for q in q0]; flat=lambda q:[x for s in q for x in s]
    def unflat(f):
        out=[];i=0
        for L in lens: out.append(f[i:i+L]); i+=L
        return out
    t0=time.time(); f=flat(q0); fj=J0; acc=0
    for it in range(iters):
        g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
        if rnd.random()<0.3:   # kısa kaydırma
            k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
        res=evalJ(geo,unflat(g))
        if res is None: continue
        Jg,Ag=res
        if Jg>=fj: f,fj=g,Jg; acc+=1; 
        if Jg>best[0]: best=(Jg,unflat(g),Ag)
    return lv,geo,q0,J0,A0,best,time.time()-t0
if __name__=='__main__':
    key=sys.argv[1]; iters=int(sys.argv[2]); globals().__setitem__('PS_MIN',float(sys.argv[3]) if len(sys.argv)>3 else 0.9)
    lv,geo,q0,J0,A0,best,dt=climb(key,iters)
    Jb,qb,Ab=best
    moved=sum(1 for a,b in zip([x for s in q0 for x in s],[x for s in qb for x in s]) if a!=b)
    print(key,'süre %.0fs'%dt,'| hamle başı yanlış olasılığı (rastgele oyuncu): %.1f%% → %.1f%%'%(100*J0,100*Jb),'| p_random %.4f → %.4f'%(A0['root']['p'],Ab['root']['p']),'| yalnız anında kilitleneni eleyen oyuncunun kazanma oranı %.3f → %.3f'%(A0['root']['ps'],Ab['root']['ps']),'| yeri değişen parça',moved,'/',len(geo.names))
    print('   hamle türleri (kart/güvenli, %) önce',mix(A0)); print('   sonra',mix(Ab))
    json.dump(dict(q=qb,J=Jb),open(key+'_best.json','w'))
