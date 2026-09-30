"""Parça (piece) mekaniği — Python REFERANS uygulaması + tam çözücü.  (prototype/src/engine.js ile parity hedefi)

Kurallar (engine.js `PLevel` ile birebir aynı olmalı):
  * Izgara: 'E' giriş, '#' duvar, '.' zemin, harf = hedef hücre (renk).  Hedefler satır-ana sırada indekslenir.
  * Parça = sabit yönlü polyomino (döndürme yok), bir RENGİ var.  Oyuncu yalnız hangi parçayı göndereceğini seçer.
  * Olası konum = parçanın bir ÖTELEMESİ; tüm hücreleri (a) hedef hücre, (b) parça rengiyle aynı renk, (c) henüz boş,
    (d) girişten erişilebilir olmalı.
  * choose_target (AYRI FONKSİYON, sonradan değişebilir): olası konumlar içinde
        min (dmin, dsum, satır, sütun)   — dmin = hücrelerin girişe en küçük uzaklığı, dsum = uzaklık toplamı,
        (satır, sütun) = parçanın sol-üst köşesi (bbox)
    yani "girişe en yakın erişilebilir uygun konum".
  * Yerleşme sırası parça içinde (uzaklık azalan, satır, sütun) = en derinden başla. Parça ATOMİK yerleşir.
  * Kayıp: boş bir hedef hücreye girişten yol kalmadı (sealed)  VEYA  kazanılmadı ve kalan hiçbir parçanın konumu yok (stuck).
  * Kazanma: tüm hedef hücreler dolu.
"""
import json, sys, random
from collections import deque, Counter
from functools import lru_cache

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def norm(cells):
    r0 = min(r for r, c in cells); c0 = min(c for r, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


class PLevel:
    def __init__(self, text, pieces):
        rows = text.rstrip().split('\n')
        self.h = len(rows); self.w = max(len(r) for r in rows)
        self.kind = {}
        self.entrances = []
        cells = []
        for r in range(self.h):
            for c in range(self.w):
                ch = rows[r][c] if c < len(rows[r]) else '#'
                if ch == '#': self.kind[(r, c)] = 0
                elif ch == '.': self.kind[(r, c)] = 1
                elif ch == 'E': self.kind[(r, c)] = 2; self.entrances.append((r, c))
                else: self.kind[(r, c)] = 3; cells.append((r, c, ch))
        self.letters = sorted(set(ch for _, _, ch in cells))
        cells.sort(key=lambda t: (t[0], t[1]))
        self.targets = [(r, c, self.letters.index(ch)) for r, c, ch in cells]
        self.n = len(self.targets)
        self.tidx = {(r, c): i for i, (r, c, _) in enumerate(self.targets)}
        self.pieces = [dict(id=p['id'], ch=p['ch'], col=self.letters.index(p['ch']), cells=norm([tuple(x) for x in p['cells']])) for p in pieces]
        self.P = len(self.pieces)
        cnt = Counter(t[2] for t in self.targets); pc = Counter()
        for p in self.pieces: pc[p['col']] += len(p['cells'])
        assert cnt == pc, f'renk başına hücre sayısı parçalarla uyuşmuyor: {cnt} vs {pc}'
        self.full = (1 << self.n) - 1

    # --- BFS (filled = bitmask) ---
    def bfs(self, filled):
        dist = {}
        q = deque()
        for e in self.entrances: dist[e] = 0; q.append(e)
        while q:
            u = q.popleft()
            for dr, dc in DIRS:
                v = (u[0] + dr, u[1] + dc)
                if v in dist or self.kind.get(v, 0) == 0: continue
                ti = self.tidx.get(v)
                if ti is not None and (filled >> ti) & 1: continue
                dist[v] = dist[u] + 1; q.append(v)
        return dist

    def positions(self, filled, pi, dist=None):
        dist = dist if dist is not None else self.bfs(filled)
        p = self.pieces[pi]; out = []
        for r in range(self.h):
            for c in range(self.w):
                ok = True; tis = []; ds = []
                for dr, dc in p['cells']:
                    cell = (r + dr, c + dc); ti = self.tidx.get(cell)
                    if ti is None or self.targets[ti][2] != p['col'] or (filled >> ti) & 1 or cell not in dist: ok = False; break
                    tis.append(ti); ds.append(dist[cell])
                if ok: out.append(dict(r=r, c=c, cells=tis, dmin=min(ds), dsum=sum(ds)))
        return out

    def choose_target(self, filled, pi, dist=None):
        pos = self.positions(filled, pi, dist)
        if not pos: return None
        return min(pos, key=lambda q: (q['dmin'], q['dsum'], q['r'], q['c']))

    def place(self, state, pi):
        """state = (filled, used). Döner: dict(placed=[ti...], pos, state, sealed=[ti], won, stuck) veya None (yasadışı)."""
        filled, used = state
        if (used >> pi) & 1: return None
        dist = self.bfs(filled); pos = self.choose_target(filled, pi, dist)
        if pos is None: return None
        order = sorted(pos['cells'], key=lambda ti: (-dist[(self.targets[ti][0], self.targets[ti][1])], self.targets[ti][0], self.targets[ti][1]))
        f2 = filled
        for ti in order: f2 |= 1 << ti
        u2 = used | (1 << pi)
        d2 = self.bfs(f2)
        sealed = [i for i in range(self.n) if not (f2 >> i) & 1 and (self.targets[i][0], self.targets[i][1]) not in d2]
        won = f2 == self.full
        stuck = False
        if not won and not sealed:
            stuck = not any(self.positions(f2, j, d2) for j in range(self.P) if not (u2 >> j) & 1)
        return dict(placed=order, pos=pos, state=(f2, u2), sealed=sealed, won=won, stuck=stuck)

    def options(self, state):
        filled, used = state; dist = self.bfs(filled)
        return [None if (used >> j) & 1 else self.choose_target(filled, j, dist) for j in range(self.P)]

    def legal(self, state):
        return [j for j, o in enumerate(self.options(state)) if o is not None]

    def simulate(self, seq):
        """seq = parça indeksleri.  Her adım: yerleşen [r,c] sırası, konum, tüm parçaların seçtiği konum, sealed/stuck/won."""
        st = (0, 0); out = []
        for j in seq:
            opts = self.options(st)
            res = self.place(st, j)
            entry = dict(piece=j, options=[None if o is None else [o['r'], o['c']] for o in opts])
            if res is None: entry['illegal'] = True; out.append(entry); break
            entry.update(placed=[[self.targets[t][0], self.targets[t][1]] for t in res['placed']], pos=[res['pos']['r'], res['pos']['c']],
                         sealed=bool(res['sealed']), stuck=bool(res['stuck']), won=bool(res['won']))
            out.append(entry); st = res['state']
            if res['sealed'] or res['stuck'] or res['won']: break
        return out

    # --- tam çözücü ---
    def analyse(self, limit=60000):
        memo = {}
        sys.setrecursionlimit(10000)
        L = self

        def rec(st):
            if st in memo: return memo[st]
            if len(memo) > limit: raise OverflowError('durum sayısı sınırı')
            legal = L.legal(st)
            wins = []; ptot = 0.0; nlegal = 0
            for j in legal:
                res = L.place(st, j)
                if res['won']: v = (True, 1.0, res)
                elif res['sealed'] or res['stuck']: v = (False, 0.0, res)
                else:
                    sub = rec(res['state']); v = (sub[0], sub[1], res)
                wins.append((j, v[0], v[1], res)); ptot += v[1]; nlegal += 1
            win = any(w[1] for w in wins)
            memo[st] = (win, (ptot / nlegal) if nlegal else 0.0, wins)
            return memo[st]
        root = rec((0, 0))
        return memo, root

    def stats(self):
        memo, root = self.analyse()
        # kazanan hatlar üzerindeki karar durumları
        seen = set(); stack = [(0, 0)]; dec = Counter(); delayed = 0; instant = 0
        while stack:
            st = stack.pop()
            if st in seen: continue
            seen.add(st)
            win, p, wins = memo[st]
            if not win: continue
            m = len(wins); w = sum(1 for x in wins if x[1])
            kind = 'FORCED' if m == 1 else ('FREE' if w == m else 'DECISION')
            dec[kind] += 1
            if kind == 'DECISION':
                for x in wins:
                    if not x[1]:
                        if x[3]['sealed'] or x[3]['stuck']: instant += 1
                        else: delayed += 1
            for x in wins:
                if x[1] and not x[3]['won']: stack.append(x[3]['state'])
        # basit sezgiseller
        def heur(key):
            st = (0, 0)
            while True:
                legal = self.legal(st)
                if not legal: return False
                opts = self.options(st)
                j = min(legal, key=lambda j: key(j, opts[j]))
                res = self.place(st, j)
                if res['won']: return True
                if res['sealed'] or res['stuck']: return False
                st = res['state']
        H = dict(nearest=heur(lambda j, o: (o['dmin'], o['dsum'], j)),
                 farthest=heur(lambda j, o: (-o['dmin'], -o['dsum'], j)),
                 biggest=heur(lambda j, o: (-len(self.pieces[j]['cells']), j)),
                 smallest=heur(lambda j, o: (len(self.pieces[j]['cells']), j)),
                 list_order=heur(lambda j, o: j))
        return dict(solvable=root[0], p_random=root[1], n_states=len(memo), decision_states=dec['DECISION'], free_states=dec['FREE'],
                    forced_states=dec['FORCED'], trap_instant=instant, trap_delayed=delayed, heuristics=H)


def shape_key(cells): return tuple(map(tuple, norm(cells)))


def free_shape_key(cells):
    best = None
    cur = [tuple(x) for x in cells]
    for _ in range(2):
        for _ in range(4):
            cur = [(c, -r) for r, c in cur]; k = tuple(norm(cur))
            if best is None or k < best: best = k
        cur = [(r, -c) for r, c in cur]
    return best


def make_vectors(levels, n_random=25, seed=7):
    """Parity vektörleri: kazanan dizi, hatalı/rasgele diziler; her adımda TÜM parçaların seçtiği konum dahil."""
    rng = random.Random(seed); out = []
    for lv in levels:
        L = PLevel(lv['grid'], lv['pieces']); memo, root = L.analyse(); cases = []
        if root[0]:
            st = (0, 0); seq = []
            while True:
                win, p, wins = memo[st]; ch = [x for x in wins if x[1]]
                x = rng.choice(ch); seq.append(x[0])
                if x[3]['won']: break
                st = x[3]['state']
            cases.append(dict(name='winning', sequence=seq))
        for k in range(n_random):   # rasgele yasal oyun (kazanır/kaybeder)
            st = (0, 0); seq = []
            while True:
                legal = L.legal(st)
                if not legal: break
                j = rng.choice(legal); seq.append(j); res = L.place(st, j)
                if res['won'] or res['sealed'] or res['stuck']: break
                st = res['state']
            cases.append(dict(name=f'random{k}', sequence=seq))
        cases.append(dict(name='illegal_repeat', sequence=[0, 0]))
        for c in cases: c['expected'] = L.simulate(c['sequence'])
        out.append(dict(level_id=lv['id'], grid=lv['grid'], pieces=lv['pieces'], cases=cases))
    return out


if __name__ == '__main__':
    lv = json.load(open(sys.argv[1]))
    lv = lv if isinstance(lv, list) else lv['levels']
    for l in lv:
        s = PLevel(l['grid'], l['pieces']).stats(); print(l['id'], json.dumps(s))
