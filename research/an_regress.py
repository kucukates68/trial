import pandas as pd, numpy as np
from analysis_common import *
import statsmodels.api as sm
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
b=load('broad')
b['comp_per_cell']=b['cm_comp_total']/b['cells']
b['log_cells']=np.log(b['cells'])
color_comp=['cm_dominant','cm_entropy_norm']
color_clus=['cm_clustering','comp_per_cell']
depth_tr=['ent_trans_per_cell','ent_wtrans_per_cell','ent_mean_run','deep_entropy']
geo=['ent_maxdepth','ent_meandepth','log_cells','waves_nominal']
fam=pd.get_dummies(b['family'],drop_first=True).astype(float)
X_all=pd.concat([b[color_comp+color_clus+depth_tr+geo],fam],axis=1)
print("Korelasyon (yapısal tanımlayıcılar):")
print(b[color_comp+color_clus+depth_tr+['ent_maxdepth']].corr().round(2).to_string())
def fit(cols,y):
    X=sm.add_constant(pd.concat([X_all[[c for c in cols if c in X_all]]],axis=1))
    return sm.OLS(y,X).fit()
sets=[('geometri: erişim ailesi + derinlik + boyut',list(fam.columns)+geo),
      ('+ renk dağılımı (baskın, entropi)',list(fam.columns)+geo+color_comp),
      ('+ uzamsal kümelenme',list(fam.columns)+geo+color_comp+color_clus),
      ('+ derinlik-geçiş (giriş sırası)',list(fam.columns)+geo+color_comp+color_clus+depth_tr)]
out=[]
for y in ['dens_risky','dens_meaningful','e_risky','risk']:
    prev=0
    print(f"\n== {y}  (hiyerarşik R², n={len(b)})")
    for name,cols in sets:
        m=fit(cols,b[y]);print(f"  {name:48} R²={m.rsquared:.3f}  ΔR²={m.rsquared-prev:+.3f}");out.append((y,name,m.rsquared,m.rsquared-prev));prev=m.rsquared
    # reversed order: depth-transition first
    m1=fit(list(fam.columns)+geo+depth_tr,b[y]);m0=fit(list(fam.columns)+geo,b[y])
    print(f"  (sadece derinlik-geçiş eklenirse, renk dağılımı/kümelenme olmadan) R²={m1.rsquared:.3f} ΔR²={m1.rsquared-m0.rsquared:+.3f}")
    mc=fit(list(fam.columns)+geo+color_comp+color_clus,b[y])
    print(f"  (sadece renk dağılımı+kümelenme eklenirse, derinlik-geçiş olmadan) R²={mc.rsquared:.3f} ΔR²={mc.rsquared-m0.rsquared:+.3f}")
pd.DataFrame(out,columns=['resp','model','R2','dR2']).to_csv(f'{SUM}/hier_regression.csv',index=False)
# drop-one partial R² in full model + standardized betas
y='dens_risky';cols=list(fam.columns)+geo+color_comp+color_clus+depth_tr
Z=(X_all[cols]-X_all[cols].mean())/X_all[cols].std().replace(0,1)
full=sm.OLS((b[y]-b[y].mean())/b[y].std(),sm.add_constant(Z)).fit()
rows=[]
for c in color_comp+color_clus+depth_tr+geo:
    cs=[x for x in cols if x!=c]
    Z2=Z[cs];m2=sm.OLS((b[y]-b[y].mean())/b[y].std(),sm.add_constant(Z2)).fit()
    rows.append((c,full.params[c],full.rsquared-m2.rsquared))
D=pd.DataFrame(rows,columns=['var','std_beta','drop1_dR2']).sort_values('drop1_dR2',ascending=False)
print("\nTam model (dens_risky): standart beta ve tek-tek çıkarma ΔR²");print(D.round(3).to_string(index=False))
D.to_csv(f'{SUM}/drop_one_dens_risky.csv',index=False)
# nonlinear check: random forest permutation importance
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
Xtr,Xte,ytr,yte=train_test_split(X_all[cols],b[y],test_size=0.3,random_state=1)
gb=GradientBoostingRegressor(n_estimators=300,max_depth=3,random_state=1).fit(Xtr,ytr)
print("\nGB test R²:",round(gb.score(Xte,yte),3))
pi=permutation_importance(gb,Xte,yte,n_repeats=10,random_state=1)
imp=pd.Series(pi.importances_mean,index=cols).sort_values(ascending=False)
print(imp.head(10).round(3).to_string())
imp.to_csv(f'{SUM}/gb_perm_importance_dens_risky.csv')
