import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..'))
from ref import Level
ROOT = os.path.join(H, '..', '..')
def load(cid):
    t = open(os.path.join(ROOT, 'src', 'level_%s.js' % cid), encoding='utf-8').read(); lv = json.loads(t[t.index('=') + 1:].rstrip().rstrip(';'))
    return lv, Level(lv['grid'], [dict(id=p['id'], cells=p['cells']) for p in lv['pieces']], lv['hand'])
def explain(cid):
    lv, L = load(cid); memo, root = L.analyse(); P = lv['pieces']; nm = lambda c: P[c]['id']; own = {}
    for i, p in enumerate(P):
        for r, c in p['cells']: own[(r, c)] = i
    tcell = {i: t for i, t in enumerate(L.tg)}
    def sealed_names(res): return sorted({nm(own[tcell[t]]) for t in res['sealed']})
    surv_c = {}
    def surv(st):
        if st in surv_c: return surv_c[st]
        b = 0
        for m in memo[st][3]:
            if m[4] == 'cont': b = max(b, 1 + surv(m[5]))
        surv_c[st] = b; return b
    def death(st):                       # en kısa yoldan ilk mühür: (kaç hamle, kart, mühürlenen parçalar)
        from collections import deque
        q = deque([(st, 0)]); seen = {st}
        while q:
            s, d = q.popleft()
            for slot, c in enumerate(L.cards(s)):
                if c is None: continue
                r = L.place(s, slot)
                if r is None: continue
                if r['sealed']: return d + 1, nm(c), sealed_names(r)
                if not r['won'] and not r['stuck'] and r['state'] not in seen: seen.add(r['state']); q.append((r['state'], d + 1))
        return None
    s0 = L.new_state(); out = dict(id=cid, title=lv['title'], hand=lv['hand'], first=[], orders=root[2], pieces=len(P), cells=lv['cells'])
    for m in memo[s0][3]:
        slot = m[0]; c = L.cards(s0)[slot]; e = dict(slot=slot + 1, card=nm(c), size=len(P[c]['cells']))
        if m[4] != 'cont': e['kind'] = m[4]; out['first'].append(e); continue
        s1 = m[5]; heads = [(sl, nm(cc)) for sl, cc in enumerate(L.cards(s1)) if cc is not None]
        e['next_hand'] = []
        for sl, cc in enumerate(L.cards(s1)):
            if cc is None: continue
            r = L.place(s1, sl); e['next_hand'].append(dict(slot=sl + 1, card=nm(cc), seals=bool(r['sealed']), sealed=sealed_names(r) if r['sealed'] else []))
        e['closes'] = [x['slot'] for x in e['next_hand'] if x['seals'] and x['slot'] != slot + 1 and any(h for h in memo[s0][3] if h[0] == x['slot'] - 1 and h[4] == 'cont')]
        e['win'] = bool(m[1]); e['win_orders'] = m[3]
        if not m[1]: e['survive'] = surv(s1); e['death'] = death(s1)
        out['first'].append(e)
    return out
if __name__ == '__main__':
    for cid in sys.argv[1:]: print(json.dumps(explain(cid), ensure_ascii=False, indent=1))
