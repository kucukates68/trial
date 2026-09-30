"""Puzzle-yield and resolution-explicit behavioural capacity (PCA + epsilon-packing)."""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
b = load('broad')
m = b.e_moves.replace(0, np.nan)
for c in ['forced', 'free', 'meansafe', 'trap', 'crit']:
    b['sh_' + c] = b['e_' + c] / m
b['algo_free'] = ((b.greedy_fail == 1) & (b.dens_risky >= 0.25)).astype(float)       # greedy fails AND many risky decisions
b['algo_free_strict'] = ((b.greedy_fail == 1) & (b.dens_risky >= 0.25) & (b.rec2 < 1.0) | ((b.greedy_fail == 1) & (b.dens_risky >= 0.4))).astype(float)
print("PUZZLE VERİMİ = greedy başarısız VE riskli karar yoğunluğu >= 0.25 (çözülebilir adaylar içinde pay)")
print("tümü:", round(b.algo_free.mean(), 3), "| n=", len(b))
for fac in ['cm', 'family', 'src', 'bin']:
    t = b.groupby(fac)[['greedy_fail', 'algo_free']].mean().round(3); t['dens_risky'] = b.groupby(fac).dens_risky.mean().round(3)
    print(f"\n{fac}:"); print(t.to_string()); save(t, f'puzzle_yield_by_{fac}')
# high density but greedy-solvable ('algorithmic')
alg = b[(b.dens_risky >= 0.25) & (b.greedy_fail == 0)]
print("\ndens_risky>=0.25 ama greedy ÇÖZÜYOR: %d aday (%.1f%% of dens_risky>=0.25)" % (len(alg), 100 * len(alg) / (b.dens_risky >= 0.25).sum()))
print(alg.groupby('cm').size().sort_values(ascending=False).head(5).to_dict())
# fixed-CM2 style: which (cm,family,bin) give yield>=0.5
y = b.groupby(['cm', 'family']).algo_free.mean().unstack()
print("\nPuzzle verimi (CM × erişim)"); print(y.round(2).to_string()); save(y, 'puzzle_yield_cm_x_family')

# ---------------------------------------------------------------- capacity
feats = ['dens_risky', 'sh_crit', 'sh_trap', 'sh_meansafe', 'sh_free', 'sh_forced', 'trap_timing', 'trap_sharp', 'regret_max', 'rec1',
         'log_seq_canon_per_move', 'greedy_fail', 'risk', 'win_undo2']
X = b[feats].copy()
X['trap_timing'] = X['trap_timing'].fillna(X['trap_timing'].median()); X['trap_sharp'] = X['trap_sharp'].fillna(0)
X = X.fillna(0)
Z = (X - X.mean()) / X.std().replace(0, 1)
U, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
ev = S ** 2 / (S ** 2).sum()
print("\nPCA (davranış vektörü, 14 özellik): açıklanan varyans", np.round(ev[:8], 3), "| 90%% için PC=%d | 95%% için PC=%d" % ((np.cumsum(ev) < 0.90).sum() + 1, (np.cumsum(ev) < 0.95).sum() + 1))
k = int((np.cumsum(ev) < 0.95).sum() + 1)
P = U[:, :k] * S[:k]
P = P / P[:, 0].std()                                        # 1 unit = 1 std of first PC
def packing(P, eps, seed):
    rng = np.random.default_rng(seed); idx = rng.permutation(len(P)); reps = []
    for i in idx:
        if not reps or np.min(np.linalg.norm(P[reps] - P[i], axis=1)) >= eps:
            reps.append(i)
    return reps
rows = []
for eps in [0.15, 0.25, 0.4, 0.6, 0.9]:
    v = [len(packing(P, eps, s)) for s in range(5)]
    sub = {}
    for name, mask in [('cat', b.src.values == 'cat'), ('OPEN', b.layout.values == 'OPEN')]:
        sub[name] = np.mean([len(packing(P[mask], eps, s)) for s in range(5)])
    half = np.random.default_rng(0).permutation(len(P))[:len(P) // 2]
    rows.append(dict(eps=eps, tüm_adaylar=np.mean(v), yarı_örnek=np.mean([len(packing(P[half], eps, s)) for s in range(5)]), yalnız_cat=sub['cat'], yalnız_OPEN=sub['OPEN']))
R = pd.DataFrame(rows).round(1)
print("\nε-paketleme (birbirinden ≥ε uzak davranış temsilcisi sayısı); ε birimi: PC1 std"); print(R.to_string(index=False)); save(R.set_index('eps'), 'capacity_eps_packing')
# how many silhouettes are needed? packing count vs number of silhouettes (eps=0.4)
sil = sorted(b.src.unique()); out = []
for n in range(1, len(sil) + 1):
    mk = b.src.isin(sil[:n]).values
    out.append((n, np.mean([len(packing(P[mk], 0.4, s)) for s in range(3)])))
print("\nε=0.4: silüet sayısı -> temsilci:", [(n, round(v, 1)) for n, v in out])
out = []
for n in range(1, 11):
    cms = sorted(b.cm.unique())[:n]; mk = b.cm.isin(cms).values
    out.append((n, np.mean([len(packing(P[mk], 0.4, s)) for s in range(3)])))
print("ε=0.4: renk haritası sayısı -> temsilci:", [(n, round(v, 1)) for n, v in out])
out = []
for n, lays in [(1, ['OPEN']), (3, ['OPEN', 'COR1', 'BOT1']), (6, ['OPEN', 'COR1', 'BOT1', 'SPL1', 'SPB1', 'MUL1']), (18, sorted(b.layout.unique()))]:
    mk = b.layout.isin(lays).values; out.append((n, np.mean([len(packing(P[mk], 0.4, s)) for s in range(3)])))
print("ε=0.4: erişim düzeni sayısı -> temsilci:", [(n, round(v, 1)) for n, v in out])
