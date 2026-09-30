"""one-off: make seq_raw/seq_canon JSON-safe for pandas (adds log10_* columns)."""
import json, math, sys, glob
for p in glob.glob('results/*.jsonl'):
    out = []
    for line in open(p):
        r = json.loads(line)
        for key in ('seq_raw', 'seq_canon'):
            v = r.get(key)
            if isinstance(v, int):
                r['log10_' + key] = math.log10(v) if v > 0 else 0.0
                if v > 2 ** 53:
                    r[key] = float(v)
        out.append(json.dumps(r))
    open(p, 'w').write('\n'.join(out) + '\n')
    print(p, len(out))
