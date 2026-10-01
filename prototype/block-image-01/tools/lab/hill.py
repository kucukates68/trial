import sys, random; sys.path.insert(0,'.')
from search import *
def evalq(B,q):
    A=Analysis(B,q); f=A.features(); f['queues']=q; return f
def hill(B,sizes,iters=4000,seed=0,restarts=12,sc=None):
    sc=sc or score; rnd=random.Random(seed); names=B.names; best=[]
    for r in range(restarts):
        pm=names[:]; rnd.shuffle(pm)
        def mk(pm): return [pm[:sizes[0]],pm[sizes[0]:sizes[0]+sizes[1]],pm[sizes[0]+sizes[1]:]]
        f=evalq(B,mk(pm)); s=sc(f) if f['solvable'] else -99
        for it in range(iters//restarts):
            p2=pm[:]; i,j=rnd.sample(range(len(p2)),2); p2[i],p2[j]=p2[j],p2[i]
            f2=evalq(B,mk(p2)); s2=sc(f2) if f2['solvable'] else -99
            if s2>=s: pm,f,s=p2,f2,s2
        best.append((s,f))
    best.sort(key=lambda x:-x[0]); return best
def show(B,best,k=5):
    seen=set()
    for s,f in best:
        key=tuple(sorted(tuple(x) for x in f['queues']))
        if key in seen: continue
        seen.add(key); print(s,f['queues'],'orders',f['orders'],'closes',f['start_closes'],'win0',f['start_win_moves'],'infl',f['infl'],'fork',f['fork'],'lag',f['lagmin'],'surv',f['surv_max'],f['midsurv'],'sw',round(f['safe_win'],2),'st',f['states'])
        k-=1
        if k==0: break
