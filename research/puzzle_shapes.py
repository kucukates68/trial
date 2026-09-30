"""Geometry only: silhouette masks (no colours) and synthetic square pictures.

A mask is a frozenset of (row, col) cells.  Colours are assigned separately by puzzle_colormaps.
"""
from __future__ import annotations
import math


def _canvas(h, w):
    return [[0] * w for _ in range(h)]


def _rect(g, r0, c0, r1, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if 0 <= r < len(g) and 0 <= c < len(g[0]):
                g[r][c] = 1


def _ell(g, cr, cc, rr, rc):
    for r in range(len(g)):
        for c in range(len(g[0])):
            if ((r - cr) / rr) ** 2 + ((c - cc) / rc) ** 2 <= 1.0:
                g[r][c] = 1


def _pts(g, L):
    for r, c in L:
        if 0 <= r < len(g) and 0 <= c < len(g[0]):
            g[r][c] = 1


def _tri(g, top, c, h):
    for i in range(h):
        _rect(g, top + i, c - i, top + i, c + i)


def _mask(g):
    return frozenset((r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c])


def _norm(mask):
    r0 = min(r for r, c in mask); c0 = min(c for r, c in mask)
    return frozenset((r - r0, c - c0) for r, c in mask)


def cat():
    rows = [".XX..XX.", ".XXXXXX.", "XXXXXXXX", "XXXXXXXX", "XXXXXXXX", "XXXXXXXX", ".XXXXXX.", ".XXXXXX."]
    return _norm(frozenset((r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'X'))


def bird():
    g = _canvas(9, 12)
    _ell(g, 4, 5, 3, 4.2); _ell(g, 4.5, 4, 1.6, 2.6)
    _pts(g, [(3, 9), (3, 10), (4, 9), (3, 7)])
    _pts(g, [(5, 0), (5, 1), (6, 0), (6, 1), (6, 2), (4, 1)])
    _pts(g, [(7, 4), (8, 4), (7, 6), (8, 6)])
    return _norm(_mask(g))


def tree():
    g = _canvas(13, 9)
    _ell(g, 4, 4, 4, 4.2)
    _rect(g, 8, 4, 12, 5); _pts(g, [(12, 3), (12, 6)])
    return _norm(_mask(g))


def human():
    g = _canvas(14, 9)
    _ell(g, 2.5, 4, 2.5, 2.4); _rect(g, 0, 3, 0, 5); _pts(g, [(1, 2), (1, 6)])
    _rect(g, 5, 2, 9, 6); _rect(g, 5, 7, 8, 7); _pts(g, [(5, 1), (4, 1), (3, 1), (2, 0), (1, 0)])
    _rect(g, 10, 2, 13, 3); _rect(g, 10, 5, 13, 6)
    return _norm(_mask(g))


def car():
    g = _canvas(8, 14)
    _rect(g, 3, 0, 5, 13); _rect(g, 1, 3, 2, 10)
    _ell(g, 6, 3, 1.6, 1.6); _ell(g, 6, 10, 1.6, 1.6); _pts(g, [(3, 13), (4, 13)])
    return _norm(_mask(g))


def house():
    g = _canvas(12, 12)
    _rect(g, 5, 1, 10, 10); _tri(g, 1, 5, 4); _pts(g, [(4, 6), (4, 7), (4, 8), (4, 9)]); _rect(g, 1, 8, 2, 9)
    return _norm(_mask(g))


def rabbit():
    g = _canvas(16, 9)
    _rect(g, 0, 2, 5, 3); _rect(g, 0, 5, 5, 6)
    _ell(g, 8, 4, 3, 3.2); _ell(g, 12, 4, 3, 4.2)
    _pts(g, [(15, 1), (15, 2), (15, 6), (15, 7), (15, 4), (12, 8), (11, 8)])
    return _norm(_mask(g))


def landscape():
    """multi-part scene: ground strip + small house + tree + sun (~100 cells)."""
    g = _canvas(10, 16)
    _rect(g, 8, 0, 9, 15)
    _rect(g, 4, 1, 7, 6); _tri(g, 1, 3, 3)
    _ell(g, 4, 12, 3, 3.2); _pts(g, [(7, 12), (6, 12)])
    _ell(g, 1.5, 14.5, 1.1, 1.3)
    return _norm(_mask(g))


SILHOUETTES = {'cat': cat, 'bird': bird, 'human': human, 'car': car,
               'tree': tree, 'house': house, 'rabbit': rabbit, 'landscape': landscape}


def silhouette(name):
    return SILHOUETTES[name]()


def scale_mask_colors(colors: dict, s: int) -> dict:
    """nearest-neighbour upscale of a coloured picture (dict cell->label) by integer s."""
    out = {}
    for (r, c), v in colors.items():
        for i in range(s):
            for j in range(s):
                out[(r * s + i, c * s + j)] = v
    return out


# ------------------------------------------------------------ synthetic square pictures
def _square(n, m=None):
    m = m or n
    return [(r, c) for r in range(n) for c in range(m)]


def synthetic(name: str, n: int = 8, k: int = 3, seed: int = 0):
    """returns dict cell->label (0..k-1) on an n x n square."""
    import random
    rng = random.Random(seed)
    cells = _square(n)
    lab = {}
    if name == 'rows3':                # horizontal bands (AAAA/BBBB/CCCC)
        for r, c in cells: lab[(r, c)] = min(k - 1, r * k // n)
    elif name == 'cols3':
        for r, c in cells: lab[(r, c)] = min(k - 1, c * k // n)
    elif name == 'rings':              # concentric, outer->inner
        for r, c in cells:
            d = min(r, c, n - 1 - r, n - 1 - c)
            lab[(r, c)] = min(k - 1, d * k // (n // 2))
    elif name == 'rings_alt':          # alternating concentric layers
        for r, c in cells:
            d = min(r, c, n - 1 - r, n - 1 - c)
            lab[(r, c)] = d % k
    elif name == 'checker3':           # every neighbour differs
        for r, c in cells: lab[(r, c)] = (r + 2 * c) % k
    elif name == 'diag3':
        for r, c in cells: lab[(r, c)] = (r + c) % k
    elif name == 'quadrants':          # AABB/AABB/CCAA/CCAA style
        h = n // 2
        q = {(0, 0): 0, (0, 1): 1, (1, 0): 2 % k, (1, 1): 0}
        for r, c in cells: lab[(r, c)] = q[(r // h, c // h)]
    elif name == 'tiles2':             # 2x2 tiles cycling
        for r, c in cells: lab[(r, c)] = ((r // 2) + 2 * (c // 2)) % k
    elif name == 'rows_alt':           # alternating rows (high depth alternation for bottom entrance)
        for r, c in cells: lab[(r, c)] = r % k
    elif name == 'sandwich':           # A outside, B middle band, A inside core, C tiny
        for r, c in cells:
            d = min(r, c, n - 1 - r, n - 1 - c)
            lab[(r, c)] = 0 if d == 0 else (1 if d == 1 else (0 if d == 2 else k - 1))
    elif name.startswith('mrf'):       # clustered random: smoothing passes; mrf0 = iid
        passes = int(name[3:] or 0)
        for r, c in cells: lab[(r, c)] = rng.randrange(k)
        for _ in range(passes):
            new = {}
            for r, c in cells:
                votes = [0] * k
                votes[lab[(r, c)]] += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (r + dr, c + dc) in lab: votes[lab[(r + dr, c + dc)]] += 1
                mx = max(votes)
                new[(r, c)] = rng.choice([i for i, v in enumerate(votes) if v == mx])
            lab = new
    else:
        raise KeyError(name)
    return lab


SYNTH_NAMES = ['rows3', 'cols3', 'rings', 'rings_alt', 'checker3', 'diag3', 'quadrants', 'tiles2',
               'rows_alt', 'sandwich', 'mrf0', 'mrf1', 'mrf3', 'mrf8']
