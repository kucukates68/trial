import pandas as pd, numpy as np
from analysis_common import *
import statsmodels.api as sm
import statsmodels.formula.api as smf
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
dep=pd.read_csv(f'{RES}/dep_descriptors.csv')
def merged(name,solvable=True):
    d=load(name,solvable=solvable)
    for c in ('scale','syn_n'):
        if c not in d:d[c]=0 if c=='syn_n' else 1
    return d.merge(dep,on=['src','cm','k','layout','scale','syn_n'],how='left')
b=merged('broad',False)
print("broad satır",len(b),"dep_unreach:",b.dep_unreach.mean().round(3))
print("\nÇözülemez (W sonrası) ile bağımlılık döngüsü:")
b['solv']=b['solv'].astype(bool)
print(pd.crosstab(b.dep_cycle,b.solv,normalize='index').round(3))
print("unreach (kapı hücreleri ulaşılmaz) ile solv:",pd.crosstab(b.dep_unreach,b.solv).to_string())
s=b[b.solv & (b.dep_unreach==False)].copy()
s['cyc']=s.dep_cycle.astype(int)
print("\nÇözülebilirlerde: bağımlılık döngüsü payı",s.cyc.mean().round(3))
cols=['dens_risky','dens_meaningful','e_risky','greedy_fail','risk','regret_max','win_undo2']
print(s.groupby('dep_cycle')[cols].mean().round(3).to_string())
print("\nÇözülebilir + döngü var: W dağılımı (bin)");print(s[s.cyc==1].groupby('bin').size().to_dict())
print("\nKorelasyonlar (dens_risky ile):")
preds=['dep_edges','dep_density','dep_bidir','dep_shadow_frac','dep_cross_per_cell','dep_same_per_cell','dep_maxdom','cm_clustering','cm_comp_total','ent_trans_per_cell','cm_dominant','cm_entropy_norm','deep_entropy']
s['comp_per_cell']=s.cm_comp_total/s.cells
preds[preds.index('cm_comp_total')]='comp_per_cell'
print(s[preds+['dens_risky','greedy_fail']].corr()[['dens_risky','greedy_fail']].round(2).to_string())
# nested model comparison
fam=pd.get_dummies(s.family,drop_first=True).astype(float)
def r2(cols,y='dens_risky',extra=None):
    X=sm.add_constant(pd.concat([s[cols],fam] if extra is None else [s[cols],fam,extra],axis=1))
    return sm.OLS(s[y],X).fit().rsquared
cm_cols=['cm_clustering','comp_per_cell','cm_dominant','cm_entropy_norm']
tr_cols=['ent_trans_per_cell','ent_wtrans_per_cell','ent_mean_run','deep_entropy']
dp_cols=['dep_density','dep_bidir','dep_shadow_frac','dep_cross_per_cell','dep_same_per_cell','dep_maxdom']
base=r2([])
for y in ['dens_risky','dens_meaningful','e_risky','greedy_fail','risk']:
    row={k:r2(v,y) for k,v in {'erişim ailesi':[], '+renk istatistiği (kümelenme, parça, baskın, entropi)':cm_cols,'+derinlik-geçiş':cm_cols+tr_cols,'yalnız bağımlılık (dominator)':dp_cols,'bağımlılık + renk istatistiği':dp_cols+cm_cols,'hepsi':dp_cols+cm_cols+tr_cols}.items()}
    print(f"\n{y}: "+' | '.join(f"{k}: {v:.3f}" for k,v in row.items()))
# what survives after dependency? drop-one from 'hepsi'
y='dens_risky';allc=dp_cols+cm_cols+tr_cols
Z=(s[allc]-s[allc].mean())/s[allc].std().replace(0,1)
Xf=sm.add_constant(pd.concat([Z,fam],axis=1));yf=(s[y]-s[y].mean())/s[y].std()
full=sm.OLS(yf,Xf).fit();rows=[]
for c in allc:
    m2=sm.OLS(yf,Xf.drop(columns=[c])).fit();rows.append((c,full.params[c],full.rsquared-m2.rsquared))
D=pd.DataFrame(rows,columns=['var','std_beta','drop1_dR2']).sort_values('drop1_dR2',ascending=False)
print("\nTüm tanımlayıcılarla tek-tek çıkarma (dens_risky), R2=%.3f"%full.rsquared);print(D.round(3).to_string(index=False))
D.to_csv(f'{SUM}/drop_one_with_dependency.csv',index=False)
# dependency descriptors on region ablation (fragmentation fixed, order varies)
r=merged('region');r['R']=r.src.str.split(':').str[2].astype(int)
r['grp']=r.src.str.split(':').str[1]+'_'+r.R.astype(str)+'_'+r.layout+'_'+r.bin
for c in ['dep_shadow_frac','dep_cross_per_cell','dep_density','ent_trans_per_cell']:
    r[c+'_c']=r[c]-r.groupby('grp')[c].transform('mean')
r['dens_c']=r['dens_risky']-r.groupby('grp')['dens_risky'].transform('mean')
rr=r[r.groupby('grp')['dens_risky'].transform('size')>=4]
print("\nBölge ablasyonu, GRUP İÇİ (R sabit) korelasyon ~ dens_risky:")
for c in ['dep_shadow_frac','dep_cross_per_cell','dep_density','dep_bidir','ent_trans_per_cell']:
    cc=rr[c]-rr.groupby('grp')[c].transform('mean')
    print(f"  {c:20} r={np.corrcoef(cc.fillna(0),rr['dens_c'])[0,1]:.3f}")
# synthetic: patterns vs dependency
sy=merged('synth');sy=sy[(sy.waves_nominal>=7)&(sy.waves_nominal<=16)]
g=sy.groupby(sy.src.str[4:])[['dep_shadow_frac','dep_cross_per_cell','dep_density','dep_bidir','dep_cycle','dens_risky']].mean().round(3).sort_values('dens_risky')
print("\nSentetik: desen -> bağımlılık tanımlayıcıları ve dens_risky");print(g.to_string());save(g,'synth_dependency_by_pattern')
print("rings vs rings_alt bağımlılık kıyas:",g.loc[['rings','rings_alt'],['dep_shadow_frac','dep_cross_per_cell','dens_risky']].to_dict('index'))
