"""DENEY ALANI (yeni mekanik/UI yok): küçük tahtalarda "seçimin geleceği değiştirmesi" arayan kit.
Kurallar mevcut oyunla aynı: parça yerleşir ⇔ tüm hücreleri boş ve girişten erişilebilir; yerleşen hücre kalıcı engel; boş hedef erişilemez olursa kayıp (mühür).
Şablon: ASCII ('#' duvar, '.' zemin, 'E' giriş, harf = parça). Hızlı değerlendirici: ptr-durum DP + güvenli(maske,parça) önbelleği."""
import itertools, functools, sys
class Board:
    def __init__(self, rows):
        self.rows = [r for r in rows]; self.h = len(rows); self.w = len(rows[0]); self.cells = {}; self.E = None; self.wall = set()
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == 'E': self.E = (r, c)
                elif ch == '#': self.wall.add((r, c))
                elif ch != '.': self.cells.setdefault(ch, []).append((r, c))
        self.names = sorted(self.cells); self.n = len(self.names); self.idx = {k: i for i, k in enumerate(self.names)}
        self.owner = {}
        for k, cs in self.cells.items():
            for p in cs: self.owner[p] = self.idx[k]
        self.full = (1 << self.n) - 1; self.size = {k: len(v) for k, v in self.cells.items()}
        self._safe = {}; self._reach = {}
    def nb(self, p):
        r, c = p
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (r + dr, c + dc)
            if 0 <= q[0] < self.h and 0 <= q[1] < self.w and q not in self.wall: yield q
    def reach(self, mask):
        if mask in self._reach: return self._reach[mask]
        seen = {self.E}; st = [self.E]
        while st:
            p = st.pop()
            for q in self.nb(p):
                if q in seen: continue
                o = self.owner.get(q)
                if o is not None and mask >> o & 1: continue
                seen.add(q); st.append(q)
        self._reach[mask] = seen; return seen
    def safe(self, mask, i):
        """i yerleşirse: 'seal' (boş hedef erişilemez olur) / 'safe' / 'won'"""
        k = (mask, i)
        if k in self._safe: return self._safe[k]
        m2 = mask | 1 << i; R = self.reach(m2)
        if m2 == self.full: res = 'won'
        else:
            res = 'safe'
            for p, o in self.owner.items():
                if not (m2 >> o & 1) and p not in R: res = 'seal'; break
        self._safe[k] = res; return res
class Analysis:
    def __init__(self, B, queues):
        self.B = B; self.Q = [[B.idx[x] for x in q] for q in queues]; self.memo = {}; self.start = (0, 0, 0)
        self.rec(self.start, 0)
    def heads(self, ptr): return [q[p] if p < len(q) else None for q, p in zip(self.Q, ptr)]
    def moves(self, ptr, mask):
        out = []
        for s, h in enumerate(self.heads(ptr)):
            if h is None: continue
            out.append((s, h, self.B.safe(mask, h)))
        return out
    def rec(self, ptr, mask):
        k = ptr
        if k in self.memo: return self.memo[k]
        win = False; cnt = 0; mv = []
        for s, h, kind in self.moves(ptr, mask):
            if kind == 'won': mv.append((s, h, kind, True, 1, None)); win = True; cnt += 1
            elif kind == 'seal': mv.append((s, h, kind, False, 0, None))
            else:
                p2 = list(ptr); p2[s] += 1; p2 = tuple(p2); sub = self.rec(p2, mask | 1 << h); mv.append((s, h, kind, sub[0], sub[1], p2)); win |= sub[0]; cnt += sub[1]
        self.memo[k] = (win, cnt, mv, mask); return self.memo[k]
    def mask_of(self, ptr):
        m = 0
        for q, p in zip(self.Q, ptr):
            for x in q[:p]: m |= 1 << x
        return m
    def reachable(self):
        seen = {}; st = [self.start]
        while st:
            p = st.pop()
            if p in seen: continue
            seen[p] = 1
            for mv in self.memo[p][2]:
                if mv[5] is not None: st.append(mv[5])
        return list(seen)
    def lag(self, ptr):
        """kayıp durumdan terminal mühüre min hamle"""
        cache = self.__dict__.setdefault('_c_' + sys._getframe().f_code.co_name, {}); key = ptr
        if key in cache: return cache[key]
        best = 99
        for mv in self.memo[ptr][2]:
            if mv[5] is None: best = min(best, 1)
            else: best = min(best, 1 + self.lag(mv[5]))
        cache[key] = best; return best
    def surv(self, ptr):
        cache = self.__dict__.setdefault('_c_' + sys._getframe().f_code.co_name, {}); key = ptr
        if key in cache: return cache[key]
        best = 0
        for mv in self.memo[ptr][2]:
            if mv[5] is not None: best = max(best, 1 + self.surv(mv[5]))
        cache[key] = best; return best
    def sw(self, ptr):
        cache = self.__dict__.setdefault('_c_' + sys._getframe().f_code.co_name, {}); key = ptr
        if key in cache: return cache[key]
        mv = [m for m in self.memo[ptr][2] if m[2] != 'seal']
        if not mv: r = 0.0
        else: r = sum((1.0 if m[2] == 'won' else self.sw(m[5])) for m in mv) / len(mv)
        cache[key] = r; return r
    def features(self):
        B = self.B; R = self.reachable(); root = self.memo[self.start]
        f = dict(solvable=root[0], orders=root[1])
        if not root[0]: return f
        mv0 = root[2]; f['start_safe'] = sum(1 for m in mv0 if m[2] != 'seal'); f['start_moves'] = len(mv0)
        f['start_win_moves'] = sum(1 for m in mv0 if m[3])
        # kapanma haritası: slot m gönderilince başka bir slotun başı güvenli iken güvensiz oluyor mu
        def closes(ptr, mask, s_move):
            sm = self.moves(ptr, mask); base = {s: k for s, h, k in sm}
            m = [x for x in self.memo[ptr][2] if x[0] == s_move][0]
            if m[5] is None: return None
            sm2 = self.moves(m[5], mask | 1 << m[1]); after = {s: k for s, h, k in sm2}
            return {s for s in base if s != s_move and base[s] != 'seal' and after.get(s) == 'seal'}
        f['start_closes'] = {m[0]: sorted(closes(self.start, 0, m[0]) or []) for m in mv0 if m[2] != 'seal'}
        infl = fork = delayed = 0; lagmin = 99; lags = []; survs = []; ex = None
        for p in R:
            win, cnt, mv, mask = self.memo[p]
            if not win: continue
            safes = [m for m in mv if m[2] != 'seal']
            if len(safes) >= 2:
                cl = [tuple(sorted(closes(p, mask, m[0]) or [])) for m in safes]
                if len(set(cl)) > 1: infl += 1
                if any(m[3] for m in safes) and any(not m[3] for m in safes):
                    fork += 1; delayed += sum(1 for m in safes if not m[3])
                    for m in safes:
                        if m[3]: continue
                        lg = self.lag(m[5]); lags.append(lg); lagmin = min(lagmin, lg); sv = self.surv(m[5]); survs.append(sv)
                        if ex is None or sv > ex[0]: ex = (sv, p, m[0], m[1])
        f.update(states=len(R), infl=infl, fork=fork, delayed=delayed, lagmin=(lagmin if lagmin < 99 else None), deep=sum(1 for x in lags if x >= 2), lags=sorted(lags), surv_max=max(survs) if survs else 0, deepsurv=sum(1 for x in survs if x >= 2), example=ex, safe_win=self.sw(self.start), midsurv=sum(1 for x in survs if 1 <= x <= 3))
        return f
