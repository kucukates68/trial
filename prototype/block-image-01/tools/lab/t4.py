import sys; sys.path.insert(0,'.')
from hill import *
g=[list('#'*15) for _ in range(11)]
def put(r,c0,c1,ch):
    for c in range(c0,c1+1): g[r][c]=ch
for r in (6,7): put(r,3,5,'A'); put(r,6,8,'B'); put(r,9,11,'C')
for r in (4,5): put(r,5,6,'1'); put(r,8,9,'2')
for r in (2,3): put(r,5,6,'p'); put(r,8,9,'q')
for r in range(1,8): g[r][2]='l'; g[r][12]='r'
put(0,2,12,'u')
put(8,3,11,'.'); g[9][7]='E'
rows=[''.join(x) for x in g]
if __name__=='__main__':
    B=Board(rows); print('\n'.join(rows)); print(B.names,B.n)
    best=hill(B,[4,3,3],iters=9000,seed=5,restarts=20); show(B,best,8)
