import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from analysis_common import *
pd.set_option('display.width',250);pd.set_option('display.max_columns',40)
d=load('wsweep',solvable=False)
print("satır",len(d),"atlanan(state cap):",d.get('skipped',pd.Series(dtype=float)).fillna(False).sum() if 'skipped' in d else 0)
d['series']=d.src+'|'+d.cm+'|'+d.layout
ok=d[d.solv.fillna(False)]
print("\nW -> çözülebilirlik, greedy başarısızlığı, karar yoğunluğu (ortalama):")
g=d.groupby('W').agg(n=('solv','size'),solv=('solv','mean'))
h=ok.groupby('W').agg(waves=('waves_nominal','mean'),greedy_fail=('greedy_fail','mean'),dens_risky=('dens_risky','mean'),dens_meaningful=('dens_meaningful','mean'),e_risky=('e_risky','mean'),e_meaningful=('e_meaningful','mean'),risk=('risk','mean'),regret_max=('regret_max','mean'),win_undo2=('win_undo2','mean'))
T=g.join(h).round(3);print(T.to_string());save(T,'wsweep_by_W')
# W=1 check
w1=ok[ok.W==1];print("\nW=1: greedy_deep başarı oranı",w1.greedy_deep.mean().round(3),"n",len(w1))
# same waves bucket view
ok['wbin']=pd.cut(ok.waves_nominal,[0,6,10,15,20,30,60,300])
print("\nDalga sayısı kovası -> yoğunluk (W'den bağımsız kıyas)");print(ok.groupby('wbin',observed=True)[['dens_risky','dens_meaningful','e_risky','e_meaningful','greedy_fail','risk']].mean().round(3).assign(n=ok.groupby('wbin',observed=True).size()).to_string())
# monotonicity within series
rows=[]
for s,x in ok.groupby('series'):
    x=x.sort_values('W')
    if len(x)<5:continue
    y=x.dens_risky.values;ww=x.W.values
    dy=np.sign(np.diff(y));dy=dy[dy!=0]
    changes=int((np.diff(dy)!=0).sum()) if len(dy)>1 else 0
    from scipy.stats import spearmanr
    rho=spearmanr(ww,y).correlation if np.std(y)>0 else np.nan
    rows.append(dict(series=s,n=len(x),rho=rho,dir_changes=changes,argmaxW=int(ww[np.argmax(y)]),maxd=y.max(),mind=y.min(),range=y.max()-y.min()))
M=pd.DataFrame(rows)
print("\nSeri (src|cm|layout) içinde W ile dens_risky:")
print("seri sayısı",len(M),"| Spearman(W, dens_risky) medyan",M.rho.median().round(2),"| tamamen monoton artan (rho>0.95)",(M.rho>0.95).mean().round(3),"| yön değiştiren (≥1)",(M.dir_changes>=1).mean().round(3),"| ≥2 yön değişimi",(M.dir_changes>=2).mean().round(3))
print("ortalama aralık (max-min)",M.range.mean().round(3),"; zirve W dağılımı:",M.argmaxW.value_counts().sort_index().to_dict())
M.to_csv(f'{SUM}/wsweep_monotonicity.csv',index=False)
# cliffs: solvable at W but unsolvable at W+1 step and back
cl=0;tot=0;ret=0
for s,x in d.groupby('series'):
    x=x.sort_values('W');sv=x.solv.fillna(False).values
    for a,b2 in zip(sv,sv[1:]):
        tot+=1
        if a and not b2:cl+=1
        if (not a) and b2:ret+=1
print("\nÇözülebilirlik W ile değişiyor: çözülebilir→çözümsüz geçiş",cl,"| çözümsüz→çözülebilir geçiş",ret,"(toplam ardışık W çifti",tot,")")
# solvability by cm and W (high W fails?)
print("\nÇözülebilir oranı: CM x W");print(d.pivot_table(index='cm',columns='W',values='solv',aggfunc='mean').round(2).to_string())
# effect sizes of W vs others in wsweep (ANOVA)
u=ok.copy();u['Wc']=u.W.astype(str)
for r in ['dens_risky','e_risky','greedy_fail']:
    t,r2=anova_eta(u,r,['src','cm','layout','Wc']);print(f"\nη² wsweep {r} (R²={r2:.2f})");print(t['eta2'].round(3).to_string())
# W x CM interaction: per CM curve dens_risky vs W
print("\nCM x W : dens_risky");print(ok.pivot_table(index='cm',columns='W',values='dens_risky',aggfunc='mean').round(2).to_string())
print("\nLayout ailesi x W : dens_risky");print(ok.pivot_table(index='family',columns='W',values='dens_risky',aggfunc='mean').round(2).to_string())
