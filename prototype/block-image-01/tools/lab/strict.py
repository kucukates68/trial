import sys; sys.path.insert(0,'.')
from filt import *
def strict(f):
    if not f['solvable'] or f.get('start_safe')!=3: return -99
    nz=sum(1 for v in f['start_closes'].values() if v)
    s=40*nz+15*min(f['start_win_moves'],2)+min(f['orders'],30)/3+8*min(f['midsurv'],3)+10*max(0,1-abs(f['safe_win']-0.5)*2)-3*max(0,f['surv_max']-4)
    return s
for name,rows,sizes in [('C4b',T.C4b,[3,3,2]),('C3',T.C3,[3,2,2]),('C3b',T.C3b,[3,3,3]),('C2',T.C2,[4,3,3])]:
    B=Board(rows); allb=[]
    for sd in (1,2,3,4): allb+=hill(B,sizes,iters=10000,seed=sd,restarts=20,sc=strict)
    allb.sort(key=lambda x:-x[0]); print('==',name); show(B,allb,3)
