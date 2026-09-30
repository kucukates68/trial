import pandas as pd, numpy as np, warnings, itertools, random
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
b = load('broad'); w = load('wsweep')


def shares(d):
    m = d.e_moves.replace(0, np.nan)
    for c in ['forced', 'free', 'meansafe', 'trap', 'crit']:
        d['sh_' + c] = d['e_' + c] / m
    return d


b = shares(b)
print("== KARAR SINIFI PAYLARI (beklenen hamle payı, güvenli-tekdüze politika) ==")
for fac in ['family', 'cm', 'bin']:
    t = b.groupby(fac)[['sh_forced', 'sh_free', 'sh_meansafe', 'sh_trap', 'sh_crit']].mean().round(3)
    print(t.to_string()); save(t, f'taxonomy_by_{fac}')
print("tümü:", b[['sh_forced', 'sh_free', 'sh_meansafe', 'sh_trap', 'sh_crit']].mean().round(3).to_dict())
print("silüet bazında min/max:", b.groupby('src')[['sh_free', 'sh_meansafe', 'sh_trap', 'sh_crit']].mean().round(3).agg(['min', 'max']).to_dict())


# ----------------------------------------------------------- signatures
def bins(d, tq):
    d = d.copy()
    d['b_risky'] = pd.cut(d.dens_risky, [-1, 0.1, 0.25, 0.5, 9], labels=['<.1', '.1-.25', '.25-.5', '>.5']).astype(str)
    d['b_crit'] = pd.cut(d.crit_share.fillna(-1), [-2, -0.5, 0.35, 0.65, 9], labels=['none', '<.35', '.35-.65', '>.65']).astype(str)
    d['b_time'] = pd.cut(d.trap_timing.fillna(-1), [-2, -0.5, 0.35, 0.6, 9], labels=['none', 'early', 'mid', 'late']).astype(str)
    d['b_first'] = d.first_trap.astype(int).astype(str)
    d['b_reg'] = np.minimum(d.regret_max, 3).astype(int).astype(str)
    d['b_rec1'] = (d.rec1 >= 0.9).astype(int).astype(str)
    d['b_ord'] = pd.cut(d.log_seq_canon_per_move, tq, labels=['o1', 'o2', 'o3']).astype(str)
    sh = d[['sh_forced', 'sh_free', 'sh_meansafe', 'sh_trap', 'sh_crit']].fillna(0)
    d['b_type'] = sh.idxmax(axis=1).str.replace('sh_', '')
    d['sig_dec'] = d.b_risky + '|' + d.b_crit + '|' + d.b_type
    d['sig_time'] = d.b_time + '|' + d.b_first
    d['sig_reg'] = d.b_reg + '|' + d.b_rec1
    d['sig_ord'] = d.b_ord
    d['sig_all'] = d.sig_dec + '#' + d.sig_time + '#' + d.sig_reg + '#' + d.sig_ord
    return d


tq = [-1] + list(b.log_seq_canon_per_move.quantile([1 / 3, 2 / 3])) + [9]
b = bins(b, tq)


def div(series):
    vc = series.value_counts()
    return len(vc), shannon(vc.values), 2 ** shannon(vc.values), chao1(vc.values)


rows = []
for name in ['sig_dec', 'sig_time', 'sig_reg', 'sig_ord', 'sig_all']:
    n, H, eff, ch = div(b[name])
    rows.append(dict(boyut=name, gözlenen=n, entropi_bit=round(H, 2), etkin_sayı=round(eff, 1), chao1=round(ch, 1)))
print("\n== ÇEŞİTLİLİK (tüm çözülebilir broad adaylar, n=%d) ==" % len(b))
R = pd.DataFrame(rows); print(R.to_string(index=False)); save(R.set_index('boyut'), 'diversity_dimensions_all')
print("\nAlt popülasyon başına: aday / farklı sig_all / etkin sayı / chao1")
for fac in ['src', 'family', 'cm', 'bin']:
    t = []
    for k, g in b.groupby(fac):
        n, H, eff, ch = div(g.sig_all); t.append((k, len(g), n, round(eff, 1), round(ch, 1)))
    print(pd.DataFrame(t, columns=[fac, 'n', 'distinct', 'eff', 'chao1']).to_string(index=False))


def rarefy(series, sizes, reps=40, seed=3):
    rng = np.random.default_rng(seed); arr = series.values; out = []
    for s in sizes:
        if s > len(arr): continue
        out.append((s, np.mean([len(set(rng.choice(arr, s, replace=False))) for _ in range(reps)])))
    return out


sizes = [25, 50, 100, 200, 400, 800, 1600, 3200]
print("\nRarefaction (n aday -> beklenen farklı joint imza), tüm popülasyon:", [(s, round(v, 1)) for s, v in rarefy(b.sig_all, sizes)])
print("Rarefaction yalnız 'cat' (tek geometri; tüm CM×erişim×bin):", [(s, round(v, 1)) for s, v in rarefy(b[b.src == 'cat'].sig_all, [25, 50, 100, 200, 400])])
print("Rarefaction yalnız OPEN erişim:", [(s, round(v, 1)) for s, v in rarefy(b[b.layout == 'OPEN'].sig_all, [25, 50, 100, 200])])


def vary(df, ctx):
    res = []
    for k, g in df.groupby(ctx):
        if len(g) >= 2: res.append(g.sig_all.nunique())
    return np.mean(res), np.mean(np.array(res) >= 2), len(res)


print("\n'Tek faktör değişir, diğerleri sabit' -> bağlam başına ort. farklı imza (≥2 imza veren bağlam payı):")
for fac, lv in [('cm', 10), ('layout', 18), ('src', 8), ('bin', 3)]:
    ctx = [c for c in ['src', 'cm', 'layout', 'bin'] if c != fac]; m, p, n = vary(b, ctx)
    print(f"  {fac:7} ({lv} düzey) ort.farklı imza={m:.2f}  ≥2 imza veren bağlam={p:.2f}  bağlam={n}")
w2 = bins(shares(w.copy()), tq)
m, p, n = vary(w2, ['src', 'cm', 'layout']); print(f"  W (14 düzey, wsweep) ort.farklı imza={m:.2f}  ≥2 imza veren bağlam={p:.2f}  bağlam={n}")
print("\nBirikimli farklı imza (düzeyler eklendikçe):")
for fac in ['cm', 'layout', 'src', 'bin']:
    lv = sorted(b[fac].unique()); cur = set(); curve = []
    for x in lv:
        cur |= set(b[b[fac] == x].sig_all); curve.append(len(cur))
    print(f"  {fac}: {curve}")
for lab, rb in [('kaba', [-1, 0.25, 9]), ('ince', [-1, 0.05, 0.1, 0.15, 0.25, 0.35, 0.5, 0.7, 9])]:
    d = b.copy(); d['sr'] = pd.cut(d.dens_risky, rb).astype(str); d['sg'] = d.sr + d.b_type + d.b_time + d.b_reg + d.b_ord
    print(f"imza çözünürlüğü {lab}: farklı={d.sg.nunique()}")
b.to_csv(f'{SUM}/broad_with_signatures.csv', index=False)
