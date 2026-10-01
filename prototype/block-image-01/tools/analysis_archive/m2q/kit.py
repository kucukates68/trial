import sys, itertools, collections
sys.path.insert(0, '/home/user/trial/prototype/block-image-01/tools/lab')
from labkit import Board, Analysis
# Kemer silüeti: halka sırası (girişe bitişik sol ayaktan sağ ayağa)
RING = [(2,1),(1,1),(0,1),(0,2),(0,3),(1,3),(2,3)]
def board_for(partition):
    """partition: segment uzunlukları (toplam 7) → parça harfleri a,b,c... halka sırasına göre"""
    g = [list('#####'), list('#####'), list('#####')]
    letters = 'abcdefg'; i = 0; names = []
    for si, ln in enumerate(partition):
        for _ in range(ln):
            r, c = RING[i]; g[r][c] = letters[si]; i += 1
        names.append(letters[si])
    g[2][2] = 'E'
    return Board([''.join(x) for x in g]), names
def compositions(n, k):
    for cuts in itertools.combinations(range(1, n), k - 1):
        yield [b - a for a, b in zip((0,) + cuts, cuts + (n,))]
def assignments(names):
    n = len(names)
    seen = set()
    for pm in itertools.permutations(names):
        for comp in compositions(n, 3):
            q = []; i = 0
            for ln in comp: q.append(list(pm[i:i+ln])); i += ln
            key = tuple(sorted(tuple(x) for x in q))
            if key in seen: continue
            seen.add(key); yield q
def dist_map(B, mask):
    from collections import deque
    d = {B.E: 0}; q = deque([B.E])
    while q:
        p = q.popleft()
        for r in B.nb(p):
            if r in d: continue
            o = B.owner.get(r)
            if o is not None and mask >> o & 1: continue
            d[r] = d[p] + 1; q.append(r)
    return d
def depth(B, mask, piece):
    d = dist_map(B, mask); return max(d.get(p, 99) for p in B.cells[B.names[piece]])
