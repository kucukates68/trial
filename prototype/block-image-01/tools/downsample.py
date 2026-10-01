"""96×96 pixel-art kediyi (tools/art_source_cat96.json) NxN küçük bloklara indirger (kutu süzgeci; çizgi/göz gibi küçük ayrıntılar öncelikli)."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); J = json.load(open(os.path.join(H, 'art_source_cat96.json'))); S = J['N']; idx = J['idx']; PAL = J['pal']
W = {12: 3.0, 10: 1.6, 11: 1.6, 13: 2.0, 8: 1.6, 9: 1.6, 14: 1.2}
def downsample(N, cov=0.5, outline_frac=0.32):
    f = S / N; out = {}
    for r in range(N):
        for c in range(N):
            r0, r1, c0, c1 = int(r * f), int((r + 1) * f + 0.999), int(c * f), int((c + 1) * f + 0.999); cnt = {}; tot = 0; non = 0
            for y in range(r0, min(r1, S)):
                for x in range(c0, min(c1, S)):
                    tot += 1; v = idx[y * S + x]
                    if v: non += 1; cnt[v] = cnt.get(v, 0) + 1
            if non / tot < cov: continue
            if cnt.get(1, 0) >= outline_frac * non: out[(r, c)] = 1; continue
            cnt.pop(1, None)
            if not cnt: out[(r, c)] = 1; continue
            out[(r, c)] = max(cnt, key=lambda k: (cnt[k] * W.get(k, 1.0), -k))
    return out
