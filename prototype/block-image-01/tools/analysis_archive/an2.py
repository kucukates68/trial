import sys, collections, statistics; sys.path.insert(0,'.')
from an import *
def run(A, policy):
    memo=A['memo']; N=sum(len(q) for q in A['ids']); layer={A['start']:1.0}; rows=[]
    for k in range(N):
        tot=sum(layer.values()); 
        if tot==0: break
        e=collections.Counter(); nxt=collections.defaultdict(float)
        for st,w in layer.items():
            mv=memo[st]['moves']; cards=len(mv); safe=[m for m in mv if m[1]=='safe' and m[3]]; now=[m for m in mv if m[1]!='safe']; later=[m for m in mv if m[1]=='safe' and not m[3]]
            e['w']+=w; e['cards']+=w*cards; e['safe']+=w*len(safe); e['now']+=w*len(now); e['later']+=w*len(later)
            e[('t',cards,len(safe))]+=w
            if policy=='win':
                for m in safe: nxt[m[2]]+=w/len(safe)
                e['hz']+=0
            elif policy=='rand':
                e['hz']+=w*(1-len(safe)/cards)
                for m in safe: nxt[m[2]]+=w/cards
            elif policy=='careful':
                ns=[m for m in mv if m[1]=='safe']
                e['hz']+=w*(len(later)/len(ns)) if ns else w
                for m in safe: nxt[m[2]]+=w/len(ns)
        rows.append((k,tot,e)); layer=dict(nxt)
    return rows
def summarize(rows, N):
    # üçte bir fazlar
    out={}
    for name,(a,b) in {'açılış':(0,N//3),'orta':(N//3,2*N//3),'son':(2*N//3,N)}.items():
        w=cards=safe=now=later=0; hz=0; tot=0
        for k,t,e in rows:
            if a<=k<b: w+=e['w']; cards+=e['cards']; safe+=e['safe']; now+=e['now']; later+=e['later']; hz+=e['hz']; tot+=t
        out[name]=dict(cards=cards/w,safe=safe/w,now=now/w,later=later/w,hz=hz/tot)
    return out
if __name__=='__main__':
    for key in ['l01','l02','l03','l04','l05']:
        lv,geo=load(key); A=analyse(geo,lv['hand']); N=sum(len(q) for q in A['ids'])
        w=run(A,'win'); r=run(A,'rand'); c=run(A,'careful')
        # tür dağılımı (kazananlarla)
        T=collections.Counter(); W=0
        for k,t,e in w:
            for kk,v in e.items():
                if isinstance(kk,tuple): T[(kk[1],kk[2])]+=v
            W+=e['w']
        print('==',key,'hamle',N,'| p_random %.4f (rastgele seçerek bitirme olasılığı)'%A['root']['p'],'| yalnız anında kilitleneni eleyen oyuncu %.4f'%A['root']['ps'])
        print('  kazanan-yol durumlarında hamle türleri (kart sayısı/güvenli): '+', '.join('%d/%d: %.0f%%'%(c_,s_,100*v/W) for (c_,s_),v in sorted(T.items())))
        sw=summarize(w,N); print('  kazanan yol (ortalama): ',{k:{a:round(b,2) for a,b in v.items() if a!='hz'} for k,v in sw.items()})
        sr=summarize(r,N); print('  rastgele oyuncu: hamle başına yanlış seçme olasılığı (hayattayken): açılış %.1f%% orta %.1f%% son %.1f%% | genel ort. %.1f%%'%(100*sr['açılış']['hz'],100*sr['orta']['hz'],100*sr['son']['hz'],100*sum(e['hz'] for k,t,e in r)/sum(t for k,t,e in r)))
        sc=summarize(c,N); print('  önizlemede kilitleneni elemeyen değil, eleyen oyuncu: hamle başına GECİKMELİ yanlış olasılığı: açılış %.2f%% orta %.2f%% son %.2f%%'%(100*sc['açılış']['hz'],100*sc['orta']['hz'],100*sc['son']['hz']))
