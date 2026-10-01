import sys, json, collections, statistics, math; sys.path.insert(0,'.')
from an2 import *
import lvlkit
W=lvlkit.W
def cells_of(mask):
    out=[]; b=0
    while mask:
        low=mask & -mask; i=low.bit_length()-1; out.append((i%W,i//W)); mask^=low
    return out
def wmedian(vals):   # (değer, ağırlık)
    vs=sorted(vals); tot=sum(w for v,w in vs); acc=0
    for v,w in vs:
        acc+=w
        if acc>=tot/2: return v
def events(geo, A):
    memo=A['memo']; N=sum(len(q) for q in A['ids']); layer={A['start']:1.0}; ev=[]
    adjp={}
    for k in range(N):
        nxt=collections.defaultdict(float)
        for st,w in layer.items():
            r=memo[st]; S=r['S']; F=geo.fmask(S)
            safe=[m for m in r['moves'] if m[1]=='safe' and m[3]]
            for m in r['moves']:
                if m[1]=='trap':
                    i=r['hand'][m[0]]; F2=F|geo.pm[i]; R2=geo.flood(F2); sealed=(geo.targets & ~F2) & ~R2
                    P=cells_of(geo.pm[i]); Sc=cells_of(sealed)
                    d=[min(abs(x-a)+abs(y-b) for a,b in P) for x,y in Sc]
                    # kapanan parçalar
                    vict=[j for j in range(geo.n) if geo.pm[j] & sealed]
                    # komşuluk: kurban parça P'ye kenar komşu mu
                    def touch(j):
                        pj=cells_of(geo.pm[j]); return any(abs(x-a)+abs(y-b)==1 for x,y in pj for a,b in P)
                    ev.append(dict(w=w,p=geo.names[i],size=len(Sc),near=min(d),mean=sum(d)/len(d),far=max(d),nvict=len(vict),adj=any(touch(j) for j in vict),vict=[geo.names[j] for j in vict]))
            for m in safe: nxt[m[2]]+=w/len(safe)
        layer=dict(nxt)
    return ev
def evsum(ev):
    W_=sum(e['w'] for e in ev)
    if not ev: return {}
    f=lambda key: sum(e['w']*e[key] for e in ev)/W_
    return dict(olay=round(W_,2),boyut_ort=round(f('size')),yakin_ort=round(f('near'),1),yakin_med=wmedian([(e['near'],e['w']) for e in ev]),ort_ort=round(f('mean'),1),ort_med=round(wmedian([(e['mean'],e['w']) for e in ev]),1),uzak_ort=round(f('far'),1),komsu_pay=round(sum(e['w'] for e in ev if e['adj'])/W_,2),kurban_say=round(f('nvict'),1))
if __name__=='__main__':
    lv,geo=load('l01')
    for name,q in [('mevcut',lv['hand']),('mix',json.load(open('l01_mix.json'))['q']),('T25',json.load(open('l01_T25.json'))['q'])]:
        A=analyse(geo,q); ev=events(geo,A); print(name,'ps',round(A['root']['ps'],3),evsum(ev))
        if name=='mevcut':
            c=collections.Counter(); 
            for e in ev: c[(e['p'],tuple(e['vict']))]+=e['w']
            print('   olaylar',[(k,round(v,2)) for k,v in c.most_common(8)])
