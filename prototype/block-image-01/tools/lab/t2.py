import sys; sys.path.insert(0,'.')
from search import *
def run(rows,sizes,top=6,name=''):
    rows=[r.ljust(max(map(len,rows)),'#') for r in rows]
    B=Board(rows); print(name,B.names,B.size)
    res=search(B,sizes=sizes); print(len(res),'çözülebilir kuyruk')
    res.sort(key=score,reverse=True)
    for f in res[:top]: print(score(f),f['queues'],'orders',f['orders'],'closes',f['start_closes'],'win0',f['start_win_moves'],'infl',f['infl'],'fork',f['fork'],'lag',f['lagmin'],'st',f['states'])
    return B,res
if __name__=='__main__':
    rows='''#############
####11#22#####
####11#22#####
##AAABBBCCC###
##AAABBBCCC###
##.........###
######E######'''.split()
    run(rows,[2,2,1],name='T1b')
