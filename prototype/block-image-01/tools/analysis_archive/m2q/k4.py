import sys, pickle; sys.path.insert(0,'.')
from metr import *
B,names=board_for([1,1,3,2]); print(B.rows)
lab={'a':'AlA(ayak,1)','b':'AÜst(1)','c':'R(çatı,3)','d':'B(sağ bacak,2)'}
res=pickle.load(open('res.pkl','rb'))['k4 sol bacak bölük']
for m in sorted(res,key=lambda m:(m['fork'],m['p_df'])):
    print([[lab[x].split('(')[0] for x in s] for s in m['q']],'orders',m['orders'],'DF-uyumlu',m['df_orders'],'p_df',round(m['p_df'],2),'çatal',m['fork'],'serbest',m['free'],'zorunlu',m['forced'],'ölü',m['dead'],'df_yanılan',m['df_wrong'],'lag',m['lag'])
