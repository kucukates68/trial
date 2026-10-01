"""Kuyruk keşfi (yalnız TEŞHİS/aday üretimi; seçim insan okunurluğuna göre yapılır). python3 search_q.py L04 seconds seed"""
import sys, random, time, json, copy
from lvlkit import *
lvl = sys.argv[1]; T = float(sys.argv[2]); seed = int(sys.argv[3])
mod = __import__('author_' + lvl.lower()); cv = mod.cv; g = Geo(cv); vo = valid_order(cv, g); ix = {n: i for i, n in enumerate(vo)}
base = json.load(open('seed_%s.json' % lvl.lower()))        # başlangıç kuyrukları (el yazımı)
rng = random.Random(seed); t0 = time.time(); out = []
def quick(q):
    try: r = report(g, q)
    except RecursionError: return None
    return r if r['solvable'] else None
def band(r): return r
cur = base; cr = quick(cur); seen = {json.dumps(cur)}
while time.time() - t0 < T:
    q = copy.deepcopy(cur); n = rng.choice(vo)
    for s in q:
        if n in s: s.remove(n)
    k = rng.randrange(3); q[k].insert(rng.randint(0, len(q[k])), n)
    if min(len(s) for s in q) < 3: continue
    key = json.dumps(q)
    if key in seen: continue
    seen.add(key); r = quick(q)
    if not r: continue
    out.append(dict(q=q, p=r['p_random'], srw=r['safe_random_win'], ft=r['first_trap'], dl=r['delayed'], dead=r['deadlock_states'], risk=r['risk_hands'], dec=r['decision'], fc=r['forced_chain']['max'], doomed=r['doomed_reachable']))
    # rastgele yürüyüş: kabul (gevşek) — hedef bölgeden uzaklaşmayı sınırla
    if 0.002 <= r['p_random'] <= 0.06 or rng.random() < 0.15: cur = q
json.dump(out, open('cand_%s_%d.json' % (lvl.lower(), seed), 'w'))
print(lvl, seed, 'denendi', len(out))
