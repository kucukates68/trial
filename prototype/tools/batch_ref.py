"""GÖNDERİ (batch/dispatch) mekaniği — Python REFERANSI + kesin çözücü + CAT96 seviye üreticisi (yalnız bu seviye için elle kurulmuş veri).
engine.js `DLevel` ile birebir aynı kurallar:

  * Izgara: 'E' giriş, '#' duvar, '.' zemin, harf = hedef hücre (resmin dolu pikseli). 4-komşuluk; yürünebilir = zemin + giriş + BOŞ hedef.
    Dolan hedef kalıcı engel. Hedef indeksleri satır-ana sıradadır.
  * El: 3 slot; her slotun sabit kuyruğu [[bölge, k], ...]. Kart = gönderi (k adet). Gönderilen kartın yerine yalnız o slotun sıradaki gönderisi gelir.
  * choose_batch(fl, bölge, k): bölgedeki erişilebilir boş hücreler R. |R| < k ise YERLEŞEMEZ. Tohum = en derin (BFS uzaklığı en büyük, eşitlikte küçük indeks);
    tek bağlı bölge olarak büyüt: sınırdaki aday hücrelerden en derini (eşitlikte küçük indeks); sınır biterse yeni tohum = kalan en derin.
  * dispatch: seçilen k hücre en derinden başlayarak TEK TEK yerleşir; her yerleşmeden önce güncel tahtaya göre yeni BFS (rota), sonra hücre kalıcı engel.
    Sonra: sealed (boş hücre erişilemez) · stuck (kazanılmadı, kayıp yok, hiçbir kart yerleşemez) · won (hepsi dolu).
  Değişmez: en derinden başlayınca kalan gönderi hücrelerinin uzaklığı değişmez ⇒ hepsi erişilebilir kalır (dispatch bunu denetler).
  `dispatch_fast` (çözücü için) bu değişmeze dayanıp kümeyi tek seferde ekler; `check_equivalence` ikisinin aynı durumu verdiğini sınar.
"""
import json, os, sys, heapq, random
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class BLevel:
    def __init__(self, text, zones, hand):
        rows = text.rstrip().split('\n'); self.h = len(rows); self.w = max(len(r) for r in rows)
        w, h = self.w, self.h; self.kind = [0] * (w * h); self.entrances = []; tg = []
        for r in range(h):
            for c in range(w):
                ch = rows[r][c] if c < len(rows[r]) else '#'; i = r * w + c
                if ch == '#': self.kind[i] = 0
                elif ch == '.': self.kind[i] = 1
                elif ch == 'E': self.kind[i] = 2; self.entrances.append(i)
                else: self.kind[i] = 3; tg.append((r, c))
        tg.sort(); self.n = len(tg); self.tr = [t[0] for t in tg]; self.tc = [t[1] for t in tg]; self.cell = [r * w + c for r, c in tg]
        self.tof = {c: i for i, c in enumerate(self.cell)}
        assert len(zones) == self.n; self.zone = list(zones); self.hand = hand
        self.nbr = [None] * (w * h)     # yürünebilir hücrelerin yürünebilir komşuları (DIRS sırasıyla, JS ile aynı)
        for i in range(w * h):
            if self.kind[i] == 0: continue
            r, c = divmod(i, w); L = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and self.kind[rr * w + cc] != 0: L.append(rr * w + cc)
            self.nbr[i] = L
        self.tnb = []                    # hedef komşulukları (hedef indeksleri)
        for t in range(self.n):
            r, c = self.tr[t], self.tc[t]; L = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and (rr * w + cc) in self.tof: L.append(self.tof[rr * w + cc])
            self.tnb.append(L)

    def new_state(self): return (bytes(self.n), tuple(0 for _ in self.hand))

    def bfs(self, fl, parent=False):
        w, h = self.w, self.h; blocked = bytearray(w * h)
        for t in range(self.n):
            if fl[t]: blocked[self.cell[t]] = 1
        dist = [-1] * (w * h); par = [-1] * (w * h) if parent else None; q = deque()
        for e in self.entrances: dist[e] = 0; q.append(e)
        nbr = self.nbr
        while q:
            u = q.popleft(); du = dist[u] + 1
            for v in nbr[u]:
                if dist[v] < 0 and not blocked[v]:
                    dist[v] = du
                    if par is not None: par[v] = u
                    q.append(v)
        return dist, par

    def cards(self, st):
        fl, ptr = st; return [(self.hand[s][ptr[s]][0], self.hand[s][ptr[s]][1]) if ptr[s] < len(self.hand[s]) else None for s in range(len(self.hand))]

    def choose_batch(self, fl, zone, k, dist):
        R = [t for t in range(self.n) if not fl[t] and self.zone[t] == zone and dist[self.cell[t]] >= 0]
        if len(R) < k: return None
        inR = set(R); S = []; inS = set(); inF = set(); heap = []; cell = self.cell
        def expand(t):
            for nt in self.tnb[t]:
                if nt in inR and nt not in inS and nt not in inF: inF.add(nt); heapq.heappush(heap, (-dist[cell[nt]], nt))
        while len(S) < k:
            if heap: _, pick = heapq.heappop(heap)
            else: pick = min((t for t in R if t not in inS), key=lambda t: (-dist[cell[t]], t))
            inS.add(pick); S.append(pick); expand(pick)
        return S

    def options(self, st):
        fl, ptr = st; dist, _ = self.bfs(fl)
        return [None if c is None else self.choose_batch(fl, c[0], c[1], dist) for c in self.cards(st)]

    def sealed(self, fl, dist=None):
        if dist is None: dist, _ = self.bfs(fl)
        return [t for t in range(self.n) if not fl[t] and dist[self.cell[t]] < 0]

    def _finish(self, st, slot, sel, fl2):
        fl, ptr = st; p2 = list(ptr); p2[slot] += 1; ns = (bytes(fl2), tuple(p2))
        dist, _ = self.bfs(fl2); sealed = self.sealed(fl2, dist); won = all(fl2)
        stuck = False
        if not won and not sealed:
            stuck = True
            for c in self.cards(ns):
                if c is not None and self.choose_batch(fl2, c[0], c[1], dist) is not None: stuck = False; break
        return ns, sealed, won, stuck

    def dispatch(self, st, slot):
        """LİTERAL hücre-hücre yerleşme (her adımda yeni BFS). Döner: dict veya None (yerleşemez)."""
        fl, ptr = st; cards = self.cards(st); c = cards[slot]
        if c is None: return None
        dist0, _ = self.bfs(fl); sel = self.choose_batch(fl, c[0], c[1], dist0)
        if sel is None: return None
        order = sorted(sel, key=lambda t: (-dist0[self.cell[t]], t)); f = bytearray(fl); steps = []
        for t in order:
            dist, par = self.bfs(f, True); assert dist[self.cell[t]] >= 0, 'değişmez ihlali'
            path = []; cur = self.cell[t]
            while cur >= 0: path.append(cur); cur = par[cur]
            path.reverse(); steps.append((t, path)); f[t] = 1
        ns, sealed, won, stuck = self._finish(st, slot, sel, f)
        return dict(card=c, selection=sel, cells=order, steps=steps, state=ns, sealed=sealed, won=won, stuck=stuck)

    def dispatch_fast(self, st, slot):
        fl, ptr = st; c = self.cards(st)[slot]
        if c is None: return None
        dist0, _ = self.bfs(fl); sel = self.choose_batch(fl, c[0], c[1], dist0)
        if sel is None: return None
        f = bytearray(fl)
        for t in sel: f[t] = 1
        ns, sealed, won, stuck = self._finish(st, slot, sel, f)
        return dict(card=c, selection=sel, state=ns, sealed=sealed, won=won, stuck=stuck)

    def simulate(self, seq):
        st = self.new_state(); out = []
        for slot in seq:
            cards = self.cards(st); opts = self.options(st)
            e = dict(slot=slot, cards=[None if c is None else [c[0], c[1]] for c in cards], legal=[o is not None for o in opts])
            r = self.dispatch(st, slot)
            if r is None: e['illegal'] = True; out.append(e); break
            e['cells'] = r['cells']; e['rlen'] = [len(p) for _, p in r['steps']]; e['rsig'] = route_sig(r['steps'])
            e['sealed'] = bool(r['sealed']); e['stuck'] = bool(r['stuck']); e['won'] = bool(r['won']); out.append(e); st = r['state']
            if e['sealed'] or e['stuck'] or e['won']: break
        return out

    # ---- kesin çözücü: durum = (kuyruk işaretçileri, dolu maske)
    def analyse(self):
        memo = {}
        def rec(st):
            if st in memo: return memo[st]
            moves = []
            for slot, c in enumerate(self.cards(st)):
                if c is None: continue
                r = self.dispatch_fast(st, slot)
                if r is None: continue
                if r['won']: moves.append((slot, True, 1.0, 1, 'won'))
                elif r['sealed'] or r['stuck']: moves.append((slot, False, 0.0, 0, 'sealed' if r['sealed'] else 'stuck'))
                else:
                    sub = rec(r['state']); moves.append((slot, sub[0], sub[1], sub[2], 'cont', r['state']))
            win = any(m[1] for m in moves); p = sum(m[2] for m in moves) / len(moves) if moves else 0.0
            memo[st] = (win, p, sum(m[3] for m in moves), moves); return memo[st]
        return memo, rec(self.new_state())

    def stats(self):
        memo, root = self.analyse(); st0 = self.new_state(); seen = set(); stack = [st0]; dec = free = forced = inst = delay = 0
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
        return dict(solvable=bool(root[0]), p_random=round(root[1], 5), winning_orders=root[2], decision_states=dec, free_states=free, forced_states=forced,
                    trap_instant=inst, trap_delayed=delay, n_states=len(memo))


def route_sig(steps):
    m = 1000000007; h = 0
    for _, route in steps:
        a = 0
        for i, c in enumerate(route): a = (a + c * (i + 1)) % m
        h = (h * 31 + a + len(route)) % m
    return h


def check_equivalence(L, rng, trials=12):
    """literal hücre-hücre yerleşme = tek seferde ekleme (çözücünün hızlı yolu) — rasgele durumlarda sınanır"""
    st = L.new_state(); n_ok = 0
    for _ in range(trials * 8):
        slots = [s for s, o in enumerate(L.options(st)) if o is not None]
        if not slots: break
        s = rng.choice(slots); a = L.dispatch(st, s); b = L.dispatch_fast(st, s)
        assert a['state'] == b['state'] and a['sealed'] == b['sealed'] and a['stuck'] == b['stuck'] and a['won'] == b['won'], 'hızlı yol literal yoldan farklı'
        n_ok += 1
        if a['sealed'] or a['won'] or a['stuck']: st = L.new_state()
        else: st = a['state']
    return n_ok
