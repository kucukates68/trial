"""jsonl -> csv.gz (repo-friendly).  Raw candidate tables keep every solver metric + colour/entrance descriptors."""
import glob, os, pandas as pd
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
for p in sorted(glob.glob(os.path.join(R, '*.jsonl'))):
    df = pd.read_json(p, lines=True)
    out = p[:-len('.jsonl')] + '.csv.gz'
    df.to_csv(out, index=False, compression='gzip')
    print(os.path.basename(out), df.shape, round(os.path.getsize(out) / 1e6, 2), 'MB')
