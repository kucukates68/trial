import sys, pickle, collections, statistics; sys.path.insert(0,'.')
from metr import *
base=pickle.load(open('res.pkl','rb')); rows=base['k5 iki bacak bölük']
c=collections.defaultdict(list)
for m in rows:
    heads={s[0] for s in m['q']}; legs=len(heads & {'a','e'}); rh='c' in heads
    c[(legs,rh)].append(m)
print('k5 (ring A1 A2 R B2 B1): başlangıçta girişe bitişik iki parça (A1,B1) kaç tanesi el başında × R el başında mı')
for k in sorted(c):
    v=c[k]; print(' A1/B1 elde: %d, R elde: %-5s | düzen %2d | çatallı %2d | tek-sıralı %2d | ort.sıra %.1f' % (k[0],k[1],len(v),sum(1 for m in v if m['fork']>0),sum(1 for m in v if m['orders']==1),statistics.mean(m['orders'] for m in v)))
rows=base['k6']
c=collections.defaultdict(list)
for m in rows:
    heads={s[0] for s in m['q']}; legs=len(heads & {'a','f'}); c[legs].append(m)
print('k6: A1/B1 elde kaç tane')
for k in sorted(c):
    v=c[k]; print(' ',k,'| düzen',len(v),'| çatallı %.0f%%'%(100*sum(1 for m in v if m['fork']>0)/len(v)),'| tek-sıralı %.0f%%'%(100*sum(1 for m in v if m['orders']==1)/len(v)),'| ort.sıra %.1f'%statistics.mean(m['orders'] for m in v))
