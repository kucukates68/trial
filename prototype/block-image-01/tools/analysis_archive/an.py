import sys, json, collections, statistics
sys.path.insert(0,'/home/user/trial/prototype/block-image-01/tools')
from lvlkit import Canvas, Geo, analyse
def load(key):
    lv=json.load(open(key+'_up.json')); rows=lv['grid'].split('\n'); ER=len(rows)-1; EC=rows[ER].index('E')
    cv=Canvas(); cv.entrance=(EC,ER); cv.floor={(c,r) for r,row in enumerate(rows) for c,ch in enumerate(row) if ch=='.'}
    for p in lv['pieces']: cv.piece(p['id'],'x',[(c,r) for r,c in p['cells']])
    names=[p['id'] for p in lv['pieces']]; geo=Geo(cv,names); return lv,geo
def classify(A):
    memo=A['memo']; out={}
    for st,r in memo.items():
        mv=r['moves']; cards=len(mv)
        safe=sum(1 for m in mv if m[1]=='safe' and m[3]); now=sum(1 for m in mv if m[1]!='safe'); later=sum(1 for m in mv if m[1]=='safe' and not m[3])
        out[st]=(cards,safe,now,later)
    return out
def forward(A, policy):
    """policy: 'win' = kazandıran hamleler arasından düzgün; 'rand' = tüm kartlar arasından düzgün (ölenler düşer)"""
    memo=A['memo']; N=sum(len(q) for q in A['ids']); layer={A['start']:1.0}; prof=[]
    for k in range(N):
        agg=collections.Counter(); alive=sum(layer.values()); nxt=collections.defaultdict(float); hz_wrong=0.0
        for st,w in layer.items():
            r=memo[st]; mv=r['moves']
            cards=len(mv); safe=[m for m in mv if m[1]=='safe' and m[3]]; now=[m for m in mv if m[1]!='safe']; later=[m for m in mv if m[1]=='safe' and not m[3]]
            agg[(cards,len(safe))]+=w
            agg['cards']+=w*cards; agg['safe']+=w*len(safe); agg['now']+=w*len(now); agg['later']+=w*len(later)
            if policy=='win':
                for m in safe: nxt[m[2]]+=w/len(safe)
            else:
                hz_wrong+=w*(len(now)+len(later))/cards
                for m in mv:
                    if m[1]=='safe': nxt[m[2]]+=w/cards   # kısa görüşlü olmayan: kötü hamle (doom) sonra ölür; burada ölü durumlar yaşamaya devam eder, win=False olarak izlenir
        prof.append((alive,agg,hz_wrong)); layer=dict(nxt)
        if not layer: break
    return prof
