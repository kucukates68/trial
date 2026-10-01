import sys, itertools, random, pickle; sys.path.insert(0,'.')
from metr import *
from functools import lru_cache
def solver(B):
    @lru_cache(maxsize=None)
    def win(mask, qs):
        if mask == B.full: return True
        for s, q in enumerate(qs):
            if not q: continue
            kind = B.safe(mask, q[0])
            if kind == 'seal': continue
            nq = qs[:s] + (q[1:],) + qs[s+1:]
            if kind == 'won' or win(mask | 1 << q[0], nq): return True
        return False
    return win
def tails_hyp(rem, heads_present):
    """rem: kalan (başı olmayan) parça indeksleri; üç kuyruğun kuyruk kısımlarına her dağılım+sıra. Başı olmayan (biten) slota kuyruk eklenmez."""
    slots = [s for s, h in enumerate(heads_present) if h is not None]
    for perm in itertools.permutations(rem):
        for comp in itertools.product(range(len(perm) + 1), repeat=len(slots) - 1) if len(slots) > 1 else [()]:
            if len(slots) > 1 and sum(comp) > len(perm): continue
            sizes = list(comp) + ([len(perm) - sum(comp)] if len(slots) > 1 else [len(perm)])
            if any(x < 0 for x in sizes): continue
            out = [()] * len(heads_present); i = 0
            for sl, sz in zip(slots, sizes):
                out[sl] = tuple(perm[i:i + sz]); i += sz
            yield out
def analyse_hidden(B, q):
    A = Analysis(B, q); win = solver(B); R = A.reachable(); idx = B.idx
    Qi = [[idx[x] for x in qq] for qq in q]; stats = dict(dec=0, free=0, readable=0, gamble=0, df_wrong_read=0, df_wrong_gamble=0, ex=[])
    for p in R:
        wn, cnt, mv, mask = A.memo[p]
        if not wn: continue
        safes = [m for m in mv if m[2] != 'seal']
        if len(safes) < 2: continue
        stats['dec'] += 1
        heads = A.heads(p); present = [h for h in heads]
        rem = [i for i in range(B.n) if not (mask >> i & 1) and i not in [h for h in heads if h is not None]]
        wins_by = {m[0]: [] for m in safes}; nh = 0
        for tl in tails_hyp(rem, present):
            qs = tuple(((heads[s],) + tl[s]) if heads[s] is not None else () for s in range(3))
            if not win(mask, qs): continue       # çözülebilir varsayımlar (oyuncu seviyenin çözülebilir olduğunu bilir)
            nh += 1
            for m in safes:
                # m kazandırıyor mu bu varsayımda
                s = m[0]; q0 = qs[s]; nq = qs[:s] + (q0[1:],) + qs[s+1:]
                kind = B.safe(mask, q0[0]); ok = (kind == 'won') or (kind == 'safe' and win(mask | 1 << q0[0], nq))
                wins_by[s].append(ok)
        robust = [s for s, v in wins_by.items() if v and all(v)]
        everwin = [s for s, v in wins_by.items() if v and any(v)]
        if len(robust) == len(safes): stats['free'] += 1; continue          # hangisi olursa olsun kazandırıyor (gerçek tercih değil)
        # derin-önce seçeneği
        dp = {m[0]: depth(B, mask, m[1]) for m in mv}; mx = max(dp.values()); dfbest = [m[0] for m in mv if dp[m[0]] == mx]
        df_ok = any(s in robust for s in dfbest) if robust else False
        if robust:
            stats['readable'] += 1
            if not df_ok: stats['df_wrong_read'] += 1; stats['ex'].append(('okunur,derin-önce yanlış', p, heads, robust, dfbest))
        else:
            stats['gamble'] += 1
            if not any(m[3] for m in mv if m[0] in dfbest): stats['df_wrong_gamble'] += 1
            stats['ex'].append(('şans', p, heads, everwin, dfbest))
    return stats
if __name__ == '__main__':
    PART = {'k5 iki bacak bölük':[1,1,3,1,1], 'k6':[1,1,2,1,1,1]}
    res = pickle.load(open('res.pkl','rb'))
    for name, part in PART.items():
        B, names = board_for(part); agg = collections.Counter(); n = 0; ex = []
        for m in res[name]:
            st = analyse_hidden(B, m['q']); n += 1
            for k in ('dec','free','readable','gamble','df_wrong_read','df_wrong_gamble'): agg[k] += st[k]
            m['hid'] = st
            agg['asg_has_read'] += 1 if st['readable'] else 0; agg['asg_has_gamble'] += 1 if st['gamble'] else 0; agg['asg_df_wrong_read'] += 1 if st['df_wrong_read'] else 0; agg['asg_only_free'] += 1 if (st['readable'] == 0 and st['gamble'] == 0) else 0
        print(name, 'düzen', n, dict(agg))
    pickle.dump(res, open('res2.pkl','wb'))
