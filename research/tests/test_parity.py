"""1) the standalone simulator (default rules) must reproduce the engine's wave placements on all 32 human-test levels;
2) the diagnoser must name the right rule when the 'prototype' deviates in a known way."""
import json, os, sys, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import parity
from puzzle_engine import Level

HT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'human_test', 'levels.json')


def main():
    data = json.load(open(HT))
    # (1) engine equivalence on every level: replay each example sequence, compare filled sets move by move
    for lv in data['levels']:
        L = Level(lv['grid'], lv['W'])
        s = 0
        sim = parity.simulate(lv['grid'], lv['W'], lv['example_winning_sequence'])
        pos = {p: i for i, p in enumerate(L.tpos)}
        for mv in sim:
            k = L.letters.index(mv['color'])
            nxt = dict(L.info(s)[1])[k]
            assert sorted(pos[tuple(p)] for p in mv['placed']) == [i for i in range(L.n) if (nxt >> i) & 1 and not (s >> i) & 1], lv['id']
            s = nxt
        assert s == L.full, lv['id']
    print('simulator == engine on', len(data['levels']), 'levels')
    # (2) diagnosis of known deviations
    sub = dict(levels=data['levels'][:8])
    vec = dict(levels=[parity.make_vectors_for(l['id'], l['grid'], l['W'], l.get('example_winning_sequence')) for l in sub['levels']])
    def traces_from(var=None, Wdelta=0, grid_fn=None):
        return dict(traces=[dict(level_id=lv['level_id'], cases=[dict(name=c['name'], moves=parity.simulate(lv['grid'] if not grid_fn else grid_fn(lv['grid']), lv['W'] + Wdelta, c['sequence'], var)) for c in lv['cases']]) for lv in vec['levels']])
    def run(traces):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = parity.check(vec, traces)
        return ok, buf.getvalue()
    ok, out = run(traces_from()); assert ok, out
    for name, tr, expect in [('nearest-first', traces_from(dict(order='near')), "'order': 'near'"),
                             ('8-neighbour', traces_from(dict(nbr=8)), "'nbr': 8"),
                             ('col-major ties', traces_from(dict(tie='col')), "'tie': 'col'"),
                             ('W+1', traces_from(Wdelta=1), 'dalga boyu farkı')]:
        ok, out = run(tr)
        assert not ok, name
        print(f'{name:16} -> fark yakalandı; tanı/mesaj içeriyor:', expect in out)
        if name != 'W+1':
            assert expect in out.split('Tanı')[1].split('\n')[1], (name, out[-400:])
    print('ok')


if __name__ == '__main__':
    main()
