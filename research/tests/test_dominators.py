"""locked_mask (Cooper-Harvey-Kennedy dominators) must equal the brute-force definition:
u is a live bottleneck iff filling u alone makes some other unfilled target unreachable."""
import sys, random
sys.path.insert(0, '..')
from puzzle_engine import Level
from test_engine_equivalence import random_grid

def brute(L, s):
    d0 = L.bfs(s)
    mask = 0
    for u in range(L.n):
        if (s >> u) & 1 or d0[L.tnode[u]] < 0:
            continue
        d = L.bfs(s | (1 << u))
        if any((not ((s >> x) & 1)) and x != u and d[L.tnode[x]] < 0 for x in range(L.n)):
            mask |= 1 << u
    return mask

def main(trials=500):
    rng = random.Random(9); bad = 0; checked = 0
    for _ in range(trials):
        g = random_grid(rng)
        L = Level(g, 1)
        if L.n == 0: continue
        s = 0
        for step in range(6):
            sealed, mv = L.info(s)
            if sealed: break
            checked += 1
            if L.locked_mask(s) != brute(L, s):
                bad += 1; print('MISMATCH', g, bin(s)); break
            if not mv: break
            s = rng.choice(mv)[1]
    print('states checked', checked, 'mismatches', bad)
    assert bad == 0
if __name__ == '__main__':
    main()
