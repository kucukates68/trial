import sys; sys.path.insert(0,'.')
from filt import *
if __name__=='__main__':
    go('T3',T.T3,[4,3,3],iters=14000); go('C4b',T.C4b,[3,3,2],iters=12000)
