"""Deepest-first wave puzzle: exact solver + decision metrics.

Model (unchanged reference model):
  * grid, 'E' entrance, '#' wall, '.' floor, any other letter = target cell of that colour
  * workers move on 4-neighbourhood over floor + not-yet-filled target cells
  * a filled target cell becomes a permanent obstacle
  * player picks a colour; W boxes of that colour are placed, deepest reachable cell first
    (ties: lower row-major index first)
  * a target that is unreachable while unfilled is lost for good -> the state is "sealed"
  * goal: fill every target cell

Speed note: within one wave the placement order equals "sort the reachable unfilled cells of
that colour by (-dist, index) at the START of the wave and take W" (placing the deepest cell
cannot change dist/reachability of the remaining cells of the same colour).  Verified against
the naive box-by-box implementation in research/tests.
"""
from __future__ import annotations
import math, os, random, sys
from collections import deque

sys.setrecursionlimit(100000)

DELTA_MEAN = float(os.environ.get('PUZZLE_DELTA', '0.05'))      # MEANINGFUL-SAFE threshold on spread of random-continuation win prob
STATE_CAP = 120000


class Level:
    def __init__(self, grid: str, W: int):
        rows = grid.split('\n')
        self.W = W
        ids = {}
        cells = []
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != '#':
                    ids[(r, c)] = len(cells)
                    cells.append((r, c, ch))
        self.N = len(cells)
        self.nbrs = [[] for _ in range(self.N)]
        for (r, c), i in ids.items():
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                j = ids.get((r + dr, c + dc))
                if j is not None:
                    self.nbrs[i].append(j)
        self.ent = [i for i, (r, c, ch) in enumerate(cells) if ch == 'E']
        tcells = [(i, r, c, ch) for i, (r, c, ch) in enumerate(cells) if ch not in '.E']
        tcells.sort(key=lambda x: (x[1], x[2]))          # row-major
        self.n = len(tcells)
        self.tnode = [t[0] for t in tcells]
        self.tpos = [(t[1], t[2]) for t in tcells]
        letters = sorted(set(t[3] for t in tcells))
        self.letters = letters
        self.K = len(letters)
        self.tcolor = [letters.index(t[3]) for t in tcells]
        self.ti_of_node = [-1] * self.N
        for ti, nd in enumerate(self.tnode):
            self.ti_of_node[nd] = ti
        self.by_color = [[ti for ti in range(self.n) if self.tcolor[ti] == k] for k in range(self.K)]
        self.cnt = [len(b) for b in self.by_color]
        self.full = (1 << self.n) - 1
        self.waves_nominal = sum(math.ceil(c / W) for c in self.cnt)
        self._info = {}

    # ---------------------------------------------------------------- basics
    def bfs(self, s):
        d = [-1] * self.N
        q = deque(self.ent)
        for e in self.ent:
            d[e] = 0
        nb = self.nbrs
        tio = self.ti_of_node
        while q:
            u = q.popleft()
            du = d[u] + 1
            for v in nb[u]:
                if d[v] < 0:
                    ti = tio[v]
                    if ti >= 0 and (s >> ti) & 1:
                        continue
                    d[v] = du
                    q.append(v)
        return d

    def info(self, s):
        """(sealed, moves) ; moves = tuple of (colour, next_state)."""
        r = self._info.get(s)
        if r is not None:
            return r
        d = self.bfs(s)
        tnode = self.tnode
        sealed = False
        for ti in range(self.n):
            if not (s >> ti) & 1 and d[tnode[ti]] < 0:
                sealed = True
                break
        if sealed:
            r = (True, ())
        else:
            mv = []
            for k in range(self.K):
                cand = [(-d[tnode[ti]], ti) for ti in self.by_color[k]
                        if not (s >> ti) & 1 and d[tnode[ti]] >= 0]
                if not cand:
                    continue
                cand.sort()
                t = s
                for _, ti in cand[:self.W]:
                    t |= 1 << ti
                mv.append((k, t))
            r = (False, tuple(mv))
        self._info[s] = r
        return r

    def locked_mask(self, s):
        """bitmask of *live bottlenecks* at state s: unfilled target cells that dominate >=1 other unfilled
        target (every entrance path to that other target passes through the cell).  Cooper-Harvey-Kennedy
        dominators on the open graph with a virtual root joined to all entrances."""
        N = self.N
        nb, tio, ent = self.nbrs, self.ti_of_node, self.ent
        filled = lambda v: tio[v] >= 0 and (s >> tio[v]) & 1
        ent_set = set(ent)
        visited = [False] * (N + 1)
        post = []
        visited[N] = True
        stack = [(N, iter(ent))]
        while stack:
            u, it = stack[-1]
            for v in it:
                if not visited[v] and not filled(v):
                    visited[v] = True
                    stack.append((v, iter(nb[v])))
                    break
            else:
                post.append(u)
                stack.pop()
        po = [-1] * (N + 1)
        for i, u in enumerate(post):
            po[u] = i
        idom = [-1] * (N + 1)
        idom[N] = N
        rpo = post[::-1]
        changed = True
        while changed:
            changed = False
            for v in rpo[1:]:
                new = -1
                cand = [u for u in nb[v] if visited[u] and idom[u] != -1]
                if v in ent_set and idom[N] != -1:
                    cand.append(N)
                for p in cand:
                    if new == -1:
                        new = p
                    else:
                        a, b = p, new
                        while a != b:
                            while po[a] < po[b]:
                                a = idom[a]
                            while po[b] < po[a]:
                                b = idom[b]
                        new = a
                if idom[v] != new:
                    idom[v] = new
                    changed = True
        has = [False] * (N + 1)
        for v in post[:-1]:
            if tio[v] >= 0 or has[v]:
                has[idom[v]] = True
        mask = 0
        for ti in range(self.n):
            nd = self.tnode[ti]
            if not (s >> ti) & 1 and visited[nd] and has[nd]:
                mask |= 1 << ti
        return mask

    def depth_profile(self):
        """initial reach depth of every target (-1 = unreachable)."""
        d = self.bfs(0)
        return [d[nd] for nd in self.tnode]


# ------------------------------------------------------------------ analysis
def _wmean(vals, w):
    sw = sum(w)
    return sum(v * x for v, x in zip(vals, w)) / sw if sw > 0 else float('nan')


def _wquant(vals, w, q):
    if not vals:
        return float('nan')
    z = sorted(zip(vals, w))
    tot = sum(w)
    acc = 0.0
    for v, x in z:
        acc += x
        if acc >= q * tot:
            return v
    return z[-1][0]


def extra_metrics(L, order, nwin, pwin, sd, onwin, res, seed=11):
    """Phase-1 metric upgrade.  All expectations are over the 'uniform among SAFE moves' path (mass pi);
    mistakes are weighted by the chance that a player who otherwise plays safely errs there
    (pi(s)/|legal(s)| per losing move).  Definitions in REPORT_PHASE2.md."""
    full = L.full
    n = L.n
    pop = {s: s.bit_count() for s in order}
    out = {}
    pi = {s: 0.0 for s in onwin}
    pi[0] = 1.0
    for s in sorted(onwin, key=lambda x: pop[x]):
        if s == full:
            continue
        good = [t for _, t in L.info(s)[1] if nwin[t]]
        for t in good:
            pi[t] += pi[s] / len(good)
    locked = {s: L.locked_mask(s) for s in onwin if s != full}
    # ---- deadlock horizon / blind progress (non-winning side)
    es, lmax, bg = {}, {}, {}
    for u in order:
        if nwin[u]:
            continue
        sealed, mv = L.info(u)
        if sealed:
            es[u] = 0.0; lmax[u] = 0; bg[u] = 0.0
        else:
            ch = [t for _, t in mv]
            es[u] = 1 + sum(es[t] for t in ch) / len(ch)
            lmax[u] = 1 + max(lmax[t] for t in ch)
            bg[u] = sum((pop[t] - pop[u]) / n + bg[t] for t in ch) / len(ch)
    W_, DHe, DHm, DHx, BP, LAT = [], [], [], [], [], []
    for s in onwin:
        if s == full:
            continue
        mv = L.info(s)[1]
        for _, t in mv:
            if not nwin[t]:
                W_.append(pi[s] / len(mv)); DHe.append(1 + es[t]); DHm.append(sd[t] + 1); DHx.append(1 + lmax[t])
                BP.append((pop[t] - pop[s]) / n + bg[t]); LAT.append(0 if L.info(t)[0] else 1)
    out['mistake_mass'] = sum(W_)
    if W_:
        out['dh_exp_mean'] = _wmean(DHe, W_); out['dh_min_mean'] = _wmean(DHm, W_); out['dh_max_mean'] = _wmean(DHx, W_)
        out['dh_p50'] = _wquant(DHe, W_, 0.5); out['dh_max_overall'] = max(DHx)
        out['dh_instant_share'] = _wmean([1.0 if m == 1 else 0.0 for m in DHm], W_)
        out['dh_latent_share'] = 1 - out['dh_instant_share']
        out['dh_band35_share'] = _wmean([1.0 if 3 <= e <= 5 else 0.0 for e in DHe], W_)
        out['blind_progress_mean'] = _wmean(BP, W_)
        out['blind_progress_ge5_share'] = _wmean([1.0 if b >= 0.05 else 0.0 for b in BP], W_)
        out['latent_doom_mass'] = sum(w for w, l in zip(W_, LAT) if l)
    else:
        for k in ('dh_exp_mean', 'dh_min_mean', 'dh_max_mean', 'dh_p50', 'dh_max_overall', 'dh_instant_share', 'dh_latent_share',
                  'dh_band35_share', 'blind_progress_mean', 'blind_progress_ge5_share'):
            out[k] = float('nan')
        out['latent_doom_mass'] = 0.0
    # ---- state-level aggregates under pi
    D0 = locked[0]
    nD0 = D0.bit_count()
    mass = mass2 = massr = 0.0
    sV = sG = sM = sH = sCpr = sAbc = sAbc3 = sLf = 0.0
    maxAbc = 0; maxLf = 0.0
    third = [[0.0, 0.0] for _ in range(3)]
    c40 = [0.0, 0.0]
    clo_lead = 0.0
    xs, hs, ls = [], [], []
    wts = []
    for s, p in pi.items():
        if s == full or p <= 0:
            continue
        mv = L.info(s)[1]
        nL = len(mv)
        good = [t for _, t in mv if nwin[t]]
        nG = len(good)
        nB = nL - nG
        prog = pop[s] / n
        ab = locked[s].bit_count()
        unf = n - pop[s]
        lf = ab / unf if unf else 0.0
        mass += p
        sV += p * nL; sG += p * nG
        haz = nB / nL
        sH += p * haz
        if nL >= 2:
            mass2 += p
            ps = sorted(pwin[t] for t in good)
            m = 1
            for a, b in zip(ps, ps[1:]):
                if b - a >= 0.05:
                    m += 1
            sM += p * m
        if nB >= 1 and nL >= 2:
            massr += p
            sCpr += p * (nG / nL)
        sAbc += p * ab
        sAbc3 += p * (1.0 if ab >= 3 else 0.0)
        sLf += p * lf
        maxAbc = max(maxAbc, ab)
        maxLf = max(maxLf, lf)
        t3 = min(2, int(prog * 3))
        third[t3][0] += p * ab; third[t3][1] += p
        if 0.35 <= prog <= 0.45 and nD0:
            c40[0] += p * ((D0 & s).bit_count() / nD0); c40[1] += p
        if nD0:
            clo_lead = max(clo_lead, (D0 & s).bit_count() / nD0 - prog)
        xs.append(prog); hs.append(haz); ls.append(lf); wts.append(p)
    out['visible_mean'] = sV / mass
    out['safe_mean'] = sG / mass
    out['mbf_mean'] = (sM / mass2) if mass2 > 0 else float('nan')
    out['mbf_over_visible'] = (sM / mass2) / (sV / mass) if mass2 > 0 else float('nan')
    out['cpr_risky'] = (sCpr / massr) if massr > 0 else float('nan')
    out['hazard_mean'] = sH / mass
    out['abc_mean'] = sAbc / mass; out['abc_max_dag'] = maxAbc; out['abc_ge3_share'] = sAbc3 / mass
    for i, nm in enumerate(('early', 'mid', 'late')):
        out['abc_' + nm] = third[i][0] / third[i][1] if third[i][1] > 0 else float('nan')
    out['pp_locked_mean'] = sLf / mass; out['pp_locked_max'] = maxLf
    out['closure_at_40pct'] = c40[0] / c40[1] if c40[1] > 0 else float('nan')
    out['closure_lead_max'] = clo_lead if nD0 else float('nan')
    out['abc_initial'] = nD0

    def wcorr(a, b, w):
        sw = sum(w)
        ma = _wmean(a, w); mb = _wmean(b, w)
        va = sum(x * (u - ma) ** 2 for u, x in zip(a, w)) / sw
        vb = sum(x * (u - mb) ** 2 for u, x in zip(b, w)) / sw
        if va < 1e-12 or vb < 1e-12:
            return float('nan')
        return sum(x * (u - ma) * (v - mb) for u, v, x in zip(a, b, w)) / sw / math.sqrt(va * vb)
    out['corr_progress_hazard'] = wcorr(xs, hs, wts)
    out['corr_progress_locked'] = wcorr(xs, ls, wts)
    # distinct bottlenecks per trajectory (sequential vs simultaneous)
    rng = random.Random(seed)
    dist = []
    for _ in range(100):
        s = 0; acc = 0
        while s != full:
            acc |= locked[s]
            good = [t for _, t in L.info(s)[1] if nwin[t]]
            s = rng.choice(good)
        dist.append(acc.bit_count())
    out['abc_distinct_path'] = sum(dist) / len(dist)
    out['abc_concurrency'] = out['abc_mean'] / out['abc_distinct_path'] if out['abc_distinct_path'] > 0 else float('nan')
    # ---- filler vs decision
    em = max(res['e_moves'], 1e-9)
    out['filler_ratio'] = 1 - res['e_risky'] / em
    out['filler_strict'] = (res['e_free'] + res['e_forced']) / em
    out['filler_to_decision'] = (em - res['e_risky']) / res['e_risky'] if res['e_risky'] > 1e-9 else float('nan')
    return out


def analyze(grid: str, W: int, sims: int = 1500, seed: int = 1, want_desc=None, extra: bool = False):
    L = Level(grid, W)
    res = dict(W=W, cells=L.n, K=L.K, waves_nominal=L.waves_nominal)
    # state-space guard
    est = 1
    for c in L.cnt:
        est *= (math.ceil(c / W) + 1)
    if est > STATE_CAP * 3:
        res.update(skipped=True, solv=False)
        return res
    full = L.full
    # ---- explore reachable state graph
    order = []
    seen = {0}
    stack = [0]
    while stack:
        s = stack.pop()
        order.append(s)
        sealed, mv = L.info(s)
        if sealed or s == full:
            continue
        for _, t in mv:
            if t not in seen:
                seen.add(t)
                stack.append(t)
        if len(seen) > STATE_CAP:
            res.update(skipped=True, solv=False, n_states=len(seen))
            return res
    order.sort(key=lambda s: -s.bit_count())              # children (more bits) first
    res['n_states'] = len(order)
    sealed0, _ = L.info(0)
    if sealed0:
        res.update(solv=False, seq_raw=0)
        return res

    nwin = {}
    pwin = {}
    sd = {}
    for s in order:
        sealed, mv = L.info(s)
        if s == full:
            nwin[s] = 1; pwin[s] = 1.0; sd[s] = 10 ** 6
        elif sealed:
            nwin[s] = 0; pwin[s] = 0.0; sd[s] = 0
        else:
            nwin[s] = sum(nwin[t] for _, t in mv)
            pwin[s] = sum(pwin[t] for _, t in mv) / len(mv)
            sd[s] = 1 + min(sd[t] for _, t in mv)
    total = nwin[0]
    res['seq_raw'] = total
    res['solv'] = total > 0
    if total == 0:
        res['rnd0'] = 0.0
        return res
    p0 = pwin[0]
    res['rnd0'] = p0
    wn = L.waves_nominal
    res['risk'] = 1 - p0 ** (1.0 / max(wn, 1))

    # ---- greedy heuristics
    def run_greedy(kind):
        s = 0
        while s != full:
            sealed, mv = L.info(s)
            if sealed or not mv:
                return False
            if kind == 'deep':
                d = L.bfs(s)
                best = None
                for ti in range(L.n):
                    if not (s >> ti) & 1 and d[L.tnode[ti]] >= 0:
                        key = (-d[L.tnode[ti]], ti)
                        if best is None or key < best[0]:
                            best = (key, ti)
                col = L.tcolor[best[1]]
                s = dict(mv)[col]
            else:  # biggest remaining colour
                rem = {k: sum(1 for ti in L.by_color[k] if not (s >> ti) & 1) for k, _ in mv}
                col = max(rem, key=lambda k: (rem[k], -k))
                s = dict(mv)[col]
        return True
    res['greedy_deep'] = run_greedy('deep')
    res['greedy_stock'] = run_greedy('stock')

    # ---- winning DAG, decision taxonomy, policy expectations (uniform over SAFE moves)
    win_states = []
    onwin = set()
    st = [0]
    while st:
        s = st.pop()
        if s in onwin or nwin[s] == 0:
            continue
        onwin.add(s)
        if s == full:
            continue
        for _, t in L.info(s)[1]:
            if nwin[t]:
                st.append(t)
    n = L.n
    cat_of = {}
    info_of = {}
    for s in onwin:
        if s == full:
            continue
        mv = L.info(s)[1]
        good = [(k, t) for k, t in mv if nwin[t]]
        bad = [(k, t) for k, t in mv if not nwin[t]]
        nL, nG, nB = len(mv), len(good), len(bad)
        if nL == 1:
            cat = 'forced'
        elif nB == 0:
            ps = [pwin[t] for _, t in good]
            cat = 'meansafe' if (max(ps) - min(ps)) >= DELTA_MEAN else 'free'
        elif nG == 1:
            cat = 'crit'
        else:
            cat = 'trap'
        cat_of[s] = cat
        info_of[s] = (nL, nG, nB)

    IDX = {'forced': 0, 'free': 1, 'meansafe': 2, 'trap': 3, 'crit': 4}
    # vector: [forced, free, meansafe, trap, crit, moves, risky_third0..2, sharp_sum, riskyprog_sum, n_risky]
    V = {}
    for s in sorted(onwin, key=lambda x: -x.bit_count()):
        if s == full:
            V[s] = [0.0] * 14
            continue
        cat = cat_of[s]
        nL, nG, nB = info_of[s]
        c = [0.0] * 14
        c[IDX[cat]] = 1.0
        c[5] = 1.0
        if cat in ('trap', 'crit'):
            prog = s.bit_count() / n
            c[6 + min(2, int(prog * 3))] = 1.0
            c[9] = nB / nL
            c[10] = prog
            c[11] = 1.0
        good = [t for _, t in L.info(s)[1] if nwin[t]]
        acc = [0.0] * 14
        for t in good:
            vt = V[t]
            for i in range(14):
                acc[i] += vt[i]
        for i in range(14):
            c[i] += acc[i] / len(good)
        V[s] = c
    v0 = V[0]
    res.update(e_forced=v0[0], e_free=v0[1], e_meansafe=v0[2], e_trap=v0[3], e_crit=v0[4], e_moves=v0[5])
    res['e_meaningful'] = v0[2] + v0[3] + v0[4]
    res['e_risky'] = v0[3] + v0[4]
    em = max(v0[5], 1e-9)
    res['dens_meaningful'] = res['e_meaningful'] / em
    res['dens_risky'] = res['e_risky'] / em
    res['dens_crit'] = v0[4] / em
    res['forced_free_ratio'] = (v0[0] + v0[1]) / em
    tot_r = v0[6] + v0[7] + v0[8]
    res['risky_early'] = v0[6]; res['risky_mid'] = v0[7]; res['risky_late'] = v0[8]
    res['trap_timing'] = (v0[10] / v0[11]) if v0[11] > 1e-9 else float('nan')     # mean progress at risky states
    res['trap_sharp'] = (v0[9] / v0[11]) if v0[11] > 1e-9 else float('nan')        # mean share of losing options
    res['crit_share'] = (v0[4] / res['e_risky']) if res['e_risky'] > 1e-9 else float('nan')
    # state-level (unweighted) shares on the winning DAG
    cs = {k: 0 for k in IDX}
    for s, c in cat_of.items():
        cs[c] += 1
    res['n_win_states'] = len(onwin)
    for k in IDX:
        res['share_' + k] = cs[k] / max(len(cat_of), 1)
    mv0 = L.info(0)[1]
    res['first_legal'] = len(mv0)
    res['first_safe'] = sum(1 for _, t in mv0 if nwin[t])
    res['first_trap'] = res['first_safe'] < res['first_legal']
    # earliest / latest risky progress anywhere in winning DAG
    rp = [s.bit_count() / n for s, c in cat_of.items() if c in ('trap', 'crit')]
    res['trap_first_prog'] = min(rp) if rp else float('nan')
    res['trap_last_prog'] = max(rp) if rp else float('nan')

    # ---- regret depth of every mistake edge (win state -> non-win successor)
    needs = []
    for s in onwin:
        if s == full:
            continue
        for _, t in L.info(s)[1]:
            if not nwin[t]:
                needs.append(sd[t] + 1)
    res['n_mistakes'] = len(needs)
    if needs:
        res['regret_mean'] = sum(needs) / len(needs)
        res['regret_max'] = max(needs)
        res['regret_ge2'] = sum(1 for x in needs if x >= 2) / len(needs)
        res['regret_ge3'] = sum(1 for x in needs if x >= 3) / len(needs)
        res['rec1'] = sum(1 for x in needs if x <= 1) / len(needs)
        res['rec2'] = sum(1 for x in needs if x <= 2) / len(needs)
    else:
        res.update(regret_mean=0.0, regret_max=0, regret_ge2=0.0, regret_ge3=0.0, rec1=1.0, rec2=1.0)
    res['rec0'] = 0.0 if needs else 1.0

    # ---- solution-order diversity: adjacent-commutation-normal-form count (upper bound on trace classes)
    canon_memo = {}
    def f(p, a):
        key = (p, a)
        r = canon_memo.get(key)
        if r is not None:
            return r
        mvp = dict(L.info(p)[1])
        sst = mvp[a]
        if sst == full:
            canon_memo[key] = 1
            return 1
        tot = 0
        for b, t in L.info(sst)[1]:
            if not nwin[t]:
                continue
            if b < a:
                q = mvp.get(b)
                if q is not None and dict(L.info(q)[1]).get(a) == t:
                    continue          # adjacent independent swap with smaller colour first -> not normal form
            tot += f(sst, b)
        canon_memo[key] = tot
        return tot
    res['seq_canon'] = sum(f(0, a) for a, t in mv0 if nwin[t])
    res['log_seq_raw_per_move'] = math.log10(max(total, 1)) / max(v0[5], 1)
    res['log_seq_canon_per_move'] = math.log10(max(res['seq_canon'], 1)) / max(v0[5], 1)

    # ---- undo budgets (random legal player; exact for 0, Monte-Carlo for 1 and 2)
    rng = random.Random(seed)
    for K in (1, 2):
        wins = 0
        for _ in range(sims):
            s = 0; hist = []; banned = {}; k = K
            while True:
                if s == full:
                    wins += 1
                    break
                sealed, mv = L.info(s)
                if sealed or not mv:
                    if k > 0 and hist:
                        ps, m = hist.pop(); banned.setdefault(ps, set()).add(m); s = ps; k -= 1
                        continue
                    break
                opts = [(c, t) for c, t in mv if c not in banned.get(s, ())]
                if not opts:
                    if k > 0 and hist:
                        ps, m = hist.pop(); banned.setdefault(ps, set()).add(m); s = ps; k -= 1
                        continue
                    break
                c, t = rng.choice(opts)
                hist.append((s, c)); s = t
        res[f'win_undo{K}'] = wins / sims
    res['win_undo0'] = p0

    if extra:
        res.update(extra_metrics(L, order, nwin, pwin, sd, onwin, res))

    # ---- optional descriptors that need the level (entrance depth profile)
    if want_desc is not None:
        res.update(want_desc(L))
    return res
