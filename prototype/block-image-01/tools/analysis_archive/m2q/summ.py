import sys, pickle, collections, itertools, random, statistics; sys.path.insert(0,'.')
from hid2 import *
res = pickle.load(open('res2.pkl','rb')); base = pickle.load(open('res.pkl','rb'))
PART = {'k3 Kemer':[2,3,2],'k4 sol bacak bölük':[1,1,3,2],'k5 iki bacak bölük':[1,1,3,1,1],'k6':[1,1,2,1,1,1],'k7 hepsi tek':[1,1,1,1,1,1,1]}
def extra(B, q):
    A = Analysis(B, q); R = A.reachable(); conflict = commute = 0; succ = []; win0 = 0
    root = A.memo[A.start]
    for m in root[2]:
        if m[2] != 'seal' and m[5] is not None:
            succ.append(sum(1 for x in A.memo[m[5]][2] if x[2] != 'seal'))
    for p in R:
        win, cnt, mv, mask = A.memo[p]
        if not win: continue
        safes = [m for m in mv if m[2] != 'seal']
        for x, y in itertools.combinations(safes, 2):
            m2 = mask | 1 << x[1] | 1 << y[1]
            joint = B.safe(mask | 1 << x[1], y[1])
            if joint == 'seal': conflict += 1
            else: commute += 1
    return dict(conflict=conflict, commute=commute, succ=succ, win0=root[2] and sum(1 for m in root[2] if m[3]))
print('%-20s %6s %6s | %8s %8s %8s | %7s %7s | %8s | %8s %8s' % ('','düzen','çözül','başta3güv','ilk-hamle kazandıran(1/2/3)','', 'çatal%','çatalsız%','DF pay%','çatışma','komüt'))
for name, part in PART.items():
    B, names = board_for(part); rows = res.get(name) or base[name]
    ok = [m for m in rows if m['start_safe'] == 3]
    w0 = collections.Counter(); conf = comm = 0; succs = []
    for m in ok:
        e = extra(B, m['q']); w0[e['win0']] += 1; conf += e['conflict']; comm += e['commute']; succs += e['succ']
    forkp = 100 * sum(1 for m in ok if m['fork'] > 0) / len(ok); freep = 100 - forkp
    dfp = 100 * sum(m['df_orders'] for m in ok) / sum(m['orders'] for m in ok)
    orders = [m['orders'] for m in ok]
    print('%-20s %6d %6d | w0 %s | çatallı %.0f%% çatalsız %.0f%% | derin-önce uyumlu sıra %.0f%% | çatışan çift %d vs birlikte güvenli çift %d | ilk hamle sonrası ort. güvenli kart %.2f | orders med %s min %d max %d' % (name, len(rows) if False else len(ok), len(ok), dict(sorted(w0.items())), forkp, freep, dfp, conf, comm, sum(succs)/max(1,len(succs)), statistics.median(orders), min(orders), max(orders)))
