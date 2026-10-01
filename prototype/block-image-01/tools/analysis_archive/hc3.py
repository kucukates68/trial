import sys, random, time, json, collections; sys.path.insert(0,'.')
import hc
from hc import *
TARGET={(3,3):0.30,(3,2):0.35,(3,1):0.20}   # 3 kartlı hamlelerin payı (toplam 85%; kalan 15% 1-2 kartlı sonlar)
def mixfrac(A):
    w=run(A,'win'); T=collections.Counter(); W=0
    for k,t,e in w:
        for kk,v in e.items():
            if isinstance(kk,tuple): T[(kk[1],kk[2])]+=v
        W+=e['w']
    return {k:v/W for k,v in T.items()}
def dist(m): return sum(abs(m.get(k,0)-v) for k,v in TARGET.items())
def climb_m(key, iters, seed=5, ps_min=0.9):
    hc.PS_MIN=ps_min
    lv,geo=load(key); q0=[list(q) for q in lv['hand']]; rnd=random.Random(seed); lens=[len(q) for q in q0]
    flat=[x for s in q0 for x in s]
    def unflat(f):
        out=[];i=0
        for L in lens: out.append(f[i:i+L]); i+=L
        return out
    r0=evalJ(geo,q0); A0=r0[1]; f=flat; fd=dist(mixfrac(A0)); best=(fd,q0,A0,r0[0])
    for it in range(iters):
        g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
        if rnd.random()<0.3: k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
        res=evalJ(geo,unflat(g))
        if res is None: continue
        d=dist(mixfrac(res[1]))
        if d<=fd: f,fd=g,d
        if d<best[0]: best=(d,unflat(g),res[1],res[0])
    return lv,q0,r0,best
if __name__=='__main__':
    key=sys.argv[1]; iters=int(sys.argv[2]); t0=time.time(); lv,q0,r0,best=climb_m(key,iters); d,qb,Ab,Jb=best
    print(key,'süre %.0fs'%(time.time()-t0),'| yanlış olasılığı/hamle %.1f%% → %.1f%%'%(100*r0[0],100*Jb),'| p_random %.5f → %.5f'%(r0[1]['root']['p'],Ab['root']['p']),'| önizleme bakan oyuncunun kazanması %.3f → %.3f'%(r0[1]['root']['ps'],Ab['root']['ps']))
    print('   hamle türleri % önce',mix(r0[1]),'| sonra',mix(Ab))
    moved=sum(1 for a,b in zip([x for s in q0 for x in s],[x for s in qb for x in s]) if a!=b); print('   yeri değişen parça',moved,'/',len(lv['pieces']))
    json.dump(dict(q=qb),open('%s_mix.json'%key,'w'))
