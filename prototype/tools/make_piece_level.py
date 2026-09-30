"""Elle hazırlanmış TEK test seviyesi (üretici/solver araması yok) → src/levels_pieces.js (+ parity vektörleri).
Turuncu = L (5 hücre), Mavi = T (5 hücre), Kırmızı = 2x2 (4 hücre); her renkten 2 parça."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from piece_ref import PLevel, make_vectors
GRID = """###A#BBB##
###A##B#CC
###A##B#CC
E..AA.....
#A###BBBCC
#A####B#CC
#A####B###
#AA#######"""
L5 = [[0, 0], [1, 0], [2, 0], [3, 0], [3, 1]]; T5 = [[0, 0], [0, 1], [0, 2], [1, 1], [2, 1]]; SQ = [[0, 0], [0, 1], [1, 0], [1, 1]]
pieces = [dict(id='A1', ch='A', cells=L5), dict(id='A2', ch='A', cells=L5), dict(id='B1', ch='B', cells=T5), dict(id='B2', ch='B', cells=T5),
          dict(id='C1', ch='C', cells=SQ), dict(id='C2', ch='C', cells=SQ)]
lv = dict(id='T1', name='Test seviyesi: L · T · kare', grid=GRID, pieces=pieces, cells=PLevel(GRID, pieces).n,
          palette=dict(colors=['#ff8a1f', '#3b82f6', '#e5383b'], names=['Turuncu', 'Mavi', 'Kırmızı']), stats=PLevel(GRID, pieces).stats())
S = os.path.join(H, '..', 'src')
open(os.path.join(S, 'levels_pieces.js'), 'w', encoding='utf-8').write('window.CB_LEVELS = ' + json.dumps([lv], ensure_ascii=False) + ';\n')
vec = make_vectors([lv], n_random=25)
open(os.path.join(S, 'vectors_pieces.js'), 'w', encoding='utf-8').write('window.CB_VECTORS = ' + json.dumps(dict(levels=vec)) + ';\n')
json.dump(dict(levels=vec), open(os.path.join(H, '..', 'tests', 'piece_vectors.json'), 'w'))
print('hücre', lv['cells'], 'vaka', len(vec[0]['cases']), lv['stats'])
