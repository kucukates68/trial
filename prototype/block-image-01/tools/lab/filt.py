import sys; sys.path.insert(0,'.')
from hill import *
import templates as T
def okf(f):
    if not f['solvable'] or f.get('start_safe')!=3: return False
    nz=sum(1 for v in f['start_closes'].values() if v)
    return nz>=2 and f['start_win_moves']>=2 and f['orders']>=8 and f['midsurv']>=2 and 0.3<=f['safe_win']<=0.7 and f['surv_max']<=5
def sc2(f):
    if not f['solvable']: return -99
    return score(f)+(30 if okf(f) else 0)
def go(name,rows,sizes,iters=12000,seeds=(1,2,3)):
    B=Board(rows); print('==',name,B.names,B.size); print('\n'.join(rows)); allb=[]
    for sd in seeds: allb+=hill(B,sizes,iters=iters,seed=sd,restarts=20,sc=sc2)
    allb.sort(key=lambda x:-x[0]); good=[(s,f) for s,f in allb if okf(f)]; print('süzgeçten geçen',len(good)); show(B,good if good else allb,6); return B,good
if __name__=='__main__':
    go('C2',T.C2,[4,3,3]); go('C3b',T.C3b,[3,3,3]); go('C3',T.C3,[3,2,2])
