import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
b = load('broad')
fams = ['OPEN', 'CORRIDOR', 'BOTTLENECK', 'SPLIT', 'SPLIT+BOTTLENECK', 'MULTI']
for resp in ['dens_risky', 'greedy_fail', 'e_risky']:
    t = b.pivot_table(index='cm', columns='family', values=resp, aggfunc='mean')[fams].round(2)
    print(f"\n== {resp}: renk haritası × erişim ailesi (çözülebilir adaylar)"); print(t.to_string()); save(t, f'interaction_cm_x_family_{resp}')
# range decomposition: how much does geometry (access) vs colour move the response?
print("\n== Aralık karşılaştırması (dens_risky): erişimi değiştirince vs renk haritasını değiştirince")
rows = []
for shp, g in b.groupby('src'):
    acc = g.groupby(['cm', 'layout']).dens_risky.mean().unstack('layout')          # rows cm, cols layout
    rng_layout = (acc.max(axis=1) - acc.min(axis=1)).mean()                        # fix cm, vary layout
    rng_cm = (acc.max(axis=0) - acc.min(axis=0)).mean()                            # fix layout, vary cm
    rows.append((shp, rng_layout, rng_cm))
R = pd.DataFrame(rows, columns=['silüet', 'erişim_değişince_aralık', 'renk_haritası_değişince_aralık']).round(3)
print(R.to_string(index=False)); print("ortalama:", R.iloc[:, 1:].mean().round(3).to_dict()); save(R.set_index('silüet'), 'range_layout_vs_cm')
# silhouette effect when cm and layout are fixed
sil = b.groupby(['cm', 'layout', 'bin']).dens_risky.agg(lambda s: s.max() - s.min()).mean()
print("silüet değişince (cm, erişim, bin sabit) ortalama aralık:", round(sil, 3))
# can a hard access rescue a boring colour map? can a good colour map survive an open plaza?
print("\nSıkıcı renk haritası (CM1) + zor erişim vs zengin renk haritası (CM7/CM8) + açık meydan:")
for cm in ['CM1', 'CM3', 'CM7', 'CM8']:
    print(f"  {cm}: OPEN dens_risky={b[(b.cm == cm) & (b.family == 'OPEN')].dens_risky.mean():.3f} | BOTTLENECK={b[(b.cm == cm) & (b.family == 'BOTTLENECK')].dens_risky.mean():.3f} | SPLIT+BOTTLENECK={b[(b.cm == cm) & (b.family == 'SPLIT+BOTTLENECK')].dens_risky.mean():.3f}")
# greedy success by combination: where is greedy fail >= 50%
g = b.groupby(['cm', 'family']).greedy_fail.mean().unstack()[fams]
print("\ngreedy başarısızlığı >=%50 olan (CM, aile) hücreleri:", [(i, c, round(v, 2)) for i in g.index for c, v in g.loc[i].items() if v >= 0.5])
# interaction W x CM (from wsweep already) and image-size x W handled in an_w/an_size_ab
