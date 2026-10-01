import sys; sys.path.insert(0,'.')
from search import *
rows='''##############
##3333333333###
##3111222333###
##3111222333###
##AAABBBCCC####
##AAABBBCCC####
##.........####
######E#######'''.split()
rows=[r.ljust(14,'#') for r in rows]
B=Board(rows); print(B.names,B.size)
res=search(B,sizes=[2,2,2]); print(len(res),'çözülebilir kuyruk')
res.sort(key=score,reverse=True)
for f in res[:8]: print(score(f),f['queues'],'orders',f['orders'],'closes',f['start_closes'],'winmoves',f['start_win_moves'],'infl',f['infl'],'fork',f['fork'],'lag',f['lagmin'],'states',f['states'])
