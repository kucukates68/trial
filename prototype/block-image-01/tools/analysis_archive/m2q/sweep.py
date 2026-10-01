import sys; sys.path.insert(0,'.')
from metr import *
PART = {'k3 Kemer':[2,3,2], 'k4 sol bacak bölük':[1,1,3,2], 'k4 çatı iki':[2,2,1,2], 'k5 iki bacak bölük':[1,1,3,1,1], 'k5 çatı üç':[2,1,1,1,2], 'k6':[1,1,2,1,1,1], 'k7 hepsi tek':[1,1,1,1,1,1,1]}
res = {}
for name, part in PART.items():
    B, names = board_for(part); rows = []
    for q in assignments(B.names):
        m = metrics(B, q)
        if m['solvable']: rows.append(m)
    tot = sum(1 for _ in assignments(B.names))
    ok_start = [m for m in rows if m['start_safe'] == 3]
    forks = [m for m in ok_start if m['fork'] > 0]; dfw = [m for m in ok_start if m['df_wrong'] > 0]; pdf1 = [m for m in ok_start if m['p_df'] >= 0.999]
    nocomm = [m for m in ok_start if m['noncomm_pairs'] > 0]
    print('%-22s parça %d | kuyruk düzeni %5d | çözülebilir %5d | başta 3 kart güvenli %5d | çatal(güvenli ama sonra kaybeden) var %5d | derin-önce kuralı yanılan durum var %5d | derin-önce her zaman kazandırıyor %5d | komütasyon dışı çift var %5d' % (name, len(B.names), tot, len(rows), len(ok_start), len(forks), len(dfw), len(pdf1), len(nocomm)))
    res[name] = rows
import pickle; pickle.dump(res, open('res.pkl', 'wb'))
