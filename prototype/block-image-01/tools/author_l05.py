"""L05 — KUŞ (peak). Dalda tünemiş mavi kuş (sola bakıyor): baş (göz cebi, tepelik, yanak), gaga, gövde (sırt/karın küçük parçalar), kanat + tüy uçları, 3 kuyruk tüyü, ince bacaklar (iki geçit), ayaklar, dal + yapraklar + meyve. Mekanik değişmez."""
import json, math
from lvlkit import *
cv = Canvas(); cv.entrance = (18, 24)
HEX = dict(back_a='#4a90d9', back_b='#3b7ac4', back_c='#5aa0e6', belly_a='#f3e9d2', belly_b='#e8dbbd', belly_c='#fbf3df', head_a='#5aa0e6', head_b='#4a90d9', head_c='#6bb0ee', crest='#2f5fa8', beak='#f29a2e', beak_b='#e07f1c', eye='#1d1d22', eye_hi='#ffffff', cheek='#f2a1a1',
           wing_a='#2f5fa8', wing_b='#274f90', wing_c='#3a6dbb', tail_a='#274f90', tail_b='#2f5fa8', tail_c='#3a6dbb', leg='#e8892f', foot='#d97a22', br_a='#7a4c22', br_b='#6a3f1f', br_c='#8a5a2b', leaf_a='#4f9d3a', leaf_b='#3f8a31', leaf_c='#5fae45', berry='#d8362f')
def R(spec): return [(x, y) for y, (x0, x1) in spec.items() for x in range(x0, x1 + 1)]
HEAD = {3: (8, 12), 4: (7, 13), 5: (6, 14), 6: (5, 15), 7: (5, 15), 8: (5, 15), 9: (6, 15), 10: (7, 15)}
BODY = {9: (16, 22), 10: (6, 26), 11: (6, 27), 12: (6, 28), 13: (7, 28), 14: (8, 28), 15: (9, 27), 16: (10, 26), 17: (11, 24), 18: (12, 22)}
WINGR = {11: (13, 20), 12: (12, 23), 13: (12, 25), 14: (13, 26), 15: (14, 25), 16: (16, 24)}
# gövde: en yakın tohum (sırt mavi / karın-göğüs krem)
bs = [((14, 11), 'b'), ((19, 10), 'b'), ((24, 11), 'b'), ((9, 11), 'b'), ((8, 14), 'c'), ((11, 17), 'c'), ((15, 17), 'c'), ((19, 17), 'c'), ((22, 16), 'c'), ((26, 14), 'b')]
BB = ['back_a', 'back_b', 'back_c']; BC = ['belly_a', 'belly_b', 'belly_c']
for (x, y) in R(BODY):
    k = min(range(len(bs)), key=lambda i: (x - bs[i][0][0]) ** 2 + ((y - bs[i][0][1]) * 1.2) ** 2); cv.own[(x, y)] = 'BODY_%02d' % (k + 1)
for i, (s, kind) in enumerate(bs): cv.color['BODY_%02d' % (i + 1)] = (BB if kind == 'b' else BC)[i % 3]; cv.order.append('BODY_%02d' % (i + 1))
# baş
hs = [(8, 5), (13, 5), (8, 9), (13, 9)]
for (x, y) in R(HEAD):
    k = min(range(len(hs)), key=lambda i: (x - hs[i][0]) ** 2 + (y - hs[i][1]) ** 2); cv.own[(x, y)] = 'HEAD_%d' % (k + 1)
for i in range(len(hs)): cv.color['HEAD_%d' % (i + 1)] = ['head_a', 'head_b', 'head_c', 'head_b'][i]; cv.order.append('HEAD_%d' % (i + 1))
cv.piece('BEAK_UP', 'beak', [(3, 6), (4, 6), (2, 7), (3, 7), (4, 7)]); cv.piece('BEAK_LOW', 'beak_b', [(1, 8), (2, 8), (3, 8), (4, 8), (2, 9), (3, 9), (4, 9)])
cv.piece('EYE', 'eye', [(8, 6), (7, 7), (8, 7)]); cv.piece('EYE_HI', 'eye_hi', [(7, 6)]); cv.piece('CHEEK', 'cheek', [(6, 9), (7, 9), (6, 10), (7, 10)])
cv.piece('CREST_1', 'crest', [(7, 1), (8, 1), (8, 2)]); cv.piece('CREST_2', 'crest', [(10, 0), (10, 1), (11, 1), (10, 2), (11, 2)]); cv.piece('CREST_3', 'wing_c', [(13, 1), (13, 2), (12, 2)])
# kanat (2 gövde + 3 tüy ucu)
W = R(WINGR)
cv.piece('WING_TOP', 'wing_a', [p for p in W if p[1] <= 12]); cv.piece('WING_MID', 'wing_c', [p for p in W if 13 <= p[1] <= 14])
for i, (xa, xb) in enumerate(((12, 17), (18, 21), (22, 26))): cv.piece('WING_TIP_%d' % (i + 1), ['wing_b', 'wing_a', 'wing_b'][i], [p for p in W if p[1] >= 15 and xa <= p[0] <= xb])
# kuyruk
cv.rect('TAIL_A', 'tail_a', 28, 11, 34, 12); cv.rect('TAIL_B', 'tail_b', 28, 13, 35, 14); cv.rect('TAIL_C', 'tail_c', 28, 15, 34, 16)
# bacaklar / ayaklar / dal / yapraklar / meyve
cv.rect('LEG_L', 'leg', 14, 19, 15, 20); cv.rect('LEG_R', 'leg', 19, 19, 20, 20); cv.rect('FOOT_L', 'foot', 13, 21, 16, 21); cv.rect('FOOT_R', 'foot', 18, 21, 21, 21)
cv.rect('BRANCH_L', 'br_a', 2, 22, 11, 23); cv.rect('BRANCH_C', 'br_c', 12, 22, 23, 23); cv.rect('BRANCH_R', 'br_b', 24, 22, 33, 23)
cv.rect('LEAF_L1', 'leaf_a', 3, 20, 6, 21); cv.rect('LEAF_L2', 'leaf_b', 7, 20, 9, 21); cv.rect('LEAF_R1', 'leaf_c', 25, 20, 28, 21); cv.rect('LEAF_R2', 'leaf_a', 29, 20, 32, 21)
cv.piece('BERRY_1', 'berry', [(5, 19), (6, 19)]); cv.piece('BERRY_2', 'berry', [(30, 19), (31, 19)])
moved = repair(cv)
shade(cv, [n for n in cv.order if n.startswith('BODY_') and cv.color[n] in BB], BB); shade(cv, [n for n in cv.order if n.startswith('BODY_') and cv.color[n] in BC], BC); shade(cv, [n for n in cv.order if n.startswith('HEAD_')], ['head_a', 'head_b', 'head_c'])
HAND = [['CREST_1', 'BEAK_UP', 'BEAK_LOW', 'CREST_2', 'CREST_3', 'HEAD_1', 'HEAD_2', 'EYE_HI', 'EYE', 'CHEEK', 'HEAD_3', 'HEAD_4'], ['TAIL_A', 'TAIL_B', 'TAIL_C', 'BODY_01', 'BODY_04', 'BODY_03', 'BODY_05', 'BODY_02', 'BODY_10', 'WING_TIP_3', 'BODY_06', 'WING_TIP_1', 'BODY_09', 'BODY_07', 'WING_TOP', 'WING_MID', 'WING_TIP_2', 'BODY_08'], ['BERRY_1', 'BERRY_2', 'LEAF_L1', 'LEAF_R2', 'LEAF_L2', 'LEAF_R1', 'BRANCH_L', 'LEG_L', 'BRANCH_R', 'FOOT_L', 'LEG_R', 'FOOT_R', 'BRANCH_C']]
def build(hand=None):
    errs, adj = validate(cv); same = sorted({(a, b) for a in adj for b in adj[a] if a < b and HEX[cv.color[a]] == HEX[cv.color[b]]})
    return dict(id='L05', name='L05 — Kuş', title='L05 · kuş 36×24', w=36, h=24, entrance=[24, 18], floor=[], pieces=cv.finalize(), colorHex=HEX, style='blocks', hand=hand, pattern='manuel'), errs, same
if __name__ == '__main__':
    src, errs, same = build(HAND); print('repair', moved, stats_line(cv), errs, 'aynı-renk komşu:', same)
    json.dump(src, open('l05_source.json', 'w'), separators=(',', ':'))
