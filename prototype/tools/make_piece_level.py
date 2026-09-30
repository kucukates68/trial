"""Elle hazırlanmış TEK seviye: KÜÇÜK KEDİ (üretici/arama yok) → src/levels_pieces.js + parity vektörleri.
Kedi hücreleri (A turuncu: kulak/kafa/kuyruk, B sarı: gövde, C pembe: burun/patiler) ve parçalar ELLE tanımlıdır;
aşağıdaki doğrulama parçaların kediyi TAM kapladığını (toplam hücre eşitliği, renk eşleşmesi, örtüşme yok) denetler."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from piece_ref import PLevel, make_vectors

CAT = [  # E = giriş, . = görünmez zemin (sol şerit), # = duvar (görünmez), harf = kedi hücresi (A turuncu, B sarı, C pembe)
    "#.A####A##",
    "#.AAAAAA##",
    "#.AAAAAA#A",
    "#.CBBBBC#A",
    "E.CBBBBCAA",
    "#.CBBBBC##",
    "#.CC##CC##",
]
# parça: (id, renk, [(satır, sütun) mutlak konum = kedideki YERİ (yalnız doğrulama için)])
PLACE = [
    ('A1', 'A', [(0, 2), (1, 2), (2, 2), (2, 3)]),          # sol kulak + yüz kenarı (L)
    ('A2', 'A', [(0, 7), (1, 7), (2, 7), (2, 6)]),          # sağ kulak + yüz kenarı (J)
    ('A3', 'A', [(1, 3), (1, 4), (1, 5), (1, 6)]),          # alın (I)
    ('A4', 'A', [(2, 9), (3, 9), (4, 9), (4, 8)]),          # kuyruk (J)
    ('A5', 'A', [(2, 4), (2, 5)]),                          # yüz alt orta (I2)
    ('B1', 'B', [(3, 3), (3, 4), (3, 5), (4, 3)]),          # gövde: L
    ('B2', 'B', [(3, 6), (4, 4), (4, 5), (4, 6)]),          # gövde: J
    ('B3', 'B', [(5, 3), (5, 4), (5, 5), (5, 6)]),          # gövde alt: I
    ('C1', 'C', [(3, 7), (4, 7), (5, 7), (6, 7), (6, 6)]),  # sağ bacak + pati (J5)  — el sırasında pembenin ilk parçası
    ('C2', 'C', [(3, 2), (4, 2), (5, 2), (6, 2), (6, 3)]),  # sol bacak + pati (L5)  — sıradaki
]
GRID = '\n'.join(CAT)
cat_cells = {(r, c): ch for r, row in enumerate(CAT) for c, ch in enumerate(row) if ch in 'ABC'}
cover = {}
for pid, ch, cells in PLACE:
    for x in cells:
        assert x not in cover, ('örtüşme', pid, x); cover[x] = ch
        assert cat_cells.get(x) == ch, ('renk/hücre uyuşmazlığı', pid, x)
assert set(cover) == set(cat_cells), 'parçalar kediyi tam kaplamıyor'
total = sum(len(c) for _, _, c in PLACE); assert total == len(cat_cells)
def norm(cells): r0 = min(r for r, c in cells); c0 = min(c for r, c in cells); return sorted([r - r0, c - c0] for r, c in cells)
pieces = [dict(id=pid, ch=ch, cells=norm(cells)) for pid, ch, cells in PLACE]
L = PLevel(GRID, pieces)
lv = dict(id='CAT', name='Küçük kedi', grid=GRID, pieces=pieces, cells=L.n,
          palette=dict(colors=['#ff9a4d', '#ffd96a', '#ff7fa8'], names=['Turuncu', 'Sarı', 'Pembe']), stats=L.stats())
if __name__ == '__main__':
    S = os.path.join(H, '..', 'src')
    open(os.path.join(S, 'levels_pieces.js'), 'w', encoding='utf-8').write('window.CB_LEVELS = ' + json.dumps([lv], ensure_ascii=False) + ';\n')
    vec = make_vectors([lv], n_random=25)
    open(os.path.join(S, 'vectors_pieces.js'), 'w', encoding='utf-8').write('window.CB_VECTORS = ' + json.dumps(dict(levels=vec)) + ';\n')
    json.dump(dict(levels=vec), open(os.path.join(H, '..', 'tests', 'piece_vectors.json'), 'w'))
    print('kedi hücre', L.n, 'parça', L.P, 'toplam parça hücresi', total); print(lv['stats'])
