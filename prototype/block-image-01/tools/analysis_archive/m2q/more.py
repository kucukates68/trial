import sys, pickle, collections, statistics; sys.path.insert(0,'.')
from metr import *
base=pickle.load(open('res.pkl','rb'))
for name in ['k4 sol bacak bölük','k5 iki bacak bölük','k6','k7 hepsi tek']:
    rows=[m for m in base[name] if m['start_safe']==3]
    lags=collections.Counter(); 
    for m in rows: lags.update(m['lag'])
    st=statistics.mean(m['states'] for m in rows); fk=statistics.mean(m['fork'] for m in rows); fr=statistics.mean(m['free'] for m in rows); fo=statistics.mean(m['forced'] for m in rows); de=statistics.mean(m['dead'] for m in rows)
    uniq=sum(1 for m in rows if m['orders']==1)
    print(name,'ort. erişilebilir durum %.1f: zorunlu %.1f serbest %.1f çatal %.1f ölü %.1f'%(st,fo,fr,fk,de),'| çatal sonrası kayıp-gecikmesi (güvenle oynanabilen hamle) dağılımı',dict(sorted(lags.items())),'| tek kazanan sıralı düzen',uniq,'/',len(rows))
# gatekeeper: her parça için (F güvenli, F+P güvenli değil) → kurbanlar (tüm maskeler)
def gate(part,labels):
    B,names=board_for(part); out={}
    for i,nm in enumerate(B.names):
        vict=collections.Counter(); n=0
        for mask in range(1<<B.n):
            if mask>>i&1: continue
            if mask and B.safe_state(mask) if hasattr(B,'safe_state') else False: pass
            # F güvenli mi: F'nin kendisi için her boş hedef erişilebilir mi
            R=B.reach(mask); okF=all((mask>>o&1) or p in R for p,o in B.owner.items())
            if not okF: continue
            m2=mask|1<<i; R2=B.reach(m2)
            if m2==B.full: continue
            cut={o for p,o in B.owner.items() if not (m2>>o&1) and p not in R2}
            if cut: n+=1; vict.update(labels[B.names[c]] for c in cut)
        out[labels[nm]]=(n,dict(vict))
    return out
print('KEMER kapı bekçiliği:',gate([2,3,2],{'a':'A','b':'R','c':'B'}))
print('k5:',gate([1,1,3,1,1],{'a':'A1','b':'A2','c':'R','d':'B2','e':'B1'}))
