import sys, json, collections; sys.path.insert(0,'.'); sys.path.insert(0,'/home/user/trial/prototype/block-image-01/tools')
from loc import *
from hc3 import mixfrac
from hc import evalJ
import hc; hc.PS_MIN=0.0
from ref import Level
lv,geo=load('l01')
C={ 'mevcut L01':lv['hand'], 'önceki mix (R1)':json.load(open('l01_mix.json'))['q'], 'A':json.load(open('l01_cands.json'))[0]['q'], 'B':json.load(open('l01_T22.json'))[0],
 'C':[['PAW_R','FLANK_R','EAR_L','NOSE_MOUTH','EARIN_R','EYE_L','PAW_L'],['MUZZLE','EARIN_L','FACE_L','JAW','CHEST','BELLY'],['EAR_R','HAUNCH','TAIL','FOREHEAD','EYE_R','FACE_R']]}
json.dump(C,open('l01_cands_all.json','w'))
for name,q in C.items():
    J,A=evalJ(geo,q); mf=mixfrac(A); ev=events(geo,A); s=evsum(ev)
    L=Level(lv['grid'],[dict(id=p['id'],cells=p['cells']) for p in lv['pieces']],q); st=L.stats()
    three={k:round(100*v) for k,v in mf.items() if k[0]==3}
    ge=lambda k: round(100*mf.get(k,0))
    print('%-16s yanlış/hamle %4.1f%% | 3/3 %2d%% 3/2 %2d%% 3/1 %2d%% 2/2 %2d%% 2/1 %2d%% 1/1 %2d%% | gecikmeli tuzak %d anında %d | kazanan sıra %.1e | olay boyutu ort %s hücre | en yakın uzaklık ort/med %s/%s | kapanan alan ort/med uzaklık %s/%s | kurbanı komşu %s%%'%(name,100*J,ge((3,3)),ge((3,2)),ge((3,1)),ge((2,2)),ge((2,1)),ge((1,1)),st['trap_delayed'],st['trap_instant'],st['winning_orders'],s['boyut_ort'],s['yakin_ort'],s['yakin_med'],s['ort_ort'],s['ort_med'],round(100*s['komsu_pay'])))
    if name in('B',):
        c=collections.Counter()
        for e in ev: c[(e['p'],tuple(e['vict']))]+=e['w']
        tot=sum(c.values()); print('   B yanlış olayları (kart → kapanan parçalar, payı):',[(k[0],'+'.join(k[1]),round(100*v/tot)) for k,v in c.most_common(10)])
