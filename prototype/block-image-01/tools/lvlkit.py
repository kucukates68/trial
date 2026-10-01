"""Level yazım + hızlı analiz kiti (L02+). Mekanik DEĞİŞMEZ; burada yalnızca (1) görsel/parça boyama, (2) doğrulama, (3) kuyruk için hızlı kesin çözücü (bitset taşma) bulunur.
Resmi referans yine tools/ref.py'dir (make_level_blocks.py ikisini çapraz doğrular).
  Canvas: parça = tek renk hücre kümesi; sonraki boyama öncekini ezer. Kuyruk analizi: durum = kuyruk işaretçileri; dolu küme = kuyruk önekleri."""
import json, os, sys, statistics
from collections import defaultdict, deque

W, H = 36, 24


class Canvas:
    def __init__(self):
        self.own = {}; self.color = {}; self.floor = set(); self.entrance = None; self.order = []

    def piece(self, pid, color, cells):
        if pid not in self.color: self.order.append(pid)
        self.color[pid] = color
        for p in cells: self.own[p] = pid
        return self

    def rect(self, pid, color, x0, y0, x1, y1): return self.piece(pid, color, [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)])
    def rows(self, pid, color, spec): return self.piece(pid, color, [(x, y) for y, (x0, x1) in spec.items() for x in range(x0, x1 + 1)])
    def where(self, pid, color, pred, box=(0, 0, W - 1, H - 1)): return self.piece(pid, color, [(x, y) for y in range(box[1], box[3] + 1) for x in range(box[0], box[2] + 1) if pred(x, y)])
    def erase(self, cells):
        for p in cells: self.own.pop(p, None)
    def move(self, pid, pred):    # kuralı sağlayan mevcut hücreleri pid'e ata (parçayı alt bölmek için)
        for p, o in list(self.own.items()):
            if pred(*p): self.own[p] = pid

    def pieces(self):
        d = defaultdict(list)
        for p, n in self.own.items(): d[n].append(p)
        return d

    def finalize(self):
        d = self.pieces(); order = [n for n in self.order if n in d]
        return [dict(id=n, color=self.color[n], cells=[[y, x] for x, y in sorted(d[n], key=lambda p: (p[1], p[0]))]) for n in order]


def comps(S):
    S = set(S); out = []
    while S:
        s = S.pop(); c = {s}; q = deque([s])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p in S: S.remove(p); q.append(p); c.add(p)
        out.append(c)
    return out


def validate(cv, min_size=1):
    d = cv.pieces(); errs = []
    for n, v in d.items():
        if len(comps(v)) != 1: errs.append('BAĞLI DEĞİL %s (%d bileşen)' % (n, len(comps(v))))
        if len(v) < min_size: errs.append('çok küçük %s %d' % (n, len(v)))
    adj = defaultdict(set)
    for (x, y), n in cv.own.items():
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q in cv.own and cv.own[q] != n: adj[n].add(cv.own[q]); adj[cv.own[q]].add(n)
    return errs, adj


def stats_line(cv):
    d = cv.pieces(); sz = sorted(len(v) for v in d.values())
    return dict(cells=sum(sz), pieces=len(sz), mean=round(statistics.mean(sz), 1), median=statistics.median(sz), min=sz[0], max=sz[-1])


class Geo:
    """Parça düzeyi kesin analiz: dolu parça kümesi S → kuyruk başı kartı güvenli mi / kilitler mi."""
    def __init__(self, cv, names=None):
        self.names = names or [n for n in cv.order if n in cv.pieces()]; self.idx = {n: i for i, n in enumerate(self.names)}; self.n = len(self.names)
        self.pm = [0] * self.n; self.open0 = 0
        for (x, y), n in cv.own.items(): self.pm[self.idx[n]] |= 1 << (y * W + x)
        self.targets = 0
        for m in self.pm: self.targets |= m
        self.floor = 0
        for (x, y) in cv.floor: self.floor |= 1 << (y * W + x)
        ex, ey = cv.entrance; self.seed = 1 << ((ey - 1) * W + ex)     # girişin hemen üstündeki hücre (hedef ya da zemin)
        self.nx0 = sum(1 << (y * W + x) for y in range(H + 1) for x in range(1, W)); self.nxw = sum(1 << (y * W + x) for y in range(H + 1) for x in range(W - 1))
        self.cache = {}; self.full = (1 << self.n) - 1

    def fmask(self, S):
        F = 0
        for i in range(self.n):
            if S >> i & 1: F |= self.pm[i]
        return F

    def flood(self, F):
        op = (self.targets & ~F) | self.floor
        if not (op & self.seed): return 0
        R = self.seed
        while True:
            nb = ((R << 1) & self.nx0) | ((R >> 1) & self.nxw) | (R << W) | (R >> W); R2 = (R | nb) & op
            if R2 == R: return R
            R = R2

    def head(self, S, i):
        """'safe' | 'trap' | 'blocked' | 'won'"""
        key = (S, i)
        if key in self.cache: return self.cache[key]
        F = self.fmask(S); R = self.flood(F)
        if self.pm[i] & ~R: r = 'blocked'
        else:
            F2 = F | self.pm[i]; R2 = self.flood(F2)
            if S | 1 << i == self.full: r = 'won'
            elif (self.targets & ~F2) & ~R2: r = 'trap'
            else: r = 'safe'
        self.cache[key] = r; return r


def analyse(geo, queues):
    ids = [[geo.idx[n] for n in q] for q in queues]; lens = [len(q) for q in ids]
    assert sorted(sum(ids, [])) == list(range(geo.n)), 'kuyruklar parçaları tam bir kez içermeli'
    memo = {}
    def S_of(st):
        S = 0
        for k, p in enumerate(st):
            for i in ids[k][:p]: S |= 1 << i
        return S
    def rec(st):
        if st in memo: return memo[st]
        S = S_of(st); hand = [ids[k][st[k]] if st[k] < lens[k] else None for k in range(len(ids))]; mv = []
        for k, i in enumerate(hand):
            if i is None: continue
            kind = geo.head(S, i); st2 = list(st); st2[k] += 1; st2 = tuple(st2)
            if kind == 'won': mv.append((k, 'safe', st2, True, 1, 1.0, 1.0))
            elif kind == 'safe': r = rec(st2); mv.append((k, 'safe', st2, r['win'], r['cnt'], r['p'], r['ps']))
            else: mv.append((k, kind, st2, False, 0, 0.0, 0.0))
        safe = [m for m in mv if m[1] == 'safe']
        win = any(m[3] for m in mv); cnt = sum(m[4] for m in mv); p = sum(m[5] for m in mv) / len(mv) if mv else 0.0
        ps = sum(m[6] for m in safe) / len(safe) if safe else 0.0      # kısa görüşlü oyuncu: yalnız anında kilitlemeyen kartlar arasından rastgele
        memo[st] = dict(win=win, cnt=cnt, p=p, ps=ps, moves=mv, hand=hand, S=S); return memo[st]
    root = rec(tuple(0 for _ in ids)); return dict(memo=memo, root=root, ids=ids, S_of=S_of, start=tuple(0 for _ in ids))


def report(geo, queues):
    A = analyse(geo, queues); memo = A['memo']; root = A['root']; start = A['start']; NP = geo.n
    if not root['win']: return dict(solvable=False)
    reach = set(); stack = [start]; dec = free = forced = delayed = trap_inst = 0; first_trap = first_single = None; n_single = 0; belly = None; hinfo = {}; doomed = 0; deadlock = 0
    allreach = set(); st2 = [start]
    while st2:                                       # güvenli hamlelerle erişilebilir TÜM durumlar (kazanılamaz olanlar dahil)
        s = st2.pop()
        if s in allreach: continue
        allreach.add(s)
        if s in memo:
            for m in memo[s]['moves']:
                if m[1] == 'safe' and m[2] in memo: st2.append(m[2])
    for s in allreach:
        r = memo[s]
        if not r['win'] and sum(s) != NP:
            doomed += 1
            if not [m for m in r['moves'] if m[1] == 'safe']: deadlock += 1
    while stack:
        s = stack.pop()
        if s in reach or s not in memo: continue
        reach.add(s); r = memo[s]
        if not r['win'] or not r['moves']: continue
        d = sum(s) + 1; mv = r['moves']; legal = len(mv); safe = [m for m in mv if m[1] == 'safe']; trap = [m for m in mv if m[1] != 'safe']; winm = [m for m in mv if m[3]]
        if legal == 1: forced += 1
        elif len(winm) == legal: free += 1
        else: dec += 1
        trap_inst += len(trap); delayed += len([m for m in safe if not m[3]])
        if trap: first_trap = d if first_trap is None else min(first_trap, d)
        if len(safe) == 1 and legal >= 2: n_single += 1; first_single = d if first_single is None else min(first_single, d)
        hinfo[s] = (legal, len(safe), len(trap))
        for m in mv:
            if m[3] and m[1] == 'safe': stack.append(m[2])
    order = sorted([s for s in memo if memo[s]['win']], key=lambda s: sum(s)); f = defaultdict(int); f[start] = 1
    for s in order:
        for m in memo[s]['moves']:
            if m[1] == 'safe' and m[3] and m[2] in memo: f[m[2]] += f[s]
    tot = root['cnt']; risk_h = trap_h = 0.0
    for s in order:
        r = memo[s]
        if not r['moves']: continue
        w = f[s] * r['cnt'] / tot; safe = [m for m in r['moves'] if m[1] == 'safe']; trap = [m for m in r['moves'] if m[1] != 'safe']
        if trap: trap_h += w
        if len(safe) >= 2 and trap: risk_h += w
    def runs(kind):
        def ok(info):
            legal, s, t = info
            return s >= 2 and t >= 1 if kind == 'risk' else (s == 1 if kind == 'single' else s >= 2)
        layer = {(start, 0, 0): 1}; res = defaultdict(int)
        while layer:
            nxt = defaultdict(int)
            for (s, cur, best), c in layer.items():
                r = memo[s]
                if sum(s) == NP: res[best] += c; continue
                info = hinfo.get(s); cur2 = cur + 1 if (info and ok(info)) else 0; best2 = max(best, cur2)
                for m in r['moves']:
                    if m[1] == 'safe' and m[3]:
                        if sum(m[2]) == NP: res[best2] += c
                        else: nxt[(m[2], cur2, best2)] += c
            layer = nxt
        t = sum(res.values()); items = sorted(res.items()); mean = sum(k * v for k, v in items) / t; med = None; acc = 0
        for k, v in items:
            acc += v
            if med is None and acc >= t / 2: med = k; break
        return dict(max=items[-1][0], min=items[0][0], mean=round(mean, 2), median=med)
    last = geo.idx.get('__belly__')
    return dict(solvable=True, winning_orders=root['cnt'], p_random=round(root['p'], 5), safe_random_win=round(root['ps'], 4), first_trap=first_trap, first_single_safe=first_single, single_safe_states=n_single,
                forced=forced, decision=dec, free=free, delayed=delayed, trap_instant=trap_inst, doomed_reachable=doomed, deadlock_states=deadlock, n_states=len(allreach),
                risk_hands=round(risk_h, 2), trap_hands=round(trap_h, 2), mdr_risk=runs('risk'), forced_chain=runs('single'))


def story(geo, queues, policy=None, maxrows=99):
    A = analyse(geo, queues); memo = A['memo']; st = A['start']; rows = []
    pol = policy or (lambda s, win: win[0])
    while True:
        r = memo[st]; h = r['hand']; cards = []
        for k, i in enumerate(h):
            if i is None: cards.append('-'); continue
            cards.append(geo.names[i] + ('✗' if geo.head(r['S'], i) in ('trap', 'blocked') else ''))
        win = [m for m in r['moves'] if m[3]]
        if not win: rows.append('%2d [%s] ÇIKMAZ' % (sum(st) + 1, ' | '.join(cards))); break
        m = pol(st, win); rows.append('%2d [%s] → %s (%s)' % (sum(st) + 1, ' | '.join('%-14s' % c for c in cards), geo.names[h[m[0]]], 'ABC'[m[0]]))
        if sum(m[2]) == geo.n: break
        st = m[2]
    return rows[:maxrows]


def repair(cv):
    """Boyama sonrası kopan küçük parça artıklarını (ezilen kümeler) en çok temas ettikleri komşu parçaya kat. Döner: taşınan hücre sayısı."""
    moved = 0
    for _ in range(5):
        changed = False
        for n, v in list(cv.pieces().items()):
            cs = comps(v)
            if len(cs) <= 1: continue
            cs.sort(key=len, reverse=True)
            for frag in cs[1:]:
                contact = defaultdict(int)
                for (x, y) in frag:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        q = (x + dx, y + dy)
                        if q in cv.own and cv.own[q] != n: contact[cv.own[q]] += 1
                if contact:
                    tgt = max(contact, key=contact.get)
                    for p in frag: cv.own[p] = tgt
                    moved += len(frag); changed = True
        if not changed: break
    return moved


def shade(cv, ids, shades, hexmap=None):
    """Aynı bölgedeki komşu parçalar farklı tonda (aynı renk ailesi içinde) olsun: açgözlü komşuluk boyaması."""
    errs, adj = validate(cv); col = {}
    for n in sorted(ids, key=lambda n: -len(adj[n])):
        used = {col[m] for m in adj[n] if m in col}; opts = [s for s in shades if s not in used] or shades
        col[n] = min(opts, key=lambda s: sum(1 for m in ids if col.get(m) == s))
    for n, c in col.items(): cv.color[n] = c


def piece_depth(cv, geo):
    """Başlangıç açık grafında girişten parçanın en yakın hücresine uzaklık (BFS)."""
    ex, ey = cv.entrance; start = (ex, ey - 1); open_ = set(cv.own) | set(cv.floor); dist = {start: 0}; q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p in open_ and p not in dist: dist[p] = dist[(x, y)] + 1; q.append(p)
    dep = {}
    for (x, y), n in cv.own.items(): dep[n] = min(dep.get(n, 999), dist.get((x, y), 999))
    return dep


def valid_order(cv, geo, key=None):
    """Güvenli (kilitlemeyen) bir tam sıra: her adımda güvenli parçalar arasından en derini (ya da key'e göre) seç."""
    dep = piece_depth(cv, geo); S = 0; order = []
    while S != geo.full:
        cand = []
        for i in range(geo.n):
            if S >> i & 1: continue
            k = geo.head(S, i)
            if k in ('safe', 'won'): cand.append(i)
        if not cand: return None
        pick = max(cand, key=lambda i: (key(geo.names[i]) if key else 0, dep[geo.names[i]], -i)); order.append(geo.names[pick]); S |= 1 << pick
    return order


def show(geo, queues, label=''):
    r = report(geo, queues); print('==', label, [len(q) for q in queues])
    if not r['solvable']: print('  ÇÖZÜLEMEZ'); return r
    print('  ' + ' | '.join('%s=%s' % (k, r[k]) for k in ('winning_orders', 'p_random', 'safe_random_win', 'first_trap', 'first_single_safe', 'forced', 'decision', 'free', 'delayed', 'trap_instant', 'doomed_reachable', 'deadlock_states', 'n_states', 'risk_hands', 'trap_hands')))
    print('  mdr_risk %s | forced_chain %s' % (r['mdr_risk'], r['forced_chain'])); return r


def delayed_list(geo, queues, maxn=6):
    A = analyse(geo, queues); memo = A['memo']; out = []; seen = set(); stack = [A['start']]
    while stack:
        st = stack.pop()
        if st in seen or st not in memo: continue
        seen.add(st); r = memo[st]
        if not r['win']: continue
        for m in r['moves']:
            if m[1] == 'safe' and m[3]: stack.append(m[2])
            elif m[1] == 'safe' and not m[3]: out.append((st, m, r['hand']))
    out.sort(key=lambda x: sum(x[0]))
    for st, m, h in out[:maxn]:
        nm = lambda i: geo.names[i] if i is not None else '-'
        print('  durum', st, 'el', [nm(i) for i in h], '→ güvenli ama kazanılamaz:', nm(h[m[0]]), '| sonraki el', [nm(i) for i in memo[m[2]]['hand']])
    return len(out)
