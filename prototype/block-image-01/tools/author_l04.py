"""L04 — ARABA (zor). Yan görünüş: kabin (pencere cepleri, sütunlar), gövde (kapılar, kapı kolu cebi), farlar/tamponlar, iç içe tekerlek (lastik ⊃ jant ⊃ kapak), alt şasi; giriş araç altındaki tek hücrelik koridordan şasiye. Mekanik değişmez."""
import json, math
from lvlkit import *
cv = Canvas(); cv.entrance = (18, 24); cv.floor = {(18, 20), (18, 21), (18, 22), (18, 23)}
HEX = dict(body_a='#d63a3a', body_b='#c22e2e', body_c='#e24b4b', roof='#b72b2b', glass_a='#9fd0ee', glass_b='#b9dff3', pillar='#3a3f4a', tire='#2b2b30', rim='#c8ccd2', hub='#8b9099', bumper='#9aa0a8', head='#ffe066', tail='#ff7a5a',
           handle='#e8e8e8', chassis='#4a4f59', mirror='#2f333c', sill='#a82727', tire_b='#3c3c45')
# --- kabin (y5–11)
cab = {5: (11, 22), 6: (10, 23), 7: (9, 24), 8: (8, 25), 9: (7, 26), 10: (6, 27), 11: (5, 28)}
def cabin(pred): return [(x, y) for y, (x0, x1) in cab.items() for x in range(x0, x1 + 1) if pred(x, y)]
cv.piece('ROOF_L', 'roof', cabin(lambda x, y: y <= 6 and x <= 16)); cv.piece('ROOF_R', 'body_b', cabin(lambda x, y: y <= 6 and x >= 17))
cv.piece('PILLAR_L', 'pillar', cabin(lambda x, y: 7 <= y <= 10 and x <= 9)); cv.piece('PILLAR_R', 'pillar', cabin(lambda x, y: 7 <= y <= 10 and x >= 24))
cv.rect('WIN_REAR', 'glass_a', 10, 7, 13, 10); cv.rect('WIN_MID', 'glass_b', 15, 7, 18, 10); cv.rect('WIN_FRONT', 'glass_a', 20, 7, 23, 10)
cv.rect('PILLAR_B', 'pillar', 14, 7, 14, 10); cv.rect('PILLAR_C', 'pillar', 19, 7, 19, 10)
cv.rect('SILL_L', 'sill', 5, 11, 16, 11); cv.rect('SILL_R', 'roof', 17, 11, 28, 11)
# --- gövde üst şerit (y12–13)
cv.rect('TRUNK', 'body_a', 5, 12, 12, 13); cv.rect('DECK_L', 'body_c', 13, 12, 17, 13); cv.rect('DECK_R', 'body_b', 18, 12, 22, 13); cv.rect('HOOD', 'body_a', 23, 12, 30, 13)
# --- yan gövde (y14–19) taslak; sonra ışıklar/tekerlekler ezer
cv.rect('REAR_UP', 'body_b', 2, 14, 12, 16); cv.rect('REAR_LOW', 'body_c', 2, 17, 12, 19); cv.rect('FRONT_UP', 'body_a', 23, 14, 33, 16); cv.rect('FRONT_LOW', 'body_c', 23, 17, 33, 19)
cv.rect('DOOR_1', 'body_a', 13, 14, 17, 18); cv.rect('DOOR_2', 'body_b', 18, 14, 22, 18)
cv.rect('UNDER_L', 'chassis', 13, 19, 15, 19); cv.rect('UNDER_C', 'sill', 16, 19, 19, 19); cv.rect('UNDER_R', 'chassis', 20, 19, 22, 19)
# --- ışıklar, tamponlar, kapı kolları, ayna
cv.rect('TAILLIGHT', 'tail', 2, 14, 3, 16); cv.rect('BUMPER_R', 'bumper', 2, 17, 3, 18); cv.rect('HEADLIGHT', 'head', 32, 14, 33, 15); cv.rect('BUMPER_F', 'bumper', 32, 16, 33, 18)
cv.rect('HANDLE_1', 'handle', 16, 15, 17, 15); cv.rect('HANDLE_2', 'handle', 20, 15, 21, 15); cv.rect('MIRROR', 'mirror', 24, 11, 25, 11) if False else None
# --- tekerlekler (lastik ⊃ jant ⊃ kapak): kabuk yarıçapları
for tag, cx in (('R', 9.5), ('F', 26.5)):
    cy = 19.5
    def ring(r0, r1): return [(x, y) for y in range(14, 24) for x in range(int(cx) - 6, int(cx) + 7) if r0 < math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r1 and 0 <= y <= 23]
    tire = ring(-1, 4.4); cv.piece('TIRE_%s_TOP' % tag, 'tire', [p for p in tire if p[1] < 19]); cv.piece('TIRE_%s_BOT' % tag, 'tire_b', [p for p in tire if p[1] >= 19]); cv.piece('RIM_' + tag, 'rim', ring(-1, 2.8)); cv.piece('HUB_' + tag, 'hub', ring(-1, 1.3))
moved = repair(cv)
shade(cv, ['TRUNK', 'DECK_L', 'DECK_R', 'HOOD', 'REAR_UP', 'REAR_LOW', 'FRONT_UP', 'FRONT_LOW', 'DOOR_1', 'DOOR_2'], ['body_a', 'body_b', 'body_c'])
HAND = [['PILLAR_L', 'TAILLIGHT', 'BUMPER_R', 'WIN_REAR', 'REAR_LOW', 'REAR_UP', 'HUB_R', 'RIM_R', 'TIRE_R_TOP', 'TIRE_R_BOT', 'UNDER_L', 'TRUNK'], ['HEADLIGHT', 'PILLAR_R', 'BUMPER_F', 'FRONT_LOW', 'WIN_FRONT', 'FRONT_UP', 'HUB_F', 'RIM_F', 'TIRE_F_TOP', 'TIRE_F_BOT', 'UNDER_R', 'HOOD'], ['ROOF_L', 'ROOF_R', 'PILLAR_B', 'PILLAR_C', 'SILL_L', 'WIN_MID', 'SILL_R', 'HANDLE_2', 'HANDLE_1', 'DOOR_1', 'DECK_L', 'DECK_R', 'DOOR_2', 'UNDER_C']]
def build(hand=None):
    errs, adj = validate(cv); same = sorted({(a, b) for a in adj for b in adj[a] if a < b and HEX[cv.color[a]] == HEX[cv.color[b]]})
    return dict(id='L04', name='L04 — Araba', title='L04 · araba 36×24', w=36, h=24, entrance=[24, 18], floor=[list(f) for f in sorted(cv.floor)], pieces=cv.finalize(), colorHex=HEX, style='blocks', hand=hand, pattern='manuel'), errs, same
if __name__ == '__main__':
    src, errs, same = build(HAND); print('repair', moved, stats_line(cv), errs, 'aynı-renk komşu:', same)
    json.dump(src, open('l04_source.json', 'w'), separators=(',', ':'))
