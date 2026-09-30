import pandas as pd, numpy as np
from analysis_common import *
import statsmodels.formula.api as smf
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
d=load('region',solvable=False)
print("satır",len(d),"çözülebilir",round(d.solv.mean(),3))
d['R']=d.src.str.split(':').str[2].astype(int);d['shape']=d.src.str.split(':').str[1]
print("çözülebilirlik R'ye göre:",d.groupby('R').solv.mean().round(2).to_dict())
s=d[d.solv].copy()
s['comp_total']=s['cm_comp_total']
print("\nR (bölge sayısı = parçalanmışlık) ile ent_trans_per_cell korelasyonu:",round(s[['R','ent_trans_per_cell']].corr().iloc[0,1],2))
print("R -> ortalama (çözülebilir):")
g=s.groupby('R')[['dens_risky','dens_meaningful','e_risky','e_crit','risk','ent_trans_per_cell','cm_trans_sp','greedy_fail','regret_max','win_undo2']].mean().round(3)
print(g.to_string());save(g,'region_by_R')
# within-R, depth-order effect: transitions tertile within (shape,R,layout,bin)
s['grp']=s['shape']+'_'+s['R'].astype(str)+'_'+s['layout']+'_'+s['bin']
s['trans_c']=s['ent_trans_per_cell']-s.groupby('grp')['ent_trans_per_cell'].transform('mean')
s['dens_c']=s['dens_risky']-s.groupby('grp')['dens_risky'].transform('mean')
grp_sizes=s.groupby('grp').size()
s2=s[s['grp'].map(grp_sizes)>=4]
print("\nAynı bölge sayısı/yerleşim içinde (renk SIRASI değişiyor, parçalanmışlık sabit): korelasyon trans_c ~ dens_risky_c =",round(s2[['trans_c','dens_c']].corr().iloc[0,1],3),"n=",len(s2))
for R in sorted(s.R.unique()):
    x=s2[s2.R==R]
    if len(x)>30:print(f"  R={R:2d} içi korelasyon (derinlik-geçiş ~ riskli yoğunluk):",round(x[['trans_c','dens_c']].corr().iloc[0,1],3),"n=",len(x))
# variance decomposition: R vs ordering
m_full=smf.ols('dens_risky ~ C(shape)+C(layout)+C(bin)+C(R)+ent_trans_per_cell+cm_entropy_norm',data=s).fit()
m_noR=smf.ols('dens_risky ~ C(shape)+C(layout)+C(bin)+ent_trans_per_cell+cm_entropy_norm',data=s).fit()
m_noT=smf.ols('dens_risky ~ C(shape)+C(layout)+C(bin)+C(R)+cm_entropy_norm',data=s).fit()
m_base=smf.ols('dens_risky ~ C(shape)+C(layout)+C(bin)',data=s).fit()
print(f"\nR² taban(şekil+erişim+bin)={m_base.rsquared:.3f} | +R ve +geçiş ={m_full.rsquared:.3f}")
print(f"  parçalanmışlık (R) yalnız katkı ΔR² = {m_full.rsquared-m_noR.rsquared:.3f}")
print(f"  derinlik-geçiş yalnız katkı ΔR² = {m_full.rsquared-m_noT.rsquared:.3f}")
print("  ent_trans katsayısı:",round(m_full.params['ent_trans_per_cell'],3),"(p=%.3g)"%m_full.pvalues['ent_trans_per_cell'])
# dose-response of depth transitions at fixed R bucket
s['trans_bin']=pd.qcut(s['ent_trans_per_cell'],5,duplicates='drop')
print("\nDoz-yanıt: derinlik-geçiş/hücre kantili -> dens_risky (tüm R):");print(s.groupby('trans_bin',observed=True).dens_risky.mean().round(3).to_string())
for R in (4,8,16):
    x=s[s.R==R]
    if len(x)>50:
        x=x.assign(tb=pd.qcut(x['ent_trans_per_cell'],4,duplicates='drop'))
        print(f"  R={R}:",x.groupby('tb',observed=True).dens_risky.mean().round(3).tolist())
# and dose-response of R at fixed transitions bucket
s['tb3']=pd.qcut(s['ent_trans_per_cell'],3,labels=['düşük','orta','yüksek'])
print("\nR x (derinlik-geçiş 3'lü) -> dens_risky");print(s.pivot_table(index='R',columns='tb3',values='dens_risky',aggfunc='mean',observed=True).round(3).to_string())
# decision taxonomy by R
cat=s.groupby('R')[['e_forced','e_free','e_meansafe','e_trap','e_crit','e_moves']].mean()
for c in ['e_forced','e_free','e_meansafe','e_trap','e_crit']:cat[c+'_share']=cat[c]/cat['e_moves']
print("\nKarar sınıfları payı (R'ye göre)");print(cat[[c for c in cat.columns if c.endswith('_share')]].round(3).to_string())
