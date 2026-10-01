import sys; sys.path.insert(0,'.')
from metr import *
LAB={'a':'A1','b':'A2','c':'Rsol','d':'Rsağ','e':'B2','f':'B1'}
B,names=board_for([1,1,2,1,1,1]); q=[['a'],['b','c'],['d','e','f']]
A=Analysis(B,q); R=sorted(A.reachable(),key=lambda p:sum(p))
print('halka sırası: A1 A2 Rsol Rsağ B2 B1 (giriş A1 ve B1 e bitişik); kuyruklar',[[LAB[x] for x in s] for s in q])
for p in R:
    win,cnt,mv,mask=A.memo[p]
    fil=[LAB[B.names[i]] for i in range(B.n) if mask>>i&1]
    s=' | '.join('%s:%s'%(LAB[B.names[m[1]]], 'SEAL' if m[2]=='seal' else ('kazanır' if m[3] else 'KAYBEDER(sonra)')) for m in mv)
    print('ptr',p,'dolu',fil or '-','|',s, '' if win else '  <ölü durum>')
print('orders',A.memo[A.start][1])
