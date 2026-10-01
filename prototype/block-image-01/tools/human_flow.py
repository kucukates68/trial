"""İnsan-deneyimi analizi (SALT OKUNUR; seviye verisini değiştirmez): python3 tools/human_flow.py [l01 l02 ...]
Oyuncunun görebileceği durumlar = anında kilitlemeyen hamlelerle ulaşılan tüm durumlar. Faz = yerleştirilen parça sayısına göre üçte bir.
Metrikler: legal kart sayısı, bloklu (erişimi kapanmış) kart sayısı, zorunlu/serbest/tuzaklı el, yumuşak bağımlılık, gecikme (hata → kayıp mesafesi)."""
import json, os, sys, re
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from ref import Level
def load(l):
    t = open(os.path.join(H, '..', 'src', 'level_%s.js' % l), encoding='utf-8').read(); lv = json.loads(t[t.index('=') + 1:].rstrip().rstrip(';'))
    return lv, Level(lv['grid'], [dict(id=p['id'], cells=p['cells']) for p in lv['pieces']], lv['hand'])
def run(l):
    lv, L = load(l); memo, root = L.analyse(); NP = len(lv['pieces']); sizes = {p['id']: len(p['cells']) for p in lv['pieces']}
    seen = {}; stack = [(L.new_state(), 0)]
    while stack:
        st, d = stack.pop()
        if st in seen: continue
        seen[st] = d
        for m in memo[st][3]:
            if m[4] == 'cont': stack.append((m[5], d + 1))
    ph = defaultdict(lambda: defaultdict(int)); lagmemo = {}
    def lag(st):                                   # kayıp durumdan terminal kayba (seal/stuck/çıkmaz) min-max hamle
        if st in lagmemo: return lagmemo[st]
        ms = memo[st][3]; lo, hi = 99, 0
        if not ms: res = (0, 0)
        else:
            for m in ms:
                if m[4] != 'cont': a = b = 1
                else: a, b = lag(m[5]); a += 1; b += 1
                lo = min(lo, a); hi = max(hi, b)
            res = (lo, hi)
        lagmemo[st] = res; return res
    delayed = []; inst_cells = []
    for st, d in seen.items():
        win, p, cnt, ms = memo[st]; f = 0 if d < NP / 3 else 1 if d < 2 * NP / 3 else 2; k = ph[f]
        if not win: k['doomed'] += 1; continue
        k['n'] += 1; cards = [c for c in L.cards(st) if c is not None]; legal = len(ms); k['legal'] += legal; k['blocked'] += len(cards) - legal
        w = [m for m in ms if m[1]]; bad = [m for m in ms if not m[1]]
        if legal == 1: k['forced'] += 1
        elif not bad:
            k['free'] += 1
            cn = [m[3] for m in w]
            if max(cn) >= 3 * max(1, min(cn)): k['soft'] += 1          # seçim kalan serbestliği ≥3× değiştiriyor
        else:
            k['trap'] += 1
            if any(m[4] != 'cont' for m in bad): k['trap_inst'] += 1
            if any(m[4] == 'cont' for m in bad): k['trap_delay'] += 1
        for m in bad:
            if m[4] == 'cont': delayed.append((d, L.pieces[L.cards(st)[m[0]]]['id'] if False else lv['pieces'][L.cards(st)[m[0]]]['id'], lag(m[5])))
    out = dict(level=l, NP=NP, states=len(seen), phase={})
    for f in range(3):
        k = ph[f]; n = max(1, k['n']); out['phase'][f] = dict(n=k['n'], legal=round(k['legal'] / n, 2), blocked=round(k['blocked'] / n, 2), forced=round(k['forced'] / n, 2), free=round(k['free'] / n, 2), soft=round(k['soft'] / n, 2), trap=round(k['trap'] / n, 2), trap_delay=k['trap_delay'], doomed=k['doomed'])
    # ilk 3 hamle: başlangıç eli ve ilk durumlar
    s0 = L.new_state(); out['hand0'] = [lv['pieces'][c]['id'] for c in L.cards(s0)]; out['legal0'] = [bool(x) for x in L.options(s0)]
    first3 = [st for st, d in seen.items() if d < 3]; n3 = len(first3)
    out['first3'] = dict(states=n3, mean_legal=round(sum(len(memo[s][3]) for s in first3) / n3, 2), with_trap=sum(1 for s in first3 if any(not m[1] for m in memo[s][3])), forced=sum(1 for s in first3 if len(memo[s][3]) == 1))
    dl = defaultdict(list)
    for d, pid, lg in delayed: dl[pid].append((d, lg))
    out['delayed'] = {pid: dict(n=len(v), depth=(min(x[0] for x in v), max(x[0] for x in v)), lag_min=min(x[1][0] for x in v), lag_max=max(x[1][1] for x in v)) for pid, v in dl.items()}
    # son çeyrek: kalan son 25% hamlede karar yoğunluğu
    last = [(st, d) for st, d in seen.items() if d >= NP * 0.75 and memo[st][0]]; out['last25'] = dict(states=len(last), with_choice=sum(1 for st, d in last if len(memo[st][3]) > 1), with_trap=sum(1 for st, d in last if any(not m[1] for m in memo[st][3])))
    # kazanan yol boyunca ortalama legal (tipik oyuncu yolu): her hamle %50 en az 2 yasal
    return out
if __name__ == '__main__':
    for l in (sys.argv[1:] or ['l01', 'l02', 'l03', 'l04', 'l05']): print(json.dumps(run(l), ensure_ascii=False))
