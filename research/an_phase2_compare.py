"""Phase 2: behaviour-profile comparison against the filtered benchmark envelope (NOT targets)."""
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)

ref = json.load(open(f'{HERE}/benchmark_reference.json'))
claims = {c['id']: c for c in ref['claims']}
# dimension table: (claim id, our column, tolerance minimum)
DIMS = [('action_space', 'visible_mean', 1.0), ('critical_decisions', 'e_risky', 1.0), ('recovery_horizon', 'dh_exp_mean', 1.0),
        ('no_instant_death', 'dh_instant_share', 0.05),
        ('total_moves', 'e_moves', 5.0), ('filler_ratio', 'filler_ratio', 0.05), ('trap_timing', 'trap_timing', 0.05)]


def envelope(cid, tol_min):
    lo, hi = claims[cid]['range']
    w = hi - lo
    t = max(0.25 * w, tol_min)
    return lo, hi, lo - t, hi + t, claims[cid]['weight']


def score(df):
    out = df.copy()
    num_core = num_tol = den = 0.0
    a_tol = []; a_den = 0
    flags = {}
    for cid, col, tm in DIMS:
        lo, hi, tlo, thi, w = envelope(cid, tm)
        x = out[col]
        valid = x.notna()
        core = (x >= lo) & (x <= hi)
        tol = (x >= tlo) & (x <= thi)
        out['in_core_' + cid] = np.where(valid, core, np.nan)
        out['in_tol_' + cid] = np.where(valid, tol, np.nan)
        num_core = num_core + np.where(valid, core, 0) * w
        num_tol = num_tol + np.where(valid, tol, 0) * w
        den = den + valid.astype(float) * w
        if claims[cid]['gemini_class'] == 'A':
            a_tol.append(np.where(valid, tol, 0)); a_den = a_den + valid.astype(float)
    out['cov_core'] = num_core / den
    out['cov_tol'] = num_tol / den
    out['covA_tol'] = np.sum(a_tol, axis=0) / a_den
    return out


v = load('broad_v2')
v['puzzle_yield'] = ((v.greedy_fail == 1) & (v.dens_risky >= 0.25)).astype(float)
S = score(v)
print("== ZARF (çekirdek / toleranslı)")
for cid, col, tm in DIMS:
    lo, hi, tlo, thi, w = envelope(cid, tm)
    print(f"  {cid:20} sınıf={claims[cid]['gemini_class']} ağırlık={w}  çekirdek=[{lo:g},{hi:g}]  toleranslı=[{tlo:.2f},{thi:.2f}]  ↔ {col}")

print("\n== BOYUT BOYUT: aday payı (çekirdek | toleranslı) ve bizim medyan")
rows = []
for cid, col, tm in DIMS:
    x = S[col].dropna(); lo, hi, tlo, thi, w = envelope(cid, tm)
    med = x.median()
    pos = 'altında' if med < lo else ('üstünde' if med > hi else 'içinde')
    rows.append(dict(boyut=cid, sinif=claims[cid]['gemini_class'], bizim_medyan=round(med, 3), p10=round(x.quantile(.1), 3), p90=round(x.quantile(.9), 3),
                     çekirdek_pay=round(S['in_core_' + cid].mean(), 3), toleranslı_pay=round(S['in_tol_' + cid].mean(), 3), medyan_zarfa_göre=pos))
T = pd.DataFrame(rows); print(T.to_string(index=False)); save(T.set_index('boyut'), 'phase2_envelope_by_dimension')

print("\n== KAPSAMA (aday başına ağırlıklı pay)")
print("çekirdek: ort %.3f | toleranslı: ort %.3f | yalnız-A toleranslı: ort %.3f" % (S.cov_core.mean(), S.cov_tol.mean(), S.covA_tol.mean()))
allA = (S.in_tol_action_space == 1) & (S.in_tol_critical_decisions == 1) & (S.in_tol_recovery_horizon == 1)
print("Üç 'A' boyutunun hepsi toleranslı zarfta: %d aday (%.2f%%)" % (allA.sum(), 100 * allA.mean()))
for drop in ['recovery_horizon', 'action_space']:
    keep = [c for c in ['action_space', 'critical_decisions', 'recovery_horizon'] if c != drop]
    m = np.all([S['in_tol_' + c] == 1 for c in keep], axis=0)
    print(f"  {drop} HARİÇ diğer A boyutları zarfta: {m.sum()} aday (%{100 * m.mean():.1f})")
print("Yukarıdaki üçünden yalnız e_risky ve e_moves+filler+timing (karar yapısı boyutları) zarfta:", int(((S.in_tol_critical_decisions == 1) & (S.in_tol_total_moves == 1) & (S.in_tol_filler_ratio == 1) & (S.in_tol_trap_timing == 1)).sum()))

print("\n== HANGİ BÖLGELER ZARFA YAKIN? (toleranslı kapsama ortalaması)")
for fac in ['cm', 'family', 'src', 'bin']:
    t = S.groupby(fac)[['cov_tol', 'covA_tol', 'in_tol_critical_decisions', 'in_tol_recovery_horizon', 'in_tol_filler_ratio', 'in_tol_trap_timing']].mean().round(2)
    print(f"\n{fac}:"); print(t.to_string()); save(t, f'phase2_envelope_cov_by_{fac}')
yy = S[S.puzzle_yield == 1]
print("\nPuzzle verimi adaylarında (n=%d): kapsama toleranslı %.2f | A-toleranslı %.2f | kritik karar zarfta %.2f | zarf içi DH %.2f | filler zarfta %.2f | trap zamanı zarfta %.2f" %
      (len(yy), yy.cov_tol.mean(), yy.covA_tol.mean(), yy.in_tol_critical_decisions.mean(), yy.in_tol_recovery_horizon.mean(), yy.in_tol_filler_ratio.mean(), yy.in_tol_trap_timing.mean()))

print("\n== TUZAK ZAMANI (risky durumların ort. ilerlemesi) ve son faz")
print("trap_timing medyan %.2f (p10 %.2f, p90 %.2f) | risky_late payı (son üçte bir) ort %.3f" % (S.trap_timing.median(), S.trap_timing.quantile(.1), S.trap_timing.quantile(.9),
      (S.risky_late / (S.risky_early + S.risky_mid + S.risky_late)).mean()))

print("\n== RECOVERY HORIZON: zarfa yaklaşan adaylar")
hh = S[S.dh_exp_mean >= 2.0].sort_values('dh_exp_mean', ascending=False)
print("dh_exp_mean >= 2 olan aday: %d (%.1f%%)" % (len(hh), 100 * len(hh) / S.dh_exp_mean.notna().sum()))
if len(hh):
    print(hh.groupby('cm').size().sort_values(ascending=False).to_dict(), hh.groupby('family').size().sort_values(ascending=False).to_dict())
    print(hh[['src', 'cm', 'layout', 'W', 'waves_nominal', 'dh_exp_mean', 'dh_instant_share', 'latent_doom_mass', 'blind_progress_mean', 'e_risky', 'dens_risky', 'greedy_fail', 'rec1']].head(10).round(2).to_string(index=False))
    print("   bunların ortalaması: e_risky %.2f, dens_risky %.2f, greedy_fail %.2f, rec1 %.2f, solv-oranı(cm içinde) düşük mü? -> CM5/7 ağırlıklı" % (hh.e_risky.mean(), hh.dens_risky.mean(), hh.greedy_fail.mean(), hh.rec1.mean()))

# ------------------------------------------------ DRV proxies
print("\n== DECISION RECOVERY VISIBILITY (solver vekilleri; UI düzeyi DEĞİL)")
has = S[S.mistake_mass > 0]
mm = has.mistake_mass
print("Hata kütlesi ağırlıklı: aynı hamlede görünür (DH=1) %.3f | gecikmeli %.3f" % ((has.dh_instant_share * mm).sum() / mm.sum(), 1 - (has.dh_instant_share * mm).sum() / mm.sum()))
print("Hatalı hamlenin KENDİ ilerlemesi ≈ 1/dalga: kör ilerleme ~ waves ile ilişki: Spearman(blind_progress, 1/waves) = %.2f" % has.blind_progress_mean.corr(1 / has.waves_nominal, method='spearman'))
print("Kör ilerleme − (1/dalga) ortalama fark: %.3f  (≈0 ise 'kör ilerleme' tek başına hatalı dalganın kendisi)" % (has.blind_progress_mean - 1 / has.waves_nominal).mean())
print("Gecikmeli hata kütlesi (oyun başına beklenen sayı, latent_doom_mass): ort %.3f ; puzzle verimi %.3f ; CM5 %.2f CM7 %.2f CM8 %.2f" %
      (S.latent_doom_mass.mean(), yy.latent_doom_mass.mean(), *[S[S.cm == c].latent_doom_mass.mean() for c in ('CM5', 'CM7', 'CM8')]))
print("İlerleme-tehlike ilişkisi (kazanan yolda): corr(ilerleme, hazard) medyan %.2f, pozitif %.2f ; corr(ilerleme, kilitli-pay) medyan %.2f" % (S.corr_progress_hazard.median(), (S.corr_progress_hazard > 0).mean(), S.corr_progress_locked.median()))

# ------------------------------------------------ 244-box style question: size_v2
z = load('size_v2')
z = score(z)
z['real'] = ~z.src.str.startswith('syn:')
print("\n== BOYUT PROXY'LERİ (size_v2): hücre sayısı vs yeni metrikler (sabit dalga kovasında)")
z['cells_b'] = pd.cut(z.cells, [0, 40, 100, 200, 320, 500])
cols = ['e_moves', 'visible_mean', 'e_risky', 'e_crit', 'abc_mean', 'abc_distinct_path', 'pp_locked_mean', 'filler_ratio', 'dh_exp_mean', 'blind_progress_mean', 'cov_tol']
g = z.groupby(['bin', 'cells_b'], observed=True)[cols].mean().round(2); g['n'] = z.groupby(['bin', 'cells_b'], observed=True).size(); print(g.to_string()); save(g, 'phase2_size_proxy')
cat2 = z[(z.src == 'cat') & (z.scale == 2)]
print("\nkedi ×2 (216 hücre; 244'lük prototipe en yakın elimizdeki proxy), n=%d:" % len(cat2))
print(cat2[cols].describe().loc[['mean', '50%']].round(2).to_string())
print("kedi ×1 (54 hücre):"); c1 = z[(z.src == 'cat') & (z.scale == 1)]; print(c1[cols].describe().loc[['mean', '50%']].round(2).to_string())
pair = z[z.real].pivot_table(index=['src', 'cm', 'layout', 'bin'], columns='scale', values=['e_risky', 'abc_mean', 'abc_distinct_path', 'filler_ratio'], aggfunc='mean').dropna()
for c in ['e_risky', 'abc_mean', 'abc_distinct_path', 'filler_ratio']:
    print(f"  eşleşmiş x1→x2 {c}: {pair[(c, 1)].mean():.2f} → {pair[(c, 2)].mean():.2f}  (n={len(pair)})")
z.to_csv(f'{SUM}/size_v2_with_envelope.csv', index=False)
S.to_csv(f'{SUM}/broad_v2_with_envelope.csv', index=False)
