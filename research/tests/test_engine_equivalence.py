"""Engine (one BFS per wave) must equal the naive box-by-box deepest-first implementation."""
import sys, random
from collections import deque
sys.path.insert(0, '..')
from puzzle_engine import Level, analyze

def naive_moves(grid, W):
    rows = grid.split('\n')
    T, E, floor = {}, [], set()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '#': continue
            if ch == 'E': E.append((r, c)); floor.add((r, c))
            elif ch == '.': floor.add((r, c))
            else: T[(r, c)] = ch
    cells = sorted(T)
    def dist(f):
        d = {}; q = deque()
        for e in E: d[e] = 0; q.append(e)
        while q:
            r, c = q.popleft()
            for n in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if n in d: continue
                if n in floor or (n in T and n not in f):
                    d[n] = d[(r, c)] + 1; q.append(n)
        return d
    def move(f0, col):
        f = set(f0); n = 0
        while n < W:
            d = dist(f)
            cand = [c for c in cells if T[c] == col and c not in f and c in d]
            if not cand: break
            b = max(cand, key=lambda c: (d[c], (-c[0], -c[1])))
            f.add(b); n += 1
        return frozenset(f) if n else None
    return cells, T, dist, move

def random_grid(rng):
    n, m = rng.randint(4, 7), rng.randint(4, 7)
    g = [['.'] * (m + 2) for _ in range(n + 2)]
    for r in range(n):
        for c in range(m):
            if rng.random() < 0.8: g[r+1][c+1] = rng.choice('ABC')
    g[rng.randrange(n+2)][0] = 'E'
    for r in range(n+2):
        for c in range(m+2):
            if g[r][c] == '.' and rng.random() < 0.3: g[r][c] = '#'
    g[rng.randrange(n+2)][0] = 'E'
    return '\n'.join(''.join(x) for x in g)

def main(trials=400):
    rng = random.Random(5)
    bad = 0
    for t in range(trials):
        g = random_grid(rng); W = rng.randint(1, 5)
        L = Level(g, W)
        if L.n == 0: continue
        cells, T, dist, move = naive_moves(g, W)
        letters = L.letters
        # walk a few random states and compare successor sets
        s_bits = 0; s_set = frozenset()
        for step in range(30):
            sealed, mv = L.info(s_bits)
            d = dist(s_set)
            nsealed = any(c not in s_set and c not in d for c in T)
            if sealed != nsealed: bad += 1; print('sealed mismatch', g, W); break
            if sealed: break
            mine = {}
            for k, tb in mv:
                mine[letters[k]] = frozenset(L.tpos[i] for i in range(L.n) if (tb >> i) & 1)
            ref = {}
            for k in letters:
                res = move(s_set, k)
                if res is not None: ref[k] = res
            if mine != ref: bad += 1; print('move mismatch', g, W); break
            if not mv: break
            k, tb = rng.choice(mv)
            s_bits = tb; s_set = mine[letters[k]]
    print('mismatches:', bad)
    assert bad == 0
if __name__ == '__main__':
    main()
