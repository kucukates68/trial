import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
R = load('refine', solvable=False)
R['series'] = R.src + '|' + R.cm + '|' + R.layout
R['yield'] = ((R.greedy_fail == 1) & (R.dens_risky >= 0.25)).astype(float)
print("== YÜKSEK ÇÖZÜNÜRLÜKLÜ W TARAMASI (en verimli 48 bölge × W=1..32) ==  satır", len(R))
print("çözülebilir pay:", round(R.solv.mean(), 3), "| W=1 greedy başarısı:", R[(R.W == 1) & R.solv].greedy_deep.mean())
ok = R[R.solv]
t = ok.groupby('W').agg(n=('yield', 'size'), greedy_fail=('greedy_fail', 'mean'), yield_=('yield', 'mean'), dens_risky=('dens_risky', 'mean'),
                         e_risky=('e_risky', 'mean'), waves=('waves_nominal', 'mean')).round(3)
print(t.to_string()); save(t, 'refine_by_W')
# sweet spot per region: W maximizing e_risky subject to greedy failing and solvable; and its waves
rows = []
for s, g in ok.groupby('series'):
    gg = g[g.greedy_fail == 1]
    if len(gg) == 0:
        rows.append(dict(series=s, has_greedy_fail_W=0)); continue
    b = gg.loc[gg.e_risky.idxmax()]
    rows.append(dict(series=s, has_greedy_fail_W=1, W=int(b.W), waves=b.waves_nominal, e_risky=b.e_risky, dens_risky=b.dens_risky,
                     n_W_with_greedy_fail=len(gg), n_W_solvable=len(g), first_W_greedy_fail=int(gg.W.min()), last_W_solvable=int(g.W.max())))
S = pd.DataFrame(rows)
print("\nBölge başına: greedy'nin başarısız olduğu en az bir W var mı:", S.has_greedy_fail_W.mean().round(3))
print(S.dropna().describe().round(2).to_string())
print("\nZirve e_risky veren W'nin dalga sayısı dağılımı:", S.dropna().waves.round().value_counts().sort_index().to_dict())
S.to_csv(f'{SUM}/refine_sweet_spots.csv', index=False)
# how wide is the 'good W' window? fraction of W in which a region is solvable AND greedy fails AND dens>=0.25
win = ok.groupby('series').agg(good=('yield', 'sum'), solvable=('yield', 'size'))
print("\nBölge başına 'verimli' W sayısı (çözülebilir, greedy başarısız, dens>=0.25): medyan %.0f, ortalama %.1f (çözülebilir W medyan %.0f)" % (win.good.median(), win.good.mean(), win.solvable.median()))
# contiguity of good-W window
cont = []
for s, g in ok.groupby('series'):
    w = g.sort_values('W'); y = w['yield'].values.astype(int)
    if y.sum() == 0: continue
    idx = np.where(y == 1)[0]; cont.append((idx.max() - idx.min() + 1 - len(idx)))
print("verimli W penceresi içindeki 'delik' sayısı (ortalama):", round(np.mean(cont), 2), "; hiç delik olmayan bölge payı:", round(np.mean(np.array(cont) == 0), 2))

L = load('refine_layout', solvable=False)
L['yield'] = ((L.greedy_fail == 1) & (L.dens_risky >= 0.25)).astype(float)
print("\n== ERİŞİM KOMŞULUK TARAMASI (en iyi 24 bölgenin tek-port değişimleri) ==  satır", len(L), "| çözülebilir", round(L.solv.mean(), 3))
lo = L[L.solv]
L['base'] = L.src + '|' + L.cm
print("komşu düzenlerde verim: ortalama %.3f ; OPEN olmayan" % lo['yield'].mean())
byfam = lo.groupby('family').agg(n=('yield', 'size'), yield_=('yield', 'mean'), dens_risky=('dens_risky', 'mean'), greedy_fail=('greedy_fail', 'mean')).round(3)
print(byfam.to_string()); save(byfam, 'refine_layout_by_family')
# how many distinct behaviours does the neighbourhood of ONE colour map + geometry produce?
rows = []
for base, g in lo.groupby(lo.src + '|' + lo.cm):
    rows.append(dict(base=base, n=len(g), n_layouts=g.layout.nunique(), yield_share=g['yield'].mean(),
                     dens_min=g.dens_risky.min(), dens_max=g.dens_risky.max(), greedy_fail_share=g.greedy_fail.mean()))
B = pd.DataFrame(rows).round(3); print(B.head(12).to_string(index=False)); B.to_csv(f'{SUM}/refine_layout_bases.csv', index=False)
print("\nTek (silüet,CM) sabitken erişim komşulukları: verimli (greedy başarısız & dens>=0.25) adaylar ortalama pay =", round(B.yield_share.mean(), 3), "; dens_risky aralığı ortalama", round((B.dens_max - B.dens_min).mean(), 3))
