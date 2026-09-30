"""Builds the 30-level human-test shortlist (3 groups x 10: 6 small + 4 large each).

Group A  instant mistake   (DH ~ 1)          - the natural behaviour of the current mechanic
Group B  delayed mistake   (DH_exp >= 2)     - rare region; each B level is MATCHED to an A level of the same colour-map
                                               family with similar decision density / waves / size / bottlenecks, so the
                                               A-vs-B contrast is mostly about mistake timing (colour-structure confounds are
                                               reduced, not removed - reported below)
Group W  two warm-up levels (teach the rule; excluded from analysis)
Group C  benchmark-near profile              - puzzle-yield levels closest to the filtered envelope on every dimension
                                               EXCEPT deadlock horizon (which is what A/B vary)
Nothing here is a design target; the envelope is only used to pick comparison levels.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_common import SUM, HERE
from run_experiments import make_labels
from puzzle_access import build_grid
from human_test_oracle import Oracle

OUT = os.path.join(HERE, 'human_test')
os.makedirs(OUT, exist_ok=True)

S = pd.read_csv(f'{SUM}/broad_v2_with_envelope.csv'); S['pool'] = 'small'
Z = pd.read_csv(f'{SUM}/size_v2_with_envelope.csv')
Z = Z[(~Z.src.str.startswith('syn:')) & (Z.scale == 2)].copy(); Z['pool'] = 'large'
P = pd.concat([S, Z], ignore_index=True)
P = P[(P.solv == True) & (P.greedy_fail == 1) & (P.dens_risky >= 0.25)].copy()      # puzzle-yield candidates only
P['uid'] = P.src + '|' + P.cm + '|' + P.layout + '|' + P.W.astype(str) + '|' + P.scale.astype(str) + '|' + P.bin
P['comp_per_cell'] = P.cm_comp_total / P.cells

# envelope coverage WITHOUT the horizon dimensions (A/B vary those on purpose)
NODH = [('in_tol_action_space', 1.0), ('in_tol_critical_decisions', 1.0), ('in_tol_total_moves', 0.5), ('in_tol_filler_ratio', 0.5), ('in_tol_trap_timing', 0.5)]
NODHc = [(c.replace('in_tol', 'in_core'), w) for c, w in NODH]
def cov(df, dims):
    num = sum(df[c].fillna(0) * w for c, w in dims); den = sum(df[c].notna() * w for c, w in dims)
    return num / den
P['cov_noDH_tol'] = cov(P, NODH); P['cov_noDH_core'] = cov(P, NODHc)

NS, NL = 6, 4
def diverse_pick(df, n, used, key, max_cm=3, max_src=2, max_fam=3):
    out = []
    for _, r in df.sort_values(key, ascending=False).iterrows():
        if r.uid in used or (r.src, r.cm, r.layout) in {(o.src, o.cm, o.layout) for o in out}:
            continue
        if sum(o.cm == r.cm for o in out) >= max_cm or sum(o.src == r.src for o in out) >= max_src or sum(o.family == r.family for o in out) >= max_fam:
            continue
        out.append(r)
        if len(out) == n:
            break
    return out

used = set()
# ---------------- group B (delayed), then matched A
Bc = P[P.dh_exp_mean >= 2.0]
B = []
for pool, n in (('small', NS), ('large', NL)):
    B += diverse_pick(Bc[Bc.pool == pool], n, used, 'dh_exp_mean', max_cm=3, max_src=2, max_fam=3)
used |= {b.uid for b in B}
FEAT = ['e_risky', 'waves_nominal', 'cells', 'abc_mean', 'cm_clustering']
Ac = P[(P.dh_instant_share >= 0.9)]
A = []
for b in B:
    pool_df = Ac[(Ac.pool == b.pool) & (Ac.cm == b.cm) & (~Ac.uid.isin(used))]
    if len(pool_df) == 0:                                                   # relax the colour-map family if needed
        pool_df = Ac[(Ac.pool == b.pool) & (~Ac.uid.isin(used))]
    sd = Ac[FEAT].std().replace(0, 1)
    d = (((pool_df[FEAT] - b[FEAT].astype(float)) / sd) ** 2).sum(axis=1)
    pick = pool_df.loc[d.idxmin()]
    A.append(pick); used.add(pick.uid)
# ---------------- group C (near envelope on the non-horizon dimensions)
Cc = P[(P.dh_exp_mean < 2.0)].copy()
Cc['score'] = Cc.cov_noDH_tol + 0.25 * Cc.cov_noDH_core
C = []
for pool, n in (('small', NS), ('large', NL)):
    C += diverse_pick(Cc[Cc.pool == pool], n, used, 'score', max_cm=3, max_src=2, max_fam=3)
used |= {c.uid for c in C}

def card(r, group, idx, pair=None):
    lab = make_labels(r.src, r.cm, int(r.k), int(r.scale), int(r.syn_n) if 'syn_n' in r and not pd.isna(r.syn_n) else 0)
    grid = build_grid(lab, r.layout)
    o = Oracle(grid, int(r.W))
    # one example winning colour sequence (for facilitators / prototype sanity check)
    s = 0; seq = []
    import random
    rng = random.Random(1)
    while s != o.L.full:
        safe = [(o.L.letters[k], t) for k, t in o.L.info(s)[1] if o.nwin(t) > 0]
        c, s = rng.choice(safe); seq.append(c)
    lid = f"{group}{idx:02d}{'L' if r.pool == 'large' else 'S'}"
    return dict(id=lid, group=group, pair=pair, pool=r.pool, src=r.src, cm=r.cm, layout=r.layout, family=r.family, W=int(r.W), colors=o.L.letters,
                cells=int(r.cells), waves=int(r.waves_nominal), grid=grid, safe_first_colors=o.safe_colors(0), legal_first_colors=o.legal_colors(0),
                example_winning_sequence=seq,
                metrics={k: (None if pd.isna(r[k]) else round(float(r[k]), 3)) for k in
                         ['dh_exp_mean', 'dh_min_mean', 'dh_instant_share', 'latent_doom_mass', 'blind_progress_mean', 'e_moves', 'e_risky', 'e_crit', 'e_forced', 'dens_risky',
                          'filler_ratio', 'visible_mean', 'mbf_mean', 'cpr_risky', 'abc_mean', 'abc_max_dag', 'trap_timing', 'rnd0', 'win_undo0', 'win_undo1', 'win_undo2',
                          'rec1', 'regret_max', 'cm_clustering', 'comp_per_cell', 'cov_noDH_tol', 'cov_noDH_core', 'cov_tol']})

levels = []
for i, (a, b) in enumerate(zip(A, B), 1):
    levels.append(card(b, 'B', i, pair=i)); levels.append(card(a, 'A', i, pair=i))
for i, c in enumerate(C, 1):
    levels.append(card(c, 'C', i))
# ---------------- warm-ups (teach the rule; NOT analysed): a no-decision level and a mild one that greedy solves
Wm = S[(S.solv == True)].copy()
Wm['cov_noDH_tol'] = cov(Wm, NODH); Wm['cov_noDH_core'] = cov(Wm, NODHc); Wm['comp_per_cell'] = Wm.cm_comp_total / Wm.cells
w1 = Wm[(Wm.family == 'OPEN') & (Wm.cm.isin(['CM1', 'CM2'])) & (Wm.dens_risky < 0.02) & (Wm.cells <= 60)].sort_values('cells').iloc[0]
w2 = Wm[(Wm.greedy_fail == 0) & (Wm.dens_risky.between(0.10, 0.25)) & (Wm.cells <= 75)].sort_values('dens_risky').iloc[0]
for i, w in enumerate([w1, w2], 1):
    levels.append(card(w, 'W', i))
levels.sort(key=lambda l: (l['group'], l['id']))
json.dump(dict(meta=dict(note="İnsan testi karşılaştırma seti; hedef değil. Gruplar: A anında hata, B gecikmeli hata (eşleştirilmiş), C zarfa yakın (DH hariç). Izgara: E giriş, # duvar, . zemin, harfler renkli hedef.",
                         grid_legend={'E': 'giriş', '#': 'duvar', '.': 'zemin (kalıcı açık)'}, rules="sabit W, en derinden başla, dolu hücre kalıcı engel, erişilemez hedef = kayıp"),
               levels=levels), open(f'{OUT}/levels.json', 'w'), ensure_ascii=False, indent=1)

df = pd.DataFrame([{**{k: l[k] for k in ['id', 'group', 'pair', 'pool', 'src', 'cm', 'layout', 'family', 'W', 'cells', 'waves']}, **l['metrics']} for l in levels])
df.to_csv(f'{OUT}/shortlist.csv', index=False)

# ---------------- level cards
md = ["# İnsan testi seviye kartları\n", "Izgara: `E` giriş, `#` duvar, `.` zemin, `A/B/C` renkli hedef hücreler. Metrikler çözücüden (hedef değil).\n"]
for l in levels:
    m = l['metrics']
    md.append(f"\n## {l['id']}  (grup {l['group']}{', eş ' + str(l['pair']) if l['pair'] else ''}) — {l['src']} / {l['cm']} / {l['layout']} — {l['cells']} hücre, W={l['W']}, {l['waves']} dalga\n")
    md.append("```\n" + l['grid'] + "\n```\n")
    md.append(f"- ilk hamlede güvenli renkler: {l['safe_first_colors']} (yasal: {l['legal_first_colors']}) | örnek kazanan dizi: {''.join(l['example_winning_sequence'])}\n"
              f"- DH beklenen {m['dh_exp_mean']}, anlık hata payı {m['dh_instant_share']}, gecikmeli-hata/oyun {m['latent_doom_mass']}, kör ilerleme {m['blind_progress_mean']}\n"
              f"- riskli karar/oyun {m['e_risky']} (tek-doğru {m['e_crit']}), filler {m['filler_ratio']}, ABC {m['abc_mean']}, rastgele kazanma undo0/1/2 {m['win_undo0']}/{m['win_undo1']}/{m['win_undo2']}\n")
open(f'{OUT}/level_cards.md', 'w').write(''.join(md))

# ---------------- balance report
print("== GRUP ÖZETİ (ortalama)")
cols = ['cells', 'waves', 'dh_exp_mean', 'dh_instant_share', 'latent_doom_mass', 'e_risky', 'e_crit', 'dens_risky', 'filler_ratio', 'abc_mean', 'cm_clustering', 'comp_per_cell', 'cov_noDH_tol', 'cov_tol', 'win_undo0', 'rec1']
print(df.groupby('group')[cols].mean().round(2).to_string())
print("\n== A–B EŞLEŞME KALİTESİ (çift başına |B−A|, ortalama)")
pv = df[df.group.isin(['A', 'B'])].pivot(index='pair', columns='group', values=['e_risky', 'waves', 'cells', 'abc_mean', 'cm_clustering', 'comp_per_cell', 'dens_risky', 'dh_exp_mean'])
for c in ['e_risky', 'waves', 'cells', 'abc_mean', 'cm_clustering', 'comp_per_cell', 'dens_risky', 'dh_exp_mean']:
    print(f"  {c:16} A={pv[(c,'A')].mean():.2f}  B={pv[(c,'B')].mean():.2f}  ort|Δ|={(pv[(c,'A')]-pv[(c,'B')]).abs().mean():.2f}")
print("  aynı CM'de eşleşen çift:", int(sum(a.cm == b.cm for a, b in zip(A, B))), "/", len(A))
print("\n== ÇEŞİTLİLİK")
for g in 'ABC':
    d = df[df.group == g]; print(g, 'cm', d.cm.value_counts().to_dict(), '| aile', d.family.value_counts().to_dict(), '| silüet', d.src.value_counts().to_dict())
print("\nyazıldı:", OUT, "->", sorted(os.listdir(OUT)))
