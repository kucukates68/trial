import sys, json, collections; sys.path.insert(0,'.')
from l2 import *
import statistics
C=json.load(open(sys.argv[1]))
q=C[0]; print('QUEUE',q)
A=analyse(geo,q); ev=events(geo,A)
cells=[cells_of(m) for m in geo.pm]
# temas genişliği: yerleştirilen parçanın kapanan alana bitişik hücre sayısı
def contact(pname, victs):
    P=set(cells[geo.idx[pname]]); V=set()
    for v in victs: V|=set(cells[geo.idx[v]])
    return len({p for p in P if any((p[0]+dx,p[1]+dy) in V for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))})
tot=sum(e['w'] for e in ev); grp=collections.defaultdict(lambda:[0,0,0,0])
for e in ev:
    k=(e['p'],tuple(sorted(e['vict']))); g=grp[k]; g[0]+=e['w']; g[1]=e['size']; g[2]=contact(e['p'],e['vict']); g[3]=round(e['mean'],1)
print('toplam olay ağırlığı %.1f'%tot)
rows=sorted(grp.items(),key=lambda kv:-kv[1][0])
for (p,v),(w,size,ct,md) in rows[:16]: print('  %-10s → %-40s pay %2d%% | kapanan %3d hücre | temas %d hücre | ort.uzaklık %s'%(p,'+'.join(v),round(100*w/tot),size,ct,md))
pe=[(contact(e['p'],e['vict']),e['w']) for e in ev if e['nvict']>=2]; po=[(contact(e['p'],e['vict']),e['w']) for e in ev if e['nvict']<2]
f=lambda L: round(sum(c*w for c,w in L)/sum(w for c,w in L),1)
print('geçiş olayları (≥2 parça kapanır): pay %.0f%% | ortalama temas %s hücre'%(100*sum(w for c,w in pe)/tot,f(pe)),'| cep olayları (1 parça): pay %.0f%% | temas %s'%(100*sum(w for c,w in po)/tot,f(po)))
mf=mixfrac(A); print({'%d/%d'%a:round(100*b) for a,b in sorted(mf.items())})
print('p_random %.5f ps %.3f orders %.2e'%(A['root']['p'],A['root']['ps'],A['root']['cnt']))
# açılış eli
memo=A['memo']; st=A['start']; r=memo[st]; print('açılış eli',[geo.names[i] for i in r['hand']],[(geo.names[r['hand'][m[0]]],m[1],m[3]) for m in r['moves']])
