import sys, itertools, pickle, collections; sys.path.insert(0,'.')
from hid import *
def analyse_peek(B, q, d):
    A = Analysis(B, q); win = solver(B); R = A.reachable(); out = collections.Counter(); exs = []
    for p in R:
        wn, cnt, mv, mask = A.memo[p]
        if not wn: continue
        safes = [m for m in mv if m[2] != 'seal']
        if len(safes) < 2: continue
        vis = [tuple(A.Q[s][p[s]:p[s] + d + 1]) for s in range(3)]
        visible = {x for v in vis for x in v}
        rem = [i for i in range(B.n) if not (mask >> i & 1) and i not in visible]
        present = [v[0] if v else None for v in vis]
        wins_by = {m[0]: [] for m in safes}
        for tl in tails_hyp(rem, present):
            qs = tuple((vis[s] + tl[s]) if vis[s] else () for s in range(3))
            if not win(mask, qs): continue
            for m in safes:
                s = m[0]; q0 = qs[s]; nq = qs[:s] + (q0[1:],) + qs[s+1:]
                kind = B.safe(mask, q0[0]); wins_by[s].append(kind == 'won' or (kind == 'safe' and win(mask | 1 << q0[0], nq)))
        robust = [s for s, v in wins_by.items() if v and all(v)]
        out['dec'] += 1
        if len(robust) == len(safes): out['free'] += 1; continue
        dp = {m[0]: depth(B, mask, m[1]) for m in mv}; mx = max(dp.values()); dfbest = [m[0] for m in mv if dp[m[0]] == mx]
        if robust:
            out['readable'] += 1
            if not any(s in robust for s in dfbest): out['readable_df_wrong'] += 1
        else: out['gamble'] += 1
    return out
if __name__ == '__main__':
    res = pickle.load(open('res2.pkl','rb'))
    for name, part in {'k5 iki bacak bölük':[1,1,3,1,1], 'k6':[1,1,2,1,1,1]}.items():
        B, names = board_for(part)
        for d in (0, 1, 2):
            agg = collections.Counter(); asg = collections.Counter()
            for m in res[name]:
                o = analyse_peek(B, m['q'], d); agg.update(o)
                asg['asg_fork'] += 1 if m['fork'] else 0
                asg['asg_readable'] += 1 if o['readable'] else 0; asg['asg_gamble'] += 1 if o['gamble'] else 0; asg['asg_readable_df_wrong'] += 1 if o['readable_df_wrong'] else 0
            print(name, 'görünen derinlik d=%d' % d, dict(agg), dict(asg))
