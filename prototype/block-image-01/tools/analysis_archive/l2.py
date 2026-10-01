import sys, json, random, time, collections; sys.path.insert(0,'.'); sys.path.insert(0,'/home/user/trial/prototype/block-image-01/tools')
import importlib.util, os
os.chdir('/home/user/trial/prototype/block-image-01/tools')
import author_l02v2 as m
os.chdir('/tmp/claude-0/-home-user-trial/309a846e-36ea-5c76-a60b-b8e84c53c4f6/scratchpad/wr')
from lvlkit import Geo, analyse, valid_order
from loc import events, evsum, cells_of
from an2 import run
from hc3 import mixfrac
import hc
cv=m.cv; names=[n for n in cv.order if n in cv.pieces()]; geo=Geo(cv,names)
TARGET={(3,3):0.20,(3,2):0.35,(3,1):0.25}
def dist(mx): return sum(abs(mx.get(k,0)-v) for k,v in TARGET.items())
def evalq(q, ps_min=0.999):
    A=analyse(geo,q)
    if not A['root']['win'] or A['root']['ps']<ps_min: return None
    r=run(A,'rand'); J=sum(e['hz'] for k,t,e in r)/sum(t for k,t,e in r)
    return J,A
if __name__=='__main__':
    order=valid_order(cv,geo); print('geçerli sıra',len(order),order)
    # başlangıç kuyruğu: sıradan 3 slota dağıt (dönüşümlü bloklar)
    n=len(order); lens=[n//3+(1 if i<n%3 else 0) for i in range(3)]
    q=[[],[],[]]; i=0
    for k in range(n): q[k%3].append(order[k])
    print([len(x) for x in q]); res=evalq(q); print('başlangıç', None if res is None else (round(res[0],3),res[1]['root']['ps'],res[1]['root']['p']))
