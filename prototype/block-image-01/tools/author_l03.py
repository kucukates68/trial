"""L03 — AĞAÇ (orta). Taç = yaprak kümeleri (en yakın tohum), elmalar = cep, çatallı dal, gövde = tek geçit, kökler, çalılar, zemin. Mekanik değişmez."""
import json, math
from lvlkit import *
cv = Canvas(); cv.entrance = (18, 24)
HEX = dict(leaf_a='#58a63f', leaf_b='#3f8a31', leaf_c='#6bb84c', leaf_d='#347a2b', apple_a='#d8362f', apple_b='#b52a26', branch_a='#7b4a24', branch_b='#6a3f1f', trunk_a='#8a5a2b', trunk_b='#7a4c22', root='#5e3a1c',
           bush_a='#2f7a35', bush_b='#3f8f3f', grass_a='#6fb34f', grass_b='#5da042', soil='#7a5a3a', rock='#9a9a9a')
canopy = {1: (12, 23), 2: (8, 27), 3: (6, 29), 4: (4, 31), 5: (3, 32), 6: (2, 33), 7: (2, 33), 8: (2, 33), 9: (2, 33), 10: (2, 33), 11: (3, 32), 12: (4, 31), 13: (6, 29), 14: (9, 26), 15: (12, 23)}
cells = [(x, y) for y, (x0, x1) in canopy.items() for x in range(x0, x1 + 1)]
seeds = []
for k in range(10):                                  # dış halka
    a = 2 * math.pi * (k + 0.5) / 10; seeds.append((17.5 + 13.3 * math.cos(a), 8 + 6.4 * math.sin(a)))
for k in range(6):                                   # iç halka
    a = 2 * math.pi * (k + 0.25) / 6; seeds.append((17.5 + 7.2 * math.cos(a), 8 + 3.4 * math.sin(a)))
seeds += [(14.5, 8.5), (21.0, 7.5)]                  # merkez
names = ['TOP_L', 'TOP_R', 'TOP_RR', 'EDGE_R', 'BOT_R', 'BOT_C', 'BOT_L', 'EDGE_L', 'TOP_LL', 'TOP_C']
for i, s in enumerate(seeds):
    pass
SH = ['leaf_a', 'leaf_b', 'leaf_c', 'leaf_d']
def cl(i): return 'LEAF_%02d' % (i + 1)
for (x, y) in cells:
    best = min(range(len(seeds)), key=lambda i: (x - seeds[i][0]) ** 2 + ((y - seeds[i][1]) * 1.25) ** 2); cv.own[(x, y)] = cl(best)
for i in range(len(seeds)): cv.color[cl(i)] = SH[i % 4]; cv.order.append(cl(i))
# dallar (taç içinde)
def line(p0, p1, th):
    out = set(); n = 60
    for i in range(n + 1):
        t = i / n; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        for dx in range(-th, th + 1):
            for dy in range(-th, th + 1):
                if dx * dx + dy * dy <= th * th + 0.5: out.add((int(round(x)) + dx, int(round(y)) + dy))
    return [p for p in out if p in cv.own]
def arm(p0, p1):
    out = set()
    for i in range(41):
        t = i / 40; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t; out.add((int(round(x)), int(round(y)))); out.add((int(round(x)) + 1, int(round(y))))
    return [p for p in out if p in cv.own]
cv.piece('BRANCH_STEM', 'branch_a', [(x, y) for x in range(16, 20) for y in range(13, 16) if (x, y) in cv.own])
cv.piece('BRANCH_L', 'branch_b', [p for p in arm((16, 12), (10, 8)) if p[1] <= 12])
cv.piece('BRANCH_R', 'branch_b', [p for p in arm((18, 12), (24, 8)) if p[1] <= 12])
# elmalar (cep)
for nm, (ax, ay), c in (('APPLE_1', (9, 5), 'apple_a'), ('APPLE_2', (25, 4), 'apple_b'), ('APPLE_3', (13, 10), 'apple_b'), ('APPLE_4', (22, 11), 'apple_a'), ('APPLE_5', (28, 9), 'apple_a')):
    cv.piece(nm, c, [(ax + dx, ay + dy) for dx in (0, 1) for dy in (0, 1)])
# gövde / kökler / çalılar / zemin
cv.rect('TRUNK_TOP', 'trunk_a', 15, 16, 20, 17); cv.rect('TRUNK_MID', 'trunk_b', 15, 18, 20, 19); cv.rect('ROOTS', 'root', 13, 20, 22, 21)
cv.rect('BUSH_L', 'bush_a', 6, 19, 11, 21); cv.rect('BUSH_R', 'bush_b', 24, 19, 29, 21)
cv.rect('GROUND_L', 'grass_a', 4, 22, 15, 23); cv.rect('GROUND_R', 'grass_b', 20, 22, 31, 23); cv.rect('SOIL_C', 'soil', 16, 22, 19, 23)
moved = repair(cv); shade(cv, [n for n in cv.order if n.startswith('LEAF_')], SH)
def build(hand=None):
    errs, adj = validate(cv); same = sorted({(a, b) for a in adj for b in adj[a] if a < b and HEX[cv.color[a]] == HEX[cv.color[b]]})
    return dict(id='L03', name='L03 — Ağaç', title='L03 · ağaç 36×24', w=36, h=24, entrance=[24, 18], floor=[], pieces=cv.finalize(), colorHex=HEX, style='blocks', hand=hand, pattern='manuel'), errs, same
A_ = "LEAF_06 LEAF_07 LEAF_05 LEAF_14 BRANCH_L LEAF_13 LEAF_04 BUSH_L GROUND_L LEAF_12".split()
B_ = "LEAF_09 LEAF_10 LEAF_01 LEAF_16 LEAF_11 BRANCH_R LEAF_02 BUSH_R GROUND_R BRANCH_STEM".split()
_g = Geo(cv); _vo = valid_order(cv, _g); _ix = {n: i for i, n in enumerate(_vo)}
_core = "LEAF_08 LEAF_15 LEAF_18 LEAF_17 LEAF_03 TRUNK_TOP TRUNK_MID ROOTS SOIL_C".split(); _apples = "APPLE_1 APPLE_2 APPLE_5 APPLE_3 APPLE_4".split()
HAND = [sorted(A_, key=lambda n: _ix[n]), sorted(B_, key=lambda n: _ix[n]), _core[:3] + _apples + _core[3:]]
if __name__ == '__main__':
    src, errs, same = build(HAND); print('repair taşınan hücre', moved, stats_line(cv), errs, 'aynı-renk komşu:', same)
    json.dump(src, open('l03_source.json', 'w'), separators=(',', ':'))
