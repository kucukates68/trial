import sys, random, collections, statistics; sys.path.insert(0,'.')
from an import *
for key in ['l01','l02','l03','l04','l05']:
    lv,geo=load(key); n=geo.n; rnd=random.Random(7); ever=set(); fr=[[],[],[]]; tot=[]
    for run_ in range(300):
        S=0; order=0
        while S!=geo.full:
            rem=[i for i in range(n) if not S>>i&1]
            kinds={i:geo.head(S,i) for i in rem}
            tr=[i for i in rem if kinds[i]=='trap']; ever.update(tr)
            f=len(tr)/len(rem); tot.append(f); fr[min(2,3*order//n)].append(f)
            safe=[i for i in rem if kinds[i] in('safe','won')]
            if not safe: break
            S|=1<<rnd.choice(safe); order+=1
    print(key,'parça',n,'| bir kez bile tuzak (ağızlık) olabilen parça %d (%.0f%%)'%(len(ever),100*len(ever)/n),'| rastgele güvenli sıralarda kalan parçaların tuzak payı: ort %.1f%% (açılış %.1f%% orta %.1f%% son %.1f%%)'%(100*statistics.mean(tot),100*statistics.mean(fr[0]),100*statistics.mean(fr[1]),100*statistics.mean(fr[2])))
