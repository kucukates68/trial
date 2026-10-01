import sys; sys.path.insert(0,'.')
from kit import *
def metrics(B, q, full=False):
    A = Analysis(B, q); root = A.memo[A.start]
    out = dict(solvable=bool(root[0]), orders=root[1], q=q)
    if not root[0]: return out
    heads0 = A.heads(A.start); out['start_safe'] = sum(1 for m in root[2] if m[2] != 'seal'); out['start_win'] = sum(1 for m in root[2] if m[3])
    R = A.reachable(); n = {'forced': 0, 'free': 0, 'fork': 0, 'dead': 0}
    comm = noncomm_asym = 0; df_wrong = 0; df_wrong_states = []; lagh = []
    # derin-önce: kartların (mevcut durumda) en derin hücre uzaklığı; en derin olan(lar) seçilir
    def dfcount(ptr, cache):
        if ptr in cache: return cache[ptr]
        win, cnt, mv, mask = A.memo[ptr]; moves = [m for m in mv]
        if not moves: cache[ptr] = (0.0, 0); return cache[ptr]
        dp = {m[0]: depth(B, mask, m[1]) for m in moves}; mx = max(dp.values()); best = [m for m in moves if dp[m[0]] == mx]
        pw = 0.0; cw = 0
        for m in best:
            if m[2] == 'won': pw += 1.0; cw += 1
            elif m[2] == 'seal': pass
            else:
                sub = dfcount(m[5], cache); pw += sub[0]; cw += sub[1]
        cache[ptr] = (pw / len(best), cw); return cache[ptr]
    cache = {}; pdf, cdf = dfcount(A.start, cache)
    out['p_df'] = pdf; out['df_orders'] = cdf   # df_orders: derin-önceyle uyumlu kazanan sıra sayısı (eşitlikte tüm dallar)
    for p in R:
        win, cnt, mv, mask = A.memo[p]
        safes = [m for m in mv if m[2] != 'seal']
        if not win: n['dead'] += 1; continue
        W = [m for m in safes if m[3]]; D = [m for m in safes if not m[3]]
        if len(safes) == 1: n['forced'] += 1
        elif D: n['fork'] += 1; [lagh.append(A.surv(m[5])) for m in D]
        else: n['free'] += 1
        # komütasyon: iki farklı slotun başı ikisi de güvenli → iki sırada da güvenli mi
        for x, y in itertools.combinations(safes, 2):
            def after(mx, my):
                p1 = list(p); p1[mx[0]] += 1; p1 = tuple(p1); mask1 = mask | 1 << mx[1]
                if p1 not in A.memo: return False
                return any(m[0] == my[0] and m[2] != 'seal' for m in A.memo[p1][2])
            a, b = after(x, y), after(y, x)
            if a and b: comm += 1
            elif a or b: noncomm_asym += 1
        # derin-önce karar: bu durumda en derin kart(lar)ın hiçbiri kazandırmıyorsa kural yanılıyor
        dp = {m[0]: depth(B, mask, m[1]) for m in mv}; mx = max(dp.values()); best = [m for m in mv if dp[m[0]] == mx]
        if not any(m[3] for m in best): df_wrong += 1; df_wrong_states.append(p)
    out.update(n, comm_pairs=comm, noncomm_pairs=noncomm_asym, df_wrong=df_wrong, lag=sorted(lagh), states=len(R))
    return out
