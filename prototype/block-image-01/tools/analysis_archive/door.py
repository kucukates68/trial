import sys, json, collections; sys.path.insert(0,'.')
from loc import *
lv,geo=load('l01'); C=json.load(open('l01_cands_all.json'))
# parça komşulukları
cells=[cells_of(m) for m in geo.pm]; own={}
for i,cs in enumerate(cells):
    for c in cs: own[c]=i
adj=[set() for _ in range(geo.n)]
for (x,y),i in own.items():
    for dx,dy in ((1,0),(0,1)):
        j=own.get((x+dx,y+dy))
        if j is not None and j!=i: adj[i].add(j); adj[j].add(i)
def door_stats(q):
    A=analyse(geo,q); memo=A['memo']; N=sum(len(x) for x in A['ids']); layer={A['start']:1.0}; res=collections.Counter(); tot=0
    for k in range(N):
        nxt=collections.defaultdict(float)
        for st,w in layer.items():
            r=memo[st]; S=r['S']; F=geo.fmask(S); safe=[m for m in r['moves'] if m[1]=='safe' and m[3]]
            for m in r['moves']:
                if m[1]!='trap': continue
                i=r['hand'][m[0]]; F2=F|geo.pm[i]; R2=geo.flood(F2); sealed=(geo.targets&~F2)&~R2
                V={j for j in range(geo.n) if geo.pm[j]&sealed}
                Nb=set().union(*[adj[v] for v in V])-V
                U={j for j in Nb if not (S>>j&1)}      # yerleşmemiş (soluk) komşular (kart dahil)
                tot+=w
                if U=={i}: res['tek_acik_yan']+=w
                elif U-{i}<= set(): res['x']+=w
                else: res['baska_soluk_komsu_var']+=w
                # çevrelenme: kurbanın tüm komşuları dolu olacak mı
                if not (U-{i}): res['cevrili']+=w
            for m in safe: nxt[m[2]]+=w/len(safe)
        layer=dict(nxt)
    return {k:round(100*v/tot) for k,v in res.items()}
for n,q in C.items(): print(n,door_stats(q))
