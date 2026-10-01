import sys; sys.path.insert(0,'.')
from hill import *
rows='''################
####p##q##r######
####p##q##r######
####1##2##3######
####1##2##3######
'''
# kapılar 3 geniş: A 2-4, B 5-7, C 8-10, D 11-13; odalar iki kapının sınırında (4-5, 7-8, 10-11)
g=[list('#'*16) for _ in range(10)]
def put(r,c0,c1,ch):
    for c in range(c0,c1+1): g[r][c]=ch
for r in (6,7): put(r,2,4,'A'); put(r,5,7,'B'); put(r,8,10,'C'); put(r,11,13,'D')
for r in (4,5): put(r,4,5,'1'); put(r,7,8,'2'); put(r,10,11,'3')
for r in (2,3): put(r,4,5,'p'); put(r,7,8,'q'); put(r,10,11,'r')
put(8,2,13,'.'); g[9][7]='E'
rows=[''.join(x) for x in g]
if __name__=='__main__':
    B=Board(rows); print('\n'.join(rows)); print(B.names,B.n)
    best=hill(B,[4,3,3],iters=6000,seed=3,restarts=15); show(B,best,6)
