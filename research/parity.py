"""Solver <-> prototype parity.

Three commands:

  grid-diff   compare the prototype's target grid with the solver's grid (dimensions, entrances, walls, colour counts, cell colours)
  vectors     produce conformance vectors: colour sequences + the EXACT ordered cells the solver places on every move
  check       compare a prototype's exported traces with the vectors; on divergence, diagnose WHICH rule explains the prototype

Trace format (language-agnostic JSON, coordinates are zero-based (row, col) in the grid text):
  {"traces": [ {"level_id": "CAT244", "moves": [ {"color": "A", "placed": [[r,c], [r,c], ...]}, ... ]}, ... ]}
  "placed" must be in the order the prototype places the boxes.  An optional per-move "sealed": true/false is compared too.

  python3 parity.py grid-diff solver_grid.txt prototype_grid.txt [--map O=A,K=B,W=C]
  python3 parity.py vectors --levels human_test/levels.json --out conformance.json
  python3 parity.py vectors --grid cat244.txt --W 16 --id CAT244 --out conformance_cat244.json
  python3 parity.py check conformance.json prototype_traces.json
"""
import argparse, json, os, random, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from human_test_oracle import Oracle

DEFAULT = dict(nbr=4, order='deep', tie='row', blocks=True)
TIES = {'row': lambda p: (p[0], p[1]), 'col': lambda p: (p[1], p[0]), 'rrow': lambda p: (-p[0], -p[1]), 'rcol': lambda p: (-p[1], -p[0])}


def parse(grid):
    T, E, floor = {}, [], set()
    for r, row in enumerate(grid.split('\n')):
        for c, ch in enumerate(row):
            if ch == '#': continue
            if ch == 'E': E.append((r, c)); floor.add((r, c))
            elif ch == '.': floor.add((r, c))
            else: T[(r, c)] = ch
    return T, E, floor


def _nbrs(p, k):
    r, c = p
    n = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    if k == 8:
        n += [(r + 1, c + 1), (r + 1, c - 1), (r - 1, c + 1), (r - 1, c - 1)]
    return n


def _dist(T, E, floor, filled, v):
    d = {e: 0 for e in E}
    q = deque(E)
    while q:
        u = q.popleft()
        for w in _nbrs(u, v['nbr']):
            if w in d: continue
            if w in floor or (w in T and (not v['blocks'] or w not in filled)):
                d[w] = d[u] + 1; q.append(w)
    return d


def simulate(grid, W, seq, variant=None):
    v = dict(DEFAULT, **(variant or {}))
    T, E, floor = parse(grid)
    filled = set(); out = []
    for col in seq:
        d = _dist(T, E, floor, filled, v)
        cand = [t for t in T if T[t] == col and t not in filled and t in d]
        key = TIES[v['tie']]
        cand.sort(key=(lambda t: (-d[t], key(t))) if v['order'] == 'deep' else (lambda t: (d[t], key(t))))
        placed = cand[:W]
        if not placed:
            out.append(dict(color=col, placed=[], illegal=True)); break
        filled |= set(placed)
        d2 = _dist(T, E, floor, filled, v)
        sealed = any(t not in filled and t not in d2 for t in T)
        out.append(dict(color=col, placed=[list(p) for p in placed], sealed=sealed))
    return out


# ------------------------------------------------------------------ grid diff
def grid_diff(a, b, cmap=None, limit=12):
    if cmap:
        b = ''.join(cmap.get(ch, ch) if ch not in '\n' else ch for ch in b)
    ra, rb = a.split('\n'), b.split('\n')
    print(f"boyut: solver {len(ra)}x{max(map(len, ra))} | prototip {len(rb)}x{max(map(len, rb))}")
    Ta, Ea, Fa = parse(a); Tb, Eb, Fb = parse(b)
    from collections import Counter
    print("hedef hücre:", len(Ta), "vs", len(Tb), "| renk sayıları:", dict(Counter(Ta.values())), "vs", dict(Counter(Tb.values())))
    print("giriş hücreleri:", sorted(Ea), "\n               vs", sorted(Eb))
    diffs = []
    for r in range(max(len(ra), len(rb))):
        for c in range(max(len(ra[r]) if r < len(ra) else 0, len(rb[r]) if r < len(rb) else 0)):
            x = ra[r][c] if r < len(ra) and c < len(ra[r]) else None
            y = rb[r][c] if r < len(rb) and c < len(rb[r]) else None
            if x != y: diffs.append((r, c, x, y))
    print("farklı hücre sayısı:", len(diffs))
    for r, c, x, y in diffs[:limit]:
        print(f"  ({r},{c}) solver={x!r} prototip={y!r}")
    return not diffs


# ------------------------------------------------------------------ vectors
def make_vectors_for(lid, grid, W, example=None, seed=5):
    o = Oracle(grid, W)
    L = o.L
    rng = random.Random(seed)
    seqs = []
    # 1) a winning sequence
    if example is None:
        s = 0; example = []
        while s != L.full:
            safe = [(L.letters[k], t) for k, t in L.info(s)[1] if o.nwin(t) > 0]
            c, s = rng.choice(safe); example.append(c)
    seqs.append(('winning', list(example)))
    # 2) sequences with a first mistake at step 1 and step 2 (then two more legal moves)
    for at in (1, 2):
        s = 0; seq = []; done = False
        for step in range(at + 4):
            sealed, mv = L.info(s)
            if not mv: break
            bad = [(L.letters[k], t) for k, t in mv if o.nwin(t) == 0]
            good = [(L.letters[k], t) for k, t in mv if o.nwin(t) > 0]
            if step == at and bad and not done:
                c, s = bad[0]; done = True
            elif good or step > at:
                c, s = rng.choice(good or [(L.letters[k], t) for k, t in mv])
            else:
                break
            seq.append(c)
            if L.info(s)[0]: break
        if done: seqs.append((f'mistake_at_{at}', seq))
    # 3) random legal walk
    s = 0; seq = []
    for _ in range(6):
        sealed, mv = L.info(s)
        if sealed or not mv: break
        c, s = rng.choice([(L.letters[k], t) for k, t in mv]); seq.append(c)
    seqs.append(('random_legal', seq))
    return dict(level_id=lid, W=W, grid=grid, colors=L.letters,
                cases=[dict(name=n, sequence=sq, expected=simulate(grid, W, sq)) for n, sq in seqs])


# ------------------------------------------------------------------ check / diagnose
VARIANTS = []
for nbr in (4, 8):
    for order in ('deep', 'near'):
        for tie in ('row', 'col', 'rrow', 'rcol'):
            for blocks in (True, False):
                VARIANTS.append(dict(nbr=nbr, order=order, tie=tie, blocks=blocks))


def same_cells(a, b):
    return sorted(map(tuple, a)) == sorted(map(tuple, b))


def check(vectors, traces, limit=3):
    tr = {t['level_id']: t for t in traces['traces']}
    ok_all = True; report = []
    for lv in vectors['levels']:
        t = tr.get(lv['level_id'])
        if not t:
            report.append((lv['level_id'], 'İZ YOK')); ok_all = False; continue
        t_moves = {c['name']: c for c in t.get('cases', [])} if 'cases' in t else None
        for case in lv['cases']:
            got = None
            if t_moves and case['name'] in t_moves: got = t_moves[case['name']]['moves']
            elif 'moves' in t and case['name'] == 'winning': got = t['moves']
            if got is None:
                report.append((lv['level_id'], case['name'], 'İZ YOK')); ok_all = False; continue
            exp = case['expected']; status = 'OK'
            for i, (e, g) in enumerate(zip(exp, got)):
                if e['placed'] == g['placed'] and (('sealed' not in g) or g['sealed'] == e.get('sealed')): continue
                if len(e['placed']) != len(g['placed']): kind = f"dalga boyu farkı (beklenen {len(e['placed'])}, prototip {len(g['placed'])})"
                elif same_cells(e['placed'], g['placed']): kind = 'aynı hücreler, FARKLI SIRA (yerleştirme sırası)'
                else: kind = 'FARKLI HÜCRELER (erişilebilirlik/komşuluk/yerleşim kuralı)'
                if 'sealed' in g and g['sealed'] != e.get('sealed') and e['placed'] == g['placed']: kind = 'yerleşim aynı ama KİLİTLENME algısı farklı'
                status = f"hamle {i + 1} ({e['color']}): {kind}"; ok_all = False; break
            if len(got) != len(exp) and status == 'OK':
                status = f"hamle sayısı farkı (beklenen {len(exp)}, prototip {len(got)})"; ok_all = False
            report.append((lv['level_id'], case['name'], status))
    for r in report: print(*r)
    print('\nSONUÇ:', 'TAM UYUM' if ok_all else 'FARK VAR')
    if not ok_all:
        print("\nTanı: hangi kural değişkeni prototip izlerini yeniden üretiyor? (tam eşleşen hamle payı)")
        res = []
        for var in VARIANTS:
            tot = match = 0
            for lv in vectors['levels']:
                t = tr.get(lv['level_id'])
                if not t: continue
                for case in lv['cases']:
                    got = None
                    if 'cases' in t:
                        cc = {c['name']: c for c in t['cases']}; got = cc.get(case['name'], {}).get('moves')
                    elif case['name'] == 'winning': got = t.get('moves')
                    if got is None: continue
                    sim = simulate(lv['grid'], lv['W'], case['sequence'], var)
                    for e, g in zip(sim, got):
                        tot += 1; match += int(e['placed'] == g['placed'])
            if tot: res.append((match / tot, var))
        res.sort(key=lambda x: -x[0])
        for frac, var in res[:5]:
            print(f"  {frac:5.1%}  {var}")
        print("  (varsayılan solver kuralı:", DEFAULT, ")")
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('grid-diff'); g.add_argument('solver'); g.add_argument('proto'); g.add_argument('--map')
    v = sub.add_parser('vectors'); v.add_argument('--levels'); v.add_argument('--grid'); v.add_argument('--W', type=int); v.add_argument('--id', default='CAT244'); v.add_argument('--out', required=True)
    c = sub.add_parser('check'); c.add_argument('vectors'); c.add_argument('traces')
    a = ap.parse_args()
    if a.cmd == 'grid-diff':
        cmap = dict(kv.split('=') for kv in a.map.split(',')) if a.map else None
        sys.exit(0 if grid_diff(open(a.solver).read().rstrip('\n'), open(a.proto).read().rstrip('\n'), cmap) else 1)
    if a.cmd == 'vectors':
        levels = []
        if a.levels:
            for lv in json.load(open(a.levels))['levels']:
                levels.append(make_vectors_for(lv['id'], lv['grid'], lv['W'], lv.get('example_winning_sequence')))
        if a.grid:
            levels.append(make_vectors_for(a.id, open(a.grid).read().rstrip('\n'), a.W))
        json.dump(dict(levels=levels), open(a.out, 'w'))
        print('yazıldı:', a.out, '| seviye:', len(levels), '| vaka:', sum(len(l['cases']) for l in levels))
    if a.cmd == 'check':
        sys.exit(0 if check(json.load(open(a.vectors)), json.load(open(a.traces))) else 1)


if __name__ == '__main__':
    main()
