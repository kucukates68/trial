"""Phase 1: distributions, drivers and redundancy of the upgraded metrics (broad_v2)."""
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)

v = load('broad_v2'); old = load('broad')
key = ['src', 'cm', 'layout', 'bin']
j = v.set_index(key)[['dens_risky', 'e_risky', 'e_crit', 'seq_raw', 'greedy_deep']].join(old.set_index(key)[['dens_risky', 'e_risky', 'e_crit', 'seq_raw', 'greedy_deep']], rsuffix='_old', how='inner')
print("== A) YENİDEN ÜRETİLEBİLİRLİK (broad_v2 vs broad)  n =", len(j))
print("max |Δ dens_risky| =", float((j.dens_risky - j.dens_risky_old).abs().max()), "| max |Δ e_crit| =", float((j.e_crit - j.e_crit_old).abs().max()),
      "| greedy farkı =", int((j.greedy_deep != j.greedy_deep_old).sum()))

v['puzzle_yield'] = ((v.greedy_fail == 1) & (v.dens_risky >= 0.25)).astype(float)
has = v[v.dh_exp_mean.notna()].copy()
print("\nmistake_mass>0 olan (hata yapılabilir) aday:", len(has), "/", len(v))
cols = ['visible_mean', 'safe_mean', 'mbf_mean', 'cpr_risky', 'hazard_mean', 'dh_exp_mean', 'dh_min_mean', 'dh_max_mean', 'dh_p50', 'dh_instant_share', 'dh_latent_share',
        'dh_band35_share', 'blind_progress_mean', 'blind_progress_ge5_share', 'latent_doom_mass', 'abc_initial', 'abc_mean', 'abc_max_dag', 'abc_ge3_share', 'abc_early', 'abc_mid', 'abc_late',
        'abc_distinct_path', 'abc_concurrency', 'pp_locked_mean', 'pp_locked_max', 'closure_at_40pct', 'closure_lead_max', 'corr_progress_hazard', 'corr_progress_locked',
        'filler_ratio', 'filler_strict', 'filler_to_decision', 'e_moves', 'e_meaningful', 'e_risky', 'e_crit', 'e_forced']
def desc(d):
    return d[cols].describe(percentiles=[.1, .5, .9]).T[['count', 'mean', '10%', '50%', '90%']].round(3)
print("\n== B) DAĞILIMLAR: tüm çözülebilir adaylar"); T = desc(v); print(T.to_string()); save(T, 'phase2_metric_distribution_all')
y = v[v.puzzle_yield == 1]
print("\n   puzzle verimi adayları (greedy başarısız & dens_risky>=0.25), n =", len(y)); T2 = desc(y); print(T2.to_string()); save(T2, 'phase2_metric_distribution_yield')

# ------------------------------------------------ interpretation helpers
print("\n== C) DEADLOCK HORIZON")
print("Hata kütlesinin payı: anında kilitlenen %.3f | gecikmeli (DH>=2) %.3f (tüm adaylarda, hata kütlesi ağırlıklı)" %
      ((has.dh_instant_share * has.mistake_mass).sum() / has.mistake_mass.sum(), 1 - (has.dh_instant_share * has.mistake_mass).sum() / has.mistake_mass.sum()))
print("Adayların DH_exp dağılımı: <1.5: %.2f | 1.5–3: %.2f | 3–5: %.2f | >5: %.2f" % ((has.dh_exp_mean < 1.5).mean(), ((has.dh_exp_mean >= 1.5) & (has.dh_exp_mean < 3)).mean(),
      ((has.dh_exp_mean >= 3) & (has.dh_exp_mean <= 5)).mean(), (has.dh_exp_mean > 5).mean()))
print("Hata-kütlesi ağırlıklı, DH_exp∈[3,5] payı (aday ortalaması): %.3f ; en az %%10 hata kütlesi bu bantta olan aday: %.3f" % (has.dh_band35_share.mean(), (has.dh_band35_share >= 0.10).mean()))
print("Kör ilerleme (hata sonrası kilitlenme görünene dek resmin tamamlanan payı): ort %.3f | ≥%%5 olan aday payı %.3f" % (has.blind_progress_mean.mean(), (has.blind_progress_mean >= 0.05).mean()))
for fac in ['cm', 'family']:
    t = has.groupby(fac)[['dh_exp_mean', 'dh_instant_share', 'dh_band35_share', 'blind_progress_mean', 'latent_doom_mass']].mean().round(3)
    print(f"\n   {fac} bazında:"); print(t.to_string()); save(t, f'phase2_dh_by_{fac}')
print("\n   W/dalga kovası:"); print(has.groupby('bin')[['dh_exp_mean', 'dh_instant_share', 'blind_progress_mean']].mean().round(3).to_string())

print("\n== D) PATH PRESSURE / CLOSURE")
print("closure_at_40pct: dolu (nan olmayan) aday", int(v.closure_at_40pct.notna().sum()), "| ortalama", round(v.closure_at_40pct.mean(), 4), "| closure_lead_max ortalama", round(v.closure_lead_max.mean(), 4))
print("=> kazanan yolda 'kritik geçitler ilerlemeden önce kapanmış' durumu yapısal olarak yok (kapanış yalnız bağımlılar dolunca güvenli).")
print("pp_locked (kilitli boş-hücre payı): ortalama %.3f, tepe (aday ort.) %.3f | corr(ilerleme, kilitli pay) medyan %.2f | corr(ilerleme, hazard) medyan %.2f (pozitif aday payı %.2f)" %
      (v.pp_locked_mean.mean(), v.pp_locked_max.mean(), v.corr_progress_locked.median(), v.corr_progress_hazard.median(), (v.corr_progress_hazard > 0).mean()))

print("\n== E) BRANCHING")
print("Görünür seçenek ort %.2f (renk sayısı 3) | güvenli seçenek ort %.2f | anlamlı (kümelenmiş) seçenek ort %.2f" % (v.visible_mean.mean(), v.safe_mean.mean(), v.mbf_mean.mean()))
print("kritik durumlarda CPR (güvenli/yasal) ort %.2f (kolay≈0.67, zor≈0.33 referansı Gemini §17)" % v.cpr_risky.mean())
print("anlamlı/görünür oran: ort %.2f ; puzzle verimi adaylarında %.2f" % (v.mbf_over_visible.mean(), y.mbf_over_visible.mean()))

print("\n== F) ACTIVE BOTTLENECK COUNT")
print("abc_mean ort %.2f | abc_max_dag ort %.1f | eşzamanlı (>=3) hamle payı %.2f | yol başına farklı dar boğaz %.1f | eşzamanlılık %.2f" %
      (v.abc_mean.mean(), v.abc_max_dag.mean(), v.abc_ge3_share.mean(), v.abc_distinct_path.mean(), v.abc_concurrency.mean()))
print("ilerleme üçte birleri (erken/orta/geç) abc:", v[['abc_early', 'abc_mid', 'abc_late']].mean().round(2).to_dict())
for fac in ['cm', 'family']:
    t = v.groupby(fac)[['abc_initial', 'abc_mean', 'abc_ge3_share', 'abc_concurrency', 'pp_locked_mean', 'e_risky']].mean().round(2)
    print(f"\n   {fac} bazında:"); print(t.to_string()); save(t, f'phase2_abc_by_{fac}')

print("\n== G) FILLER / DECISION")
print("filler_ratio ort %.3f (p10 %.2f, p50 %.2f, p90 %.2f) | strict %.3f | puzzle-verimi adaylarında %.3f" % (v.filler_ratio.mean(), *v.filler_ratio.quantile([.1, .5, .9]), v.filler_strict.mean(), y.filler_ratio.mean()))

# ------------------------------------------------ drivers (eta^2)
print("\n== H) SÜRÜCÜLER (η², çözülebilir adaylar; src, cm, layout, bin)")
rows = {}
for r in ['dh_exp_mean', 'dh_instant_share', 'blind_progress_mean', 'visible_mean', 'mbf_mean', 'cpr_risky', 'abc_mean', 'abc_ge3_share', 'abc_concurrency', 'pp_locked_mean', 'filler_ratio']:
    d = v[v[r].notna()]
    t, r2 = anova_eta(d, r, ['src', 'cm', 'layout', 'bin'])
    rows[r] = {k: round(float(t.loc[k, 'eta2']), 3) for k in ['src', 'cm', 'layout', 'bin', 'src:cm', 'cm:layout']} | {'n': len(d)}
E = pd.DataFrame(rows).T; print(E.to_string()); save(E, 'phase2_eta2_new_metrics')

# ------------------------------------------------ redundancy
print("\n== I) METRİKLER ARASI ÖRTÜŞME (Spearman)")
m = ['dh_exp_mean', 'dh_instant_share', 'blind_progress_mean', 'abc_mean', 'abc_ge3_share', 'pp_locked_mean', 'mbf_mean', 'cpr_risky', 'filler_ratio', 'e_risky', 'e_crit', 'dens_risky', 'rec1']
C = v[m].corr(method='spearman').round(2); print(C.to_string()); save(C, 'phase2_metric_correlations')
Z = v[m].fillna(v[m].median()); Z = (Z - Z.mean()) / Z.std()
ev = np.linalg.eigvalsh(np.cov(Z.values.T))[::-1]; ev = ev / ev.sum()
print("PCA açıklanan varyans:", np.round(ev[:6], 3), "| %90 için bileşen:", int((np.cumsum(ev) < 0.9).sum() + 1))
