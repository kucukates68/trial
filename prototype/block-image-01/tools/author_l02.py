"""L02 — EV (kolay / kolay-orta). Yazım betiği: görseli + parçaları boyar, kuyrukları verir, tools/l02_source.json üretir. Mekanik değişmez."""
import json, sys
from lvlkit import *
cv = Canvas(); cv.entrance = (18, 24)
HEX = dict(roof_a='#c0452f', roof_b='#a93a28', ridge='#8f2f21', brick_a='#a05a46', brick_b='#8c4a3a', wall_a='#f3e3c3', wall_b='#ead5ac', wall_c='#f8eed6', frame='#fbf7ee', glass_a='#8cc4e6', glass_b='#a5d3ee',
           door_a='#8b5a2b', door_b='#7a4c22', knob='#e8b923', found_a='#9b9b9b', found_b='#868686', step='#b4b0a8', grass_a='#6fb34f', grass_b='#5da042', path='#c9a66b')
# --- baca (önce; çatı üstüne biner)
cv.rect('CHIMNEY_CAP', 'brick_b', 24, 0, 27, 1); cv.rect('CHIMNEY', 'brick_a', 24, 2, 27, 4)
# --- çatı: 6 satır üçgen
roof = {3: (16, 19), 4: (13, 22), 5: (10, 25), 6: (7, 28), 7: (4, 31), 8: (3, 32)}
def rr(ys, side):
    out = []
    for y in ys:
        x0, x1 = roof[y]
        for x in range(x0, x1 + 1):
            if side is None or (side == 'L' and x <= 17) or (side == 'R' and x >= 18): out.append((x, y))
    return out
cv.piece('RIDGE', 'ridge', rr([3, 4], None)); cv.piece('ROOF_L1', 'roof_a', rr([5, 6], 'L')); cv.piece('ROOF_R1', 'roof_b', rr([5, 6], 'R')); cv.piece('ROOF_L2', 'roof_b', rr([7, 8], 'L')); cv.piece('ROOF_R2', 'roof_a', rr([7, 8], 'R'))
# --- duvar
cv.rect('WALL_TL', 'wall_a', 7, 9, 17, 10); cv.rect('WALL_TR', 'wall_b', 18, 9, 28, 10)
cv.rect('WALL_L_SIDE', 'wall_b', 7, 11, 8, 20); cv.rect('WALL_L_BOT', 'wall_c', 9, 17, 14, 20); cv.rect('LINTEL', 'wall_c', 15, 11, 20, 13); cv.rect('WALL_R_SIDE', 'wall_a', 27, 11, 28, 20); cv.rect('WALL_R_BOT', 'wall_c', 21, 17, 26, 20)
# --- pencereler (çerçeve halkası + cam cebi)
for nm, x0 in (('L', 9), ('R', 21)):
    cv.rect('FRAME_' + nm, 'frame', x0, 11, x0 + 5, 16); cv.rect('GLASS_' + nm, 'glass_a' if nm == 'L' else 'glass_b', x0 + 1, 12, x0 + 4, 15)
# --- kapı + tokmak
cv.rect('DOOR', 'door_a', 15, 14, 20, 20); cv.piece('KNOB', 'knob', [(19, 17), (19, 18)])
# --- temel / basamak / çim / yol
cv.rect('FOUND_L', 'found_a', 6, 21, 14, 22); cv.rect('FOUND_R', 'found_b', 21, 21, 29, 22); cv.rect('STEP', 'step', 15, 21, 20, 22)
cv.rect('GRASS_L', 'grass_a', 3, 23, 15, 23); cv.rect('GRASS_R', 'grass_b', 20, 23, 32, 23); cv.rect('PATH', 'path', 16, 19, 19, 23) if False else cv.rect('PATH', 'path', 16, 23, 19, 23)
HAND = ["CHIMNEY_CAP CHIMNEY RIDGE ROOF_L1 ROOF_L2 WALL_TL WALL_L_SIDE WALL_L_BOT FOUND_L".split(), "GLASS_L GLASS_R FRAME_L ROOF_R1 ROOF_R2 WALL_TR WALL_R_SIDE WALL_R_BOT FOUND_R".split(), "KNOB FRAME_R LINTEL DOOR GRASS_L GRASS_R STEP PATH".split()]
def build(hand=None):
    errs, adj = validate(cv); same = sorted({(a, b) for a in adj for b in adj[a] if a < b and HEX[cv.color[a]] == HEX[cv.color[b]]})
    return dict(id='L02', name='L02 — Ev', title='L02 · ev 36×24', w=36, h=24, entrance=[24, 18], floor=[], pieces=cv.finalize(), colorHex=HEX, style='blocks', hand=hand, pattern='manuel'), errs, same
if __name__ == '__main__':
    src, errs, same = build(HAND); print(stats_line(cv), errs, 'aynı-renk komşu:', same)
    json.dump(src, open('l02_source.json', 'w'), separators=(',', ':'))
