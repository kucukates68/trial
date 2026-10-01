"""block-image-01 — Python REFERANSI (src/engine.js ile birebir aynı kurallar) + kesin çözücü.

Kurallar
  * Izgara: 'E' giriş, '#' duvar (görünmez), '.' zemin (görünmez), harf = hedef hücre (resmin bir bloğu). 4-komşuluk. Yürünebilir = zemin + giriş + BOŞ hedef;
    dolan hedef kalıcı engel. Hedef indeksleri satır-ana sıradadır.
  * Parça = sabit geometrik blok (hücre listesi) ve resimdeki TEK hedefi (aynı hücreler). Oyuncu yalnız hangi parçayı göndereceğini seçer.
  * El: 3 slot, her birinin elle yazılmış sabit kuyruğu (parça id'leri). Gönderilen kartın yerine yalnız o slotun sıradaki parçası gelir.
  * Yerleşebilir ⇔ parçanın TÜM hedef hücreleri boş ve girişten erişilebilir.
  * place: hücreler en derinden başlayarak (uzaklık azalan, indeks) sıralanır; her hücre için rota = girişten BFS en kısa yol (parça başı BFS);
    sonra parça kalıcı engel olur. Sonra: sealed (boş hücre erişilemez) · stuck (hiçbir kart yerleşemez) · won (hepsi dolu).
"""
import json, heapq
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Level:
    def __init__(self, text, pieces, hand):
        rows = text.rstrip().split('\n'); self.h = len(rows); self.w = max(len(r) for r in rows); w, h = self.w, self.h
        self.kind = [0] * (w * h); self.entrances = []; tg = []
        for r in range(h):
            for c in range(w):
                ch = rows[r][c] if c < len(rows[r]) else '#'; i = r * w + c
                if ch == '#': self.kind[i] = 0
                elif ch == '.': self.kind[i] = 1
                elif ch == 'E': self.kind[i] = 2; self.entrances.append(i)
                else: self.kind[i] = 3; tg.append((r, c))
        self.tg = tg; self.n = len(tg); self.cell = [r * w + c for r, c in tg]; self.tof = {c: i for i, c in enumerate(self.cell)}
        self.nbr = [None] * (w * h)
        for i in range(w * h):
            if self.kind[i] == 0: continue
            r, c = divmod(i, w); L = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and self.kind[rr * w + cc] != 0: L.append(rr * w + cc)
            self.nbr[i] = L
        self.pieces = [dict(id=p['id'], cells=[self.tof[r * w + c] for r, c in p['cells']]) for p in pieces]
        self.pid = {p['id']: i for i, p in enumerate(self.pieces)}
        self.hand = [[self.pid[x] for x in q] for q in hand]
        assert sorted(t for p in self.pieces for t in p['cells']) == list(range(self.n)), 'parçalar resmi tam kaplamıyor'

    def new_state(self): return (bytes(self.n), tuple(0 for _ in self.hand))

    def bfs(self, fl, parent=False):
        w, h = self.w, self.h; blocked = bytearray(w * h)
        for t in range(self.n):
            if fl[t]: blocked[self.cell[t]] = 1
        dist = [-1] * (w * h); par = [-1] * (w * h) if parent else None; q = deque()
        for e in self.entrances: dist[e] = 0; q.append(e)
        while q:
            u = q.popleft(); du = dist[u] + 1
            for v in self.nbr[u]:
                if dist[v] < 0 and not blocked[v]:
                    dist[v] = du
                    if par is not None: par[v] = u
                    q.append(v)
        return dist, par

    def cards(self, st):
        fl, ptr = st; return [self.hand[s][ptr[s]] if ptr[s] < len(self.hand[s]) else None for s in range(len(self.hand))]

    def feasible(self, fl, pi, dist):
        return all(not fl[t] and dist[self.cell[t]] >= 0 for t in self.pieces[pi]['cells'])

    def options(self, st):
        fl, ptr = st; dist, _ = self.bfs(fl)
        return [None if c is None else self.feasible(fl, c, dist) for c in self.cards(st)]

    def place(self, st, slot):
        fl, ptr = st; c = self.cards(st)[slot]
        if c is None: return None
        dist, par = self.bfs(fl, True)
        if not self.feasible(fl, c, dist): return None
        order = sorted(self.pieces[c]['cells'], key=lambda t: (-dist[self.cell[t]], t)); steps = []
        for t in order:
            path = []; cur = self.cell[t]
            while cur >= 0: path.append(cur); cur = par[cur]
            path.reverse(); steps.append((t, path))
        f2 = bytearray(fl)
        for t in order: f2[t] = 1
        p2 = list(ptr); p2[slot] += 1; ns = (bytes(f2), tuple(p2)); d2, _ = self.bfs(f2)
        sealed = [t for t in range(self.n) if not f2[t] and d2[self.cell[t]] < 0]; won = all(f2); stuck = False
        if not won and not sealed:
            stuck = True
            for cc in self.cards(ns):
                if cc is not None and self.feasible(f2, cc, d2): stuck = False; break
        return dict(piece=c, cells=order, steps=steps, state=ns, sealed=sealed, won=won, stuck=stuck)

    def simulate(self, seq):
        st = self.new_state(); out = []
        for slot in seq:
            e = dict(slot=slot, cards=self.cards(st), legal=[bool(x) for x in self.options(st)])
            r = self.place(st, slot)
            if r is None: e['illegal'] = True; out.append(e); break
            e['cells'] = r['cells']; e['rlen'] = [len(p) for _, p in r['steps']]; e['rsig'] = route_sig(r['steps'])
            e['sealed'] = bool(r['sealed']); e['stuck'] = bool(r['stuck']); e['won'] = bool(r['won']); out.append(e); st = r['state']
            if e['sealed'] or e['stuck'] or e['won']: break
        return out

    def analyse(self):
        memo = {}
        def rec(st):
            if st in memo: return memo[st]
            moves = []
            for slot, c in enumerate(self.cards(st)):
                if c is None: continue
                r = self.place(st, slot)
                if r is None: continue
                if r['won']: moves.append((slot, True, 1.0, 1, 'won'))
                elif r['sealed'] or r['stuck']: moves.append((slot, False, 0.0, 0, 'sealed' if r['sealed'] else 'stuck'))
                else: sub = rec(r['state']); moves.append((slot, sub[0], sub[1], sub[2], 'cont', r['state']))
            win = any(m[1] for m in moves); p = sum(m[2] for m in moves) / len(moves) if moves else 0.0
            memo[st] = (win, p, sum(m[3] for m in moves), moves); return memo[st]
        return memo, rec(self.new_state())

    def stats(self):
        memo, root = self.analyse(); seen = set(); stack = [self.new_state()]; dec = free = forced = inst = delay = 0
        while stack:
            st = stack.pop()
            if st in seen: continue
            seen.add(st); win, p, cnt, moves = memo[st]
            if not win: continue
            m = len(moves); w = sum(1 for x in moves if x[1])
            if m == 1: forced += 1
            elif w == m: free += 1
            else:
                dec += 1
                for x in moves:
                    if not x[1]:
                        if x[4] in ('sealed', 'stuck'): inst += 1
                        else: delay += 1
            for x in moves:
                if x[1] and x[4] == 'cont': stack.append(x[5])
        return dict(solvable=bool(root[0]), p_random=round(root[1], 5), winning_orders=root[2], decision_states=dec, free_states=free, forced_states=forced, trap_instant=inst, trap_delayed=delay, n_states=len(memo))


def route_sig(steps):
    m = 1000000007; h = 0
    for _, route in steps:
        a = 0
        for i, c in enumerate(route): a = (a + c * (i + 1)) % m
        h = (h * 31 + a + len(route)) % m
    return h
