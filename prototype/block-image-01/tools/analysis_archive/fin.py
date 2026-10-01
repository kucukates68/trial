import sys, json, collections; sys.path.insert(0,'.')
from l2 import *
from hc3 import mixfrac
q=json.load(open('l02v2_c_A.json'))[0]
A=analyse(geo,q); ev=events(geo,A); s=evsum(ev); mf=mixfrac(A)
res,A2=evalq(q)
cells=[cells_of(m) for m in geo.pm]; own={}
for i,cs in enumerate(cells):
    for c in cs: own[c]=i
adj=[set() for _ in range(geo.n)]
for (x,y),i in own.items():
    for dx,dy in ((1,0),(0,1)):
        j=own.get((x+dx,y+dy))
        if j is not None and j!=i: adj[i].add(j); adj[j].add(i)
def contact(pname,victs):
    P=set(cells[geo.idx[pname]]); V=set()
    for v in victs: V|=set(cells[geo.idx[v]])
    return len({p for p in P if any((p[0]+dx,p[1]+dy) in V for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))})
# kapı testi: kapanan bölgenin tek soluk komşusu yerleştirilen kart mı
memo=A['memo']; N=sum(len(x) for x in A['ids']); layer={A['start']:1.0}; door=0; tot=0; narrow=0; narrow_ev=[]; allc=[]
for k in range(N):
    nxt=collections.defaultdict(float)
    for st,w in layer.items():
        r=memo[st]; S=r['S']; F=geo.fmask(S); safe=[m for m in r['moves'] if m[1]=='safe' and m[3]]
        for m in r['moves']:
            if m[1]!='trap': continue
            i=r['hand'][m[0]]; F2=F|geo.pm[i]; R2=geo.flood(F2); sealed=(geo.targets&~F2)&~R2
            V={j for j in range(geo.n) if geo.pm[j]&sealed}; Nb=set().union(*[adj[v] for v in V])-V; U={j for j in Nb if not (S>>j&1)}
            tot+=w; door+= w if U=={i} else 0
            ct=contact(geo.names[i],[geo.names[v] for v in V]); allc.append((ct,w))
            if ct<=4: narrow+=w
        for m in safe: nxt[m[2]]+=w/len(safe)
    layer=dict(nxt)
f=lambda L: sum(c*w for c,w in L)/sum(w for c,w in L)
def wmed(L):
    L=sorted(L); t=sum(w for c,w in L); a=0
    for c,w in L:
        a+=w
        if a>=t/2: return c
print('olay özeti',s)
print('yanlış/hamle (rastgele oyuncu) %.1f%%'%(100*res),'| p_random %.2e'%A['root']['p'],'| ps %.3f'%A['root']['ps'],'| orders %.2e'%A['root']['cnt'])
print('mix',{'%d/%d'%a:round(100*b) for a,b in sorted(mf.items())})
print('tek açık yan (kapanan bölgenin tek soluk komşusu kart) %.0f%%'%(100*door/tot),'| dar geçit olayları (temas ≤4 hücre) %.0f%%'%(100*narrow/tot),'| temas ort %.1f med %s'%(f(allc),wmed(allc)))
