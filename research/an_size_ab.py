import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
from scipy import stats
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
w=load('wsweep',solvable=False);print("W=1 çözülebilirlik (atlananlar hariç):",w[(w.W==1)&(w.get('skipped',False)!=True)].solv.mean().round(3))
# ------------------------------------------------------------- IMAGE SIZE
z=load('size',solvable=False)
print("\n=== GÖRÜNTÜ BOYUTU ===  satır",len(z),"çözülebilir",round(z.solv.mean(),3))
z['kind']=np.where(z.src.str.startswith('syn:'),'sentetik n=4 tabanı','silüet x1/x2')
s=z[z.solv].copy()
s['cellsb']=pd.cut(s.cells,[0,30,80,160,320,700])
cols=['waves_nominal','W','e_moves','e_meaningful','e_risky','e_crit','e_free','e_forced','dens_meaningful','dens_risky','greedy_fail','regret_max','win_undo2']
print("\n-- Sentetik (aynı renk topolojisi, tam sayı büyütme), sabit dalga kovası:")
syn=s[s.kind.str.startswith('sentetik')]
for b in ['w07_10','w11_15']:
    g=syn[syn.bin==b].groupby('cells')[cols].mean().round(2);g['n']=syn[syn.bin==b].groupby('cells').size();print(f"  {b}");print(g.to_string())
print("\n-- Silüet x1 vs x2 (aynı renk yapısı), sabit dalga kovası:")
sil=s[s.kind.str.startswith('silüet')]
for b in ['w07_10','w11_15']:
    g=sil[sil.bin==b].groupby('scale')[cols+['cells']].mean().round(2);g['n']=sil[sil.bin==b].groupby('scale').size();print(f"  {b}");print(g.to_string())
# paired x1 vs x2 on identical (src,cm,layout,bin)
key=['src','cm','layout','bin']
p1=sil[sil.scale==1].set_index(key);p2=sil[sil.scale==2].set_index(key)
j=p1.join(p2,lsuffix='_1',rsuffix='_2',how='inner')
print("\nEşleşmiş x1→x2 (n=%d): hücre ×%.1f"%(len(j),(j.cells_2/j.cells_1).mean()))
for c in ['e_meaningful','e_risky','e_crit','e_free','e_forced','dens_meaningful','dens_risky','greedy_fail','regret_max','win_undo2','risk']:
    dlt=j[c+'_2']-j[c+'_1'];t=stats.wilcoxon(dlt) if (dlt!=0).any() else None
    print(f"  {c:16} x1={j[c+'_1'].mean():.3f}  x2={j[c+'_2'].mean():.3f}  fark={dlt.mean():+.3f}  (p={t.pvalue:.3g})" if t else f"  {c}: fark yok")
# fixed W (not fixed waves): compare same W between scales via synthetic? (W differs by construction) -> show W
print("\nNot: sabit-dalga tasarımında W ölçekle birlikte büyür (x2'de W≈2x).")
# Fixed-W view in wsweep? cells vs decisions at same W across silhouettes
ws=load('wsweep');ws=ws[ws.W.isin([4,8])]
print("\nSabit W (wsweep, W=4 ve 8): hücre sayısı sınıfına göre ortalama karar sayıları")
ws['cb']=pd.cut(ws.cells,[0,60,75,100,200])
print(ws.groupby(['W','cb'],observed=True)[['cells','waves_nominal','e_moves','e_meaningful','e_risky','e_free','dens_risky']].mean().round(2).to_string())
# regress e_risky on cells and waves in broad
b=load('broad')
import statsmodels.formula.api as smf
m=smf.ols('e_risky ~ np.log(cells)+np.log(waves_nominal)+C(cm)+C(family)',data=b).fit()
print("\nbroad: log e_risky ~ log cells + log waves + CM + family:");
m=smf.ols('np.log(e_risky+0.05) ~ np.log(cells)+np.log(waves_nominal)+C(cm)+C(family)',data=b).fit()
print("  esneklik(hücre)=%.2f  esneklik(dalga)=%.2f  R2=%.2f"%(m.params['np.log(cells)'],m.params['np.log(waves_nominal)'],m.rsquared))
# ------------------------------------------------------------- 3 vs 4 COLOURS
a3=load('ab4',solvable=False);a3=a3[a3.exp=='ab3'];a4=load('ab4',solvable=False);a4=a4[a4.exp=='ab4']
print("\n=== 3 vs 4 RENK ===")
print("çözülebilirlik: k=3 %.3f | k=4 %.3f"%(a3.solv.mean(),a4.solv.mean()))
key=['src','cm','layout','bin']
j=a3[a3.solv].set_index(key).join(a4[a4.solv].set_index(key),lsuffix='_3',rsuffix='_4',how='inner')
print("eşleşmiş çift (ikisi de çözülebilir):",len(j))
rows=[]
for c in ['waves_nominal','e_moves','e_meaningful','e_risky','e_crit','e_trap','e_meansafe','e_free','e_forced','dens_meaningful','dens_risky','forced_free_ratio','risk','greedy_fail','regret_max','rec2','win_undo0','win_undo2','log_seq_canon_per_move','ent_trans_per_cell','cm_entropy_norm','cm_clustering']:
    if c+'_3' not in j:continue
    dl=j[c+'_4']-j[c+'_3'];r=dict(metrik=c,k3=j[c+'_3'].mean(),k4=j[c+'_4'].mean(),fark=dl.mean(),ci_lo=np.nan,ci_hi=np.nan,d=dl.mean()/dl.std() if dl.std()>0 else np.nan)
    bs=[dl.sample(len(dl),replace=True,random_state=i).mean() for i in range(300)];r['ci_lo'],r['ci_hi']=np.percentile(bs,[2.5,97.5])
    rows.append(r)
T=pd.DataFrame(rows).round(3);print(T.to_string(index=False));save(T,'ab_3v4_paired')
# by CM and family: change in e_risky, dens_risky
for fac in ['cm','family']:
    dd=j.reset_index().assign(de=lambda x:x.e_risky_4-x.e_risky_3,dd=lambda x:x.dens_risky_4-x.dens_risky_3,dm=lambda x:x.e_meaningful_4-x.e_meaningful_3)
    if 'family' not in dd and 'family_3' in dd:dd['family']=dd['family_3']
    print(f"\n{fac} bazında 4-3 farkı (ort):");print(dd.groupby(fac)[['de','dd','dm']].mean().round(2).to_string())
# is e_risky gain explained by waves? compare at equal waves bin only (already) -> also decisions per wave
j['de_per_wave']=(j.e_risky_4/j.e_moves_4)-(j.e_risky_3/j.e_moves_3)
print("\nhamle başına riskli karar farkı (k4-k3): %.3f"%j.de_per_wave.mean())
