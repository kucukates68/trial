"""L02-V2 — KAKTÜS (yol geçişi deneyi). İki dirsekli kol (dar geçit: 3 hücre yüksekliğinde bağlantı + dikey kol), ana gövde (yatay dilimler), üç çiçek, gövde/kol dikenleri (cep), saksı (giriş altında).
Zemin hücresi YOK: yol, resmin kendi hedef hücreleridir. Her parça tek renk. Mekanik değişmez."""
import json
from lvlkit import *
cv = Canvas(); cv.entrance = (17, 24)
HEX = dict(g_a='#4f9d4a', g_b='#3f8a3e', g_c='#5cae56', g_d='#478f44', spine='#f3ead2', fl_pink='#f06b9a', fl_yel='#f7c948', fl_red='#e8505b',
           pot_a='#c4693a', pot_b='#b35a2f', pot_c='#d07a48', rim_a='#a8502a', rim_b='#9a4524', rim_c='#b25f35')
# --- ana gövde (x13..22), üst köşeler yuvarlak; yatay dilimler
def trunk(y0, y1, name, col):
    cells = [(x, y) for y in range(y0, y1 + 1) for x in range(13, 23)]
    cv.piece(name, col, cells)
cv.piece('TR_1', 'g_a', [(x, y) for y in range(3, 6) for x in range(13, 23) if not ((y == 3 and (x < 15 or x > 20)) or (y == 4 and (x < 14 or x > 21)))])
trunk(6, 9, 'TR_2', 'g_b'); trunk(10, 14, 'TR_3', 'g_c'); trunk(15, 18, 'TR_4', 'g_d')
# --- üst çiçek
cv.piece('FLOWER_T', 'fl_pink', [(17, 0), (18, 0), (16, 1), (17, 1), (18, 1), (19, 1), (16, 2), (17, 2), (18, 2), (19, 2)])
# --- sol kol: dar bağlantı (x10..12,y11..13) → dirsek (x6..9,y10..13) → dikey (x6..9,y4..9) → çiçek (x6..9,y1..3)
cv.rect('ARM_L_CON', 'g_b', 10, 11, 12, 13); cv.rect('ARM_L_ELB', 'g_a', 6, 10, 9, 13); cv.rect('ARM_L_UP', 'g_c', 6, 4, 9, 9); cv.rect('FLOWER_L', 'fl_yel', 6, 1, 9, 3)
# --- sağ kol (daha yüksekte): bağlantı (x23..25,y8..10) → dirsek (x26..29,y7..10) → dikey (x26..29,y3..6) → çiçek (x26..29,y0..2)
cv.rect('ARM_R_CON', 'g_a', 23, 8, 25, 10); cv.rect('ARM_R_ELB', 'g_c', 26, 7, 29, 10); cv.rect('ARM_R_UP', 'g_b', 26, 3, 29, 6); cv.rect('FLOWER_R', 'fl_red', 26, 0, 29, 2)
# --- saksı: kenar (y19–20, x10..25) üç parça, gövde (y21–23, x12..23) üç parça; giriş (17,24) saksı orta gövdesinin altında
cv.rect('RIM_L', 'rim_a', 10, 19, 14, 20); cv.rect('RIM_C', 'rim_b', 15, 19, 20, 20); cv.rect('RIM_R', 'rim_c', 21, 19, 25, 20)
cv.rect('POT_L', 'pot_a', 12, 21, 15, 23); cv.rect('POT_C', 'pot_b', 16, 21, 19, 23); cv.rect('POT_R', 'pot_c', 20, 21, 23, 23)
# --- dikenler (cep): gövde dilimleri ve kolların içinde 2 hücrelik krem çizgiler
for i, cells in enumerate([[(16, 4), (17, 4)], [(14, 7), (15, 7)], [(20, 8), (21, 8)], [(16, 12), (17, 12)], [(14, 16), (15, 16)], [(19, 17), (20, 17)], [(7, 6), (8, 6)], [(27, 4), (28, 4)]]): cv.piece('SPINE_%d' % (i + 1), 'spine', cells)
moved = repair(cv)
HAND = [['FLOWER_R', 'SPINE_3', 'ARM_R_ELB', 'FLOWER_T', 'ARM_R_CON', 'TR_2', 'FLOWER_L', 'ARM_L_CON', 'TR_4'], ['SPINE_2', 'SPINE_8', 'SPINE_4', 'SPINE_7', 'RIM_L', 'POT_R', 'TR_1', 'ARM_L_ELB', 'SPINE_5'], ['ARM_R_UP', 'RIM_R', 'SPINE_1', 'POT_L', 'ARM_L_UP', 'TR_3', 'SPINE_6', 'RIM_C', 'POT_C']]
def build(hand=None):
    errs, adj = validate(cv); same = sorted({(a, b) for a in adj for b in adj[a] if a < b and HEX[cv.color[a]] == HEX[cv.color[b]]})
    return dict(id='L02V2', name='L02-V2 — Kaktüs (yol geçişi)', title='L02-V2 · kaktüs 36×24', entrance=[24, 17], floor=[], pieces=cv.finalize(), colorHex=HEX, style='blocks', hand=hand, pattern='manuel'), errs, adj, same
if __name__ == '__main__':
    src, errs, adj, same = build(HAND); print('repair', moved, stats_line(cv), 'hatalar', errs, 'aynı-renk komşu', same)
    json.dump(src, open('l02v2_source.json', 'w'), separators=(',', ':'))
