"""Access geometry: where workers can enter and how the plaza around the picture is walled.

Picture sits at offset 2 in a (h+4) x (w+4) plaza.  Ring cells adjacent to the picture are floor
only where a *port* opens them; every port has an 'E' gate directly outside.  Options per side:
  WIDE  whole side           HA/HB  first / second half      DA/DB  single door at ~30% / ~70%
OPEN = every outside cell is an entrance (full open plaza).
"""
from __future__ import annotations

FAMILY = {}
LAYOUTS = {
    'OPEN': {},
    # one wide front
    'COR1': {'B': 'WIDE'}, 'COR2': {'L': 'WIDE'}, 'COR3': {'T': 'HA'},
    # single door
    'BOT1': {'B': 'DA'}, 'BOT2': {'T': 'DB'}, 'BOT3': {'L': 'DA'},
    # two wide fronts
    'SPL1': {'T': 'WIDE', 'B': 'WIDE'}, 'SPL2': {'L': 'WIDE', 'R': 'WIDE'}, 'SPL3': {'T': 'HA', 'B': 'HB'},
    # two doors
    'SPB1': {'T': 'DA', 'B': 'DB'}, 'SPB2': {'L': 'DA', 'R': 'DB'}, 'SPB3': {'T': 'DA', 'R': 'DA'},
    # 3-4 ports (multi-entry)
    'MUL1': {'T': 'HA', 'B': 'DB', 'L': 'HB', 'R': 'DB'},
    'MUL2': {'T': 'DA', 'B': 'DA', 'L': 'DB', 'R': 'HA'},
    'MUL3': {'T': 'WIDE', 'B': 'WIDE', 'L': 'HB', 'R': 'HA'},
    'MUL4': {'B': 'WIDE', 'L': 'DA', 'R': 'DB'},
    'MUL5': {'T': 'DA', 'B': 'HA', 'L': 'DA'},
}
for k in LAYOUTS:
    FAMILY[k] = {'OPEN': 'OPEN', 'COR': 'CORRIDOR', 'BOT': 'BOTTLENECK', 'SPL': 'SPLIT',
                 'SPB': 'SPLIT+BOTTLENECK', 'MUL': 'MULTI'}[k[:3] if k != 'OPEN' else 'OPEN']
FAMILY_ORDER = ['OPEN', 'CORRIDOR', 'BOTTLENECK', 'SPLIT', 'SPLIT+BOTTLENECK', 'MULTI']
ONE_PER_FAMILY = ['OPEN', 'COR1', 'BOT1', 'SPL1', 'SPB1', 'MUL1']
_WIDTHS = {'WIDE': 8, 'HA': 4, 'HB': 4, 'DA': 1, 'DB': 1}


def get_ports(layout: str) -> dict:
    """named layouts (OPEN, COR1, ...) or generic 'P:TWIDE,BDA' strings."""
    if layout in LAYOUTS:
        return LAYOUTS[layout]
    return {p[0]: p[1:] for p in layout[2:].split(',')}


def layout_name(ports: dict) -> str:
    if not ports:
        return 'OPEN'
    return 'P:' + ','.join(f'{s}{o}' for s, o in sorted(ports.items(), key=lambda kv: 'TBLR'.index(kv[0])))


def family_of(layout: str) -> str:
    if layout in FAMILY:
        return FAMILY[layout]
    ports = get_ports(layout)
    ws = [_WIDTHS[o] for o in ports.values()]
    if len(ws) == 1:
        return 'CORRIDOR' if ws[0] >= 4 else 'BOTTLENECK'
    if len(ws) == 2:
        return 'SPLIT+BOTTLENECK' if all(w == 1 for w in ws) else 'SPLIT'
    return 'MULTI'


def neighbours(layout: str):
    """all layouts that differ from `layout` in exactly one side's option."""
    base = dict(get_ports(layout))
    out = []
    for side in 'TBLR':
        for opt in ['N', 'WIDE', 'HA', 'HB', 'DA', 'DB']:
            cur = base.get(side, 'N')
            if opt == cur:
                continue
            d = dict(base)
            if opt == 'N':
                d.pop(side, None)
            else:
                d[side] = opt
            if d:
                out.append(layout_name(d))
    return out


def _spans(n):
    da = int(n * 0.3)
    db = n - 1 - da
    return {'N': [], 'WIDE': list(range(n)), 'HA': list(range(n // 2)),
            'HB': list(range(n // 2, n)), 'DA': [da], 'DB': [db]}


def build_grid(colors: dict, layout: str, letters='ABCD') -> str:
    """colors: dict (r,c)->label int; returns grid string with plaza + gates."""
    r0 = min(r for r, c in colors); c0 = min(c for r, c in colors)
    cells = {(r - r0, c - c0): v for (r, c), v in colors.items()}
    h = max(r for r, c in cells) + 1
    w = max(c for r, c in cells) + 1
    H, Wd = h + 4, w + 4
    G = [['#'] * Wd for _ in range(H)]
    for (r, c), v in cells.items():
        G[r + 2][c + 2] = letters[v]
    # picture's own empty cells inside bbox are floor (plaza notches)
    for r in range(h):
        for c in range(w):
            if (r, c) not in cells:
                G[r + 2][c + 2] = '.'
    ports = get_ports(layout)
    if layout == 'OPEN':
        for r in range(H):
            for c in range(Wd):
                if G[r][c] == '#':
                    G[r][c] = 'E' if (r in (0, H - 1) or c in (0, Wd - 1)) else '.'
        return '\n'.join(''.join(x) for x in G)
    for side, opt in ports.items():
        n = w if side in 'TB' else h
        for p in _spans(n)[opt]:
            k = p + 2
            if side == 'T': G[1][k] = '.'; G[0][k] = 'E'
            if side == 'B': G[H - 2][k] = '.'; G[H - 1][k] = 'E'
            if side == 'L': G[k][1] = '.'; G[k][0] = 'E'
            if side == 'R': G[k][Wd - 2] = '.'; G[k][Wd - 1] = 'E'
    return '\n'.join(''.join(x) for x in G)
