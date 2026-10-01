import re, json, glob, os, hashlib
U='/root/.claude/uploads/309a846e-36ea-5c76-a60b-b8e84c53c4f6/'
R='/home/user/trial/prototype/block-image-01/src/'
out={}
for f in sorted(glob.glob(U+'*block-image-L0*.html')):
    t=open(f,encoding='utf-8').read(); m=re.search(r'window\.BI_LEVEL\s*=\s*(\{.*?\});\s*\n',t,re.S)
    lv=json.loads(m.group(1)); name=os.path.basename(f).split('-',1)[1]
    key=lv['id'].lower(); out[key]=lv; json.dump(lv,open(key+'_up.json','w'))
    rp=R+'level_%s.js'%key; rt=open(rp,encoding='utf-8').read(); rv=json.loads(rt[rt.index('=')+1:].rstrip().rstrip(';'))
    same_grid=lv['grid']==rv['grid']; same_hand=lv['hand']==rv['hand']; same_pieces=[ (p['id'],p['cells']) for p in lv['pieces']]==[(p['id'],p['cells']) for p in rv['pieces']]
    print(name,lv['id'],'parça',len(lv['pieces']),'hücre',lv['cells'],'| repo ile: grid',same_grid,'kuyruk',same_hand,'parçalar',same_pieces,'| kuyruk uzunlukları',[len(q) for q in lv['hand']])
