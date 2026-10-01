import sys, random, time, json, collections; sys.path.insert(0,'.')
import hc
from hc import *
def climb_t(key, T, iters, seed=3, ps_min=0.9):
    hc.PS_MIN=ps_min
    lv,geo=load(key); q0=[list(q) for q in lv['hand']]; rnd=random.Random(seed); lens=[len(q) for q in q0]
    flat=[x for s in q0 for x in s]
    def unflat(f):
        out=[];i=0
        for L in lens: out.append(f[i:i+L]); i+=L
        return out
    r0=evalJ(geo,q0); f=flat; fj=-abs(r0[0]-T); best=(fj,q0,r0[1],r0[0]); 
    for it in range(iters):
        g=f[:]; i,j=rnd.sample(range(len(g)),2); g[i],g[j]=g[j],g[i]
        if rnd.random()<0.3: k=rnd.randrange(len(g)); x=g.pop(k); g.insert(rnd.randrange(len(g)+1),x)
        res=evalJ(geo,unflat(g))
        if res is None: continue
        sc=-abs(res[0]-T)
        if sc>=fj: f,fj=g,sc
        if sc>best[0]: best=(sc,unflat(g),res[1],res[0])
    return lv,q0,r0,best
if __name__=='__main__':
    key=sys.argv[1]; T=float(sys.argv[2]); iters=int(sys.argv[3])
    t0=time.time(); lv,q0,r0,best=climb_t(key,T,iters)
    sc,qb,Ab,Jb=best
    print(key,'hedef %.0f%%'%(100*T),'süre %.0fs'%(time.time()-t0),'| hamle başı yanlış olasılığı %.1f%% → %.1f%%'%(100*r0[0],100*Jb),'| p_random %.4f → %.4f'%(r0[1]['root']['p'],Ab['root']['p']),'| önizleme bakan oyuncu (anında kilitleneni eleyen) kazanma %.3f → %.3f'%(r0[1]['root']['ps'],Ab['root']['ps']))
    print('   hamle türleri önce',mix(r0[1]),'sonra',mix(Ab))
    json.dump(dict(q=qb,J=Jb),open('%s_T%d.json'%(key,int(100*T)),'w'))
