"""Kazanan hatlar boyunca 'anlamlı karar' sayısı: bir adımda en az bir kart kazandırırken en az biri kaybettiriyorsa karar."""
import sys, json, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_level as M
from ref import Level
def measure(pattern, runs=400, seed=1):
    seed_, pieces = M.build(); order = M.valid_order(None, pieces); pats = M.patterns(pieces, order)
    hand = [[pieces[j]['id'] for j in q] for q in pats[pattern]]; L = Level(M.GRID, pieces, hand); memo, root = L.analyse(); rng = random.Random(seed); res = []
    for _ in range(runs):
        st = L.new_state(); dec = 0; first = None; k = 0
        while True:
            win, p, cnt, moves = memo[st]; good = [m for m in moves if m[1]]; bad = [m for m in moves if not m[1]]
            if good and bad:
                dec += 1
                if first is None: first = k
            m = rng.choice(good); k += 1
            if m[4] == 'won': break
            st = m[5]
        res.append((dec, first))
    return sum(d for d, f in res) / runs, min(d for d, f in res), max(d for d, f in res), sum(f for d, f in res if f is not None) / max(1, sum(1 for d, f in res if f is not None))
if __name__ == '__main__':
    for p in ('anatomy', 'round_robin', 'thirds', 'blocks2'): print(p, 'ort. karar / min / max / ilk karar adımı:', measure(p))
