"""Builds prototype/src/levels_data.js and vectors_data.js (dev tooling; imports ../../research).

Levels = 3 hero configurations of the hand-coloured cat (216 cells, single entrance) + the 32-level human-test set.
Vectors = solver conformance vectors (ordered placements) for every level, embedded so the HTML can self-check parity.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, '..', '..', 'research')
sys.path.insert(0, R)
sys.path.insert(0, HERE)
from puzzle_engine import analyze
from puzzle_access import build_grid
from parity import make_vectors_for
from hero_search import cat_labels

OUT = os.path.join(HERE, '..', 'src')
GENERIC = {'names': ['Kırmızı', 'Mavi', 'Sarı'], 'colors': ['#e4572e', '#2e86ab', '#f2c14e']}
CAT = {'names': ['Turuncu', 'Siyah', 'Beyaz'], 'colors': ['#f28c28', '#26262e', '#fbfaf5']}

HERO = [  # (id, ad, erişim, W, not)
    ('HERO1', 'Kedi · kolay', 'BOT2', 26, 'üst kapı, 9 dalga'),
    ('HERO2', 'Kedi · orta', 'BOT3', 21, 'sol kapı, 12 dalga'),
    ('HERO3', 'Kedi · gecikmeli hata', 'BOT1', 24, 'alt kapı, 10 dalga; hata çoğu zaman birkaç hamle sonra kilitler'),
]
KEYS = ['e_risky', 'e_crit', 'dens_risky', 'dh_exp_mean', 'dh_instant_share', 'abc_mean', 'filler_ratio', 'rnd0', 'win_undo1', 'win_undo2', 'rec1', 'greedy_deep']


def metrics(grid, W):
    r = analyze(grid, W, extra=True, sims=1500)
    return {k: (None if r.get(k) is None else (bool(r[k]) if isinstance(r[k], bool) else round(float(r[k]), 3))) for k in KEYS} | {'waves': r['waves_nominal']}


levels, vecs = [], []
lab = cat_labels(2)
for lid, name, lay, W, note in HERO:
    g = build_grid(lab, lay)
    m = metrics(g, W)
    levels.append(dict(id=lid, name=name, group='hero', grid=g, W=W, palette=CAT, note=note, cells=len(lab), solver=m))
    vecs.append(make_vectors_for(lid, g, W))
for lv in json.load(open(os.path.join(R, 'human_test', 'levels.json')))['levels']:
    levels.append(dict(id=lv['id'], name=f"{lv['src']} / {lv['cm']} / {lv['layout']}", group=lv['group'], grid=lv['grid'], W=lv['W'], palette=GENERIC,
                       note=f"pair {lv['pair']}" if lv.get('pair') else '', cells=lv['cells'],
                       solver={k: lv['metrics'].get(k) for k in ['e_risky', 'e_crit', 'dens_risky', 'dh_exp_mean', 'dh_instant_share', 'abc_mean', 'filler_ratio', 'rnd0', 'win_undo1', 'win_undo2', 'rec1']} | {'waves': lv['waves']}))
    vecs.append(make_vectors_for(lv['id'], lv['grid'], lv['W'], lv.get('example_winning_sequence')))

open(os.path.join(OUT, 'levels_data.js'), 'w').write('window.CB_LEVELS = ' + json.dumps(levels, ensure_ascii=False) + ';\n')
open(os.path.join(OUT, 'vectors_data.js'), 'w').write('window.CB_VECTORS = ' + json.dumps(dict(levels=vecs), separators=(',', ':')) + ';\n')
json.dump(dict(levels=vecs), open(os.path.join(HERE, '..', 'tests', 'conformance_all.json'), 'w'), separators=(',', ':'))
print('seviye', len(levels), '| vektör vaka', sum(len(v['cases']) for v in vecs))
for l in levels[:3]:
    print(l['id'], l['name'], l['cells'], 'hücre W', l['W'], l['solver'])
