import sys, pickle, collections, itertools; sys.path.insert(0,'.')
from hid2 import *
res = pickle.load(open('res2.pkl','rb'))
name='k5 iki bacak bölük'; B,names=board_for([1,1,3,1,1]); R=B.idx['c']
rows=[]
for m in res[name]:
    q=m['q']; pos=[(s,qq.index('c')) for s,qq in enumerate(q) if 'c' in qq][0]
    o=analyse_peek(B,q,1)
    # iki bacağın (a,b | d,e) kuyruk konumları
    def p(x): return [(s,qq.index(x)) for s,qq in enumerate(q) if x in qq][0]
    rows.append(dict(q=q,rpos=pos[1],rslot_len=len(q[pos[0]]),orders=m['orders'],df=m['df_orders'],fork=m['fork'],free=m['free'],p_df=m['p_df'],rd1=o['readable'],rdw1=o['readable_df_wrong'],gam1=o['gamble'],dfwrong=m['df_wrong']))
print('k5: toplam',len(rows))
for rp in (0,1,2):
    sub=[r for r in rows if r['rpos']==rp]
    print(' R kuyrukta %d. sırada: düzen %d | çatalsız %d | çatallı %d | (peek1) okunur çatallı %d | derin-önce yanılan %d | ort.kazanan sıra %.1f | derin-önce uyumlu pay %.0f%%' % (rp+1,len(sub),sum(1 for r in sub if r['fork']==0),sum(1 for r in sub if r['fork']>0),sum(1 for r in sub if r['rd1']>0),sum(1 for r in sub if r['dfwrong']>0),sum(r['orders'] for r in sub)/len(sub),100*sum(r['df'] for r in sub)/max(1,sum(r['orders'] for r in sub))))
ex=[r for r in rows if r['rdw1']>0][:3]
for r in ex: print('örnek (okunur+derin-önce yanlış):',[[ {'a':'A1','b':'A2','c':'R','d':'B2','e':'B1'}[x] for x in s] for s in r['q']],'orders',r['orders'],'df',r['df'],'çatal',r['fork'])
# çatalsız örnek
fr=[r for r in rows if r['fork']==0][:2]
for r in fr: print('örnek çatalsız:',[[ {'a':'A1','b':'A2','c':'R','d':'B2','e':'B1'}[x] for x in s] for s in r['q']],'orders',r['orders'],'df',r['df'])
