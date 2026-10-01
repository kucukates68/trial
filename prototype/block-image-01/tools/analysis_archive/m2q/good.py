import sys, pickle, random, collections; sys.path.insert(0,'.')
from hid2 import *
res = pickle.load(open('res2.pkl','rb'))
def desc_state(B, A, p, lab):
    wn, cnt, mv, mask = A.memo[p]
    filled = [lab[B.names[i]] for i in range(B.n) if mask >> i & 1]
    return filled, [(lab[B.names[m[1]]], m[2], bool(m[3])) for m in mv]
for name, part, lim in [('k5 iki bacak bölük',[1,1,3,1,1],None),('k6',[1,1,2,1,1,1],None)]:
    B, names = board_for(part); good = []
    lab = {}
    for n_, ch in zip(B.names, []): pass
    for m in res[name]:
        if m['orders'] < 4 or not m['fork']: continue
        o = analyse_peek(B, m['q'], 1)
        if o['readable_df_wrong'] > 0: good.append((m, o))
    tot = sum(1 for m in res[name])
    print(name, 'çözülebilir', tot, '| "iyi" (çatal var + peek1 ile okunur + derin-önce yanılan durum + ≥4 kazanan sıra):', len(good))
    for m, o in good[:3]: print('   ', m['q'], 'orders', m['orders'], 'DF', m['df_orders'], 'çatal', m['fork'], 'serbest', m['free'], 'okunur/yanlışDF', o['readable'], o['readable_df_wrong'])
pickle.dump(None, open('/dev/null','wb'))
