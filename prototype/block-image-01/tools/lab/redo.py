import sys; sys.path.insert(0,'.')
from filt import *
for name,rows,sizes in [('T3',T.T3,[4,3,3]),('C2',T.C2,[4,3,3]),('C4b',T.C4b,[3,3,2]),('C3',T.C3,[3,2,2])]:
    B,good=go(name,rows,sizes,iters=10000,seeds=(1,2,3))
