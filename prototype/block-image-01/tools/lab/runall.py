import sys; sys.path.insert(0,'.')
from hill import *
import templates as T
import itertools
def run(name,rows,sizes,exh=True,iters=8000):
    B=Board(rows); print('==',name,B.names,B.size); print('\n'.join(rows))
    if exh and B.n<=8:
        res=search(B,sizes=sizes); res.sort(key=score,reverse=True); print(len(res),'çözülebilir'); best=[(score(f),f) for f in res[:12]]
    else: best=hill(B,sizes,iters=iters,seed=7,restarts=20)
    show(B,best,6); return B,best
if __name__=='__main__':
    run('C1s',T.C1s,[2,2,1]); run('C1',T.C1,[3,2,2]); run('C3',T.C3,[3,2,2]); run('C4',T.C4,[2,2,2])
