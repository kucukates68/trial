#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sıkı erişim denetimi (village_access_audit.py)
==============================================
`village_semantic_linter.py` kural 7'sinin gevşekliğini kapatır. Linter yalnızca (a) tüm çizgilerin 0,8 m yakınlıkla
tek bileşende toplandığını ve (b) her kapı patikasının SON noktasının bir L1/L2'ye ≤0,3 m değdiğini sınar.
Burada ek olarak GRAF üzerinde, kapıdan köy girişine kadar yürünebilirlik kanıtlanır:

  * kapı düğümü -> kapı patikasının İLK noktası  (<= 0,30 m)
  * kapı patikası boyunca bina / su / çeşme kesişimi yok
  * kapı patikasının son noktası bir L1/L2 çizgisine T-bağlantıyla değer (<= 0,40 m)
  * çizgi grafı: iki çizgi yalnızca UÇ NOKTA o çizgiye <= 0,40 m değerse ya da kesişirse bağlıdır
    (yan yana paralel yakınlık bağlantı sayılmaz)
  * her öğeden başlangıç noktası Road_L1_Arrival(7,196) çizgisine graf üzerinde ulaşılabilir; batı<->doğu geçişi
    yalnız köprü tabanlarından
Raporlar GERÇEK BİNALAR (kind=building) ile PARSEL girişleri (crop/pasture/orchard) için AYRI verilir.
Kullanım: python3 village_access_audit.py yerlesim.json [yerlesim.html]
"""
import json
import math
import sys
from collections import defaultdict, deque

from village_network_generator import (
    load_objects, is_item, is_parcel, door_node, nearest_on_poly, sample_poly, rect_dist, seg_closest, in_poly,
    poly_edge_dist, poly_len)
from village_semantic_linter import _Map


def seg_intersect(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a, c, d) * ccw(b, c, d) < 0) and (ccw(a, b, c) * ccw(a, b, d) < 0)


def poly_cross(p1, p2):
    for i in range(len(p1) - 1):
        for j in range(len(p2) - 1):
            if seg_intersect(p1[i], p1[i + 1], p2[j], p2[j + 1]):
                return True
    return False


def build_graph(lines, tol=0.40):
    """Çizgiler arası bağlantı: uç nokta -> diğer çizgi <= tol, ya da kesişim. {i: {j: neden}}"""
    adj = defaultdict(dict)
    pts = [[(p['x'], p['z']) for p in l['pts']] for l in lines]
    for i, a in enumerate(pts):
        for j, b in enumerate(pts):
            if i >= j:
                continue
            why = None
            for e in (a[0], a[-1]):
                if nearest_on_poly(b, *e)[0] <= tol:
                    why = 'uç-çizgi'
            for e in (b[0], b[-1]):
                if nearest_on_poly(a, *e)[0] <= tol:
                    why = 'uç-çizgi'
            if why is None and poly_cross(a, b):
                why = 'kesişim'
            if why:
                adj[i][j] = why
                adj[j][i] = why
    return adj, pts


def audit(objs):
    m = _Map(objs)
    lines = [o for o in m.lines]
    adj, pts = build_graph(lines)
    idx = {l['id']: k for k, l in enumerate(lines)}
    root = idx.get('Road_L1_Arrival')
    # köprü tabanı olmadan ulaşılabilirlik testi için: deck çizgilerini işaretle
    seen = {root}
    dq = deque([root])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                dq.append(v)
    # deck'siz grafik: doğu yakası gerçekten yalnız köprüden mi bağlı?
    decks = {k for k, l in enumerate(lines) if l.get('deck')}
    seen2 = {root}
    dq = deque([root])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in seen2 and v not in decks:
                seen2.add(v)
                dq.append(v)
    res = {'building': [], 'parcel': []}
    acc = {l.get('forId'): k for k, l in enumerate(lines) if l.get('forId')}
    l12 = [k for k, l in enumerate(lines) if not l.get('forId') and not l.get('deck')]
    for o in m.items:
        grp = 'parcel' if is_parcel(o) else 'building'
        r = {'id': o['id'], 'problems': []}
        k = acc.get(o['id'])
        if k is None:
            r['problems'].append('kapı patikası yok')
            res[grp].append(r)
            continue
        p = pts[k]
        dn = door_node(o)
        d0 = math.hypot(p[0][0] - dn[0], p[0][1] - dn[1])
        r['door_gap'] = round(d0, 2)
        if d0 > 0.30:
            r['problems'].append('patika kapı düğümünden başlamıyor (%.2f m)' % d0)
        best = min((nearest_on_poly(pts[j], *p[-1])[0], j) for j in l12)
        r['end_gap'] = round(best[0], 2)
        if best[0] > 0.40:
            r['problems'].append('patika ucu L1/L2 çizgisine değmiyor (%.2f m)' % best[0])
        # patika boyunca engel
        hs = lines[k].get('strokeW', 1.2) / 2
        bad = 0
        for x, z in sample_poly(p, 0.4):
            if not m.in_ramp(x, z) and m.water_d(x, z) < 0:
                bad += 1
            for s in [q for q in m.items if q.get('kind') == 'building'] + m.fountains:
                if s is o:
                    continue
                if rect_dist(s, x, z) < hs - 0.02:
                    bad += 1
                    break
        if bad:
            r['problems'].append('patika engele giriyor (%d örnek)' % bad)
        # graf erişilebilirliği
        if k not in seen:
            r['problems'].append('ana yol grafına bağlı değil')
        r['len'] = round(poly_len(p), 1)
        res[grp].append(r)
    # ölü uçlar (L1/L2): ucu başka çizgiye değmeyen
    dead = []
    for k in l12:
        for e, nm in ((pts[k][0], 'baş'), (pts[k][-1], 'son')):
            if lines[k].get('closed') or (pts[k][0] == pts[k][-1]):
                continue
            touch = any(nearest_on_poly(pts[j], *e)[0] <= 0.4 for j in range(len(lines)) if j != k)
            if not touch:
                near_gate = min((math.hypot(e[0] - door_node(q)[0], e[1] - door_node(q)[1]) for q in m.items), default=99)
                entrance = lines[k]['id'] == 'Road_L1_Arrival' and nm == 'baş'
                dead.append((lines[k]['id'], nm, tuple(round(v, 1) for v in e),
                             'GİRİŞ KAPISI (tasarım)' if entrance else
                             ('parsel/bina girişinde biter (%.1f m)' % near_gate if near_gate <= 3.0 else 'ÖLÜ UÇ')))
    # deck'siz erişilebilirlik: doğu yakadaki L1/L2 deck olmadan ulaşılamamalı
    east_ids = [lines[k]['id'] for k in l12 if pts[k][0][0] > 100 and k not in seen2]
    return res, dead, east_ids, len(lines), len(seen)


def report(res, dead, east_ids, nlines, nseen, out=sys.stdout):
    w = lambda *a: print(*a, file=out)
    w('== SIKI ERİŞİM DENETİMİ ==')
    for grp, title in (('building', 'GERÇEK BİNA KAPILARI'), ('parcel', 'PARSEL GİRİŞLERİ (ekin/otlak/bahçe)')):
        rs = res[grp]
        okc = sum(1 for r in rs if not r['problems'])
        w('%s: %d / %d erişilebilir' % (title, okc, len(rs)))
        for r in rs:
            if r['problems']:
                w('   ! %s: %s' % (r['id'], '; '.join(r['problems'])))
        if rs:
            ls = [r['len'] for r in rs if 'len' in r]
            w('   kapı patikası uzunluğu: ort %.1f m, en uzun %.1f m' % (sum(ls) / len(ls), max(ls)))
    w('çizgi grafı: %d çizgi, köy girişinden ulaşılan %d' % (nlines, nseen))
    bad_dead = [d for d in dead if d[3] == 'ÖLÜ UÇ']
    w('serbest uçlar (L1/L2 ucu başka çizgiye değmiyor): %d  -> bunlardan GERÇEK ölü uç: %d' % (len(dead), len(bad_dead)))
    for d in dead:
        w('   - %s %s %s  [%s]' % d)
    w('köprü olmadan doğu yakadan ulaşılamayan L1/L2 çizgi sayısı: %d' % len(east_ids))
    return sum(1 for g in res.values() for r in g if r['problems']) + len(bad_dead)


def geometry_metrics(objs, out=sys.stdout):
    w = lambda *a: print(*a, file=out)
    m = _Map(objs)
    lines = [l for l in m.lines if not l.get('forId')]
    P = {l['id']: [(p['x'], p['z']) for p in l['pts']] for l in lines}
    ids = list(P)
    w('-- yan yana binen çizgiler (>=10 m boyunca 1,8 m içinde; kavşak yaklaşımı dahil)')
    n = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            c = sum(1 for x, z in sample_poly(P[ids[i]], 1.0) if nearest_on_poly(P[ids[j]], x, z)[0] < 1.8)
            if c >= 10:
                w('   %s ~ %s : %d m' % (ids[i], ids[j], c))
                n += 1
    if not n:
        w('   yok')
    forests = [[(p['x'], p['z']) for p in o['pts']] for o in objs if o.get('type') == 'forest' and 'pts' in o]
    w('-- orman poligonu içinden geçen yol uzunluğu (>2 m)')
    for l in lines:
        c = sum(1 for x, z in sample_poly(P[l['id']], 1.0) if any(in_poly(x, z, f) for f in forests))
        if c > 2:
            w('   %s : %d m' % (l['id'], c))
    w('-- köprü ağızlarına (6 m) değen non-deck çizgi sayısı')
    for b in m.bridges:
        a = math.radians(b['rot'])
        ux, uz = math.cos(a), math.sin(a)
        for e in ((b['x'] - ux * b['w'] / 2, b['z'] - uz * b['w'] / 2), (b['x'] + ux * b['w'] / 2, b['z'] + uz * b['w'] / 2)):
            near = [l['id'] for l in lines if not l.get('deck') and nearest_on_poly(P[l['id']], *e)[0] < 6]
            w('   %s (%.0f,%.0f): %s' % (b['id'], e[0], e[1], near))


if __name__ == '__main__':
    objs, _, _ = load_objects(sys.argv[1])
    r = audit(objs)
    n = report(*r)
    geometry_metrics(objs)
    sys.exit(1 if n else 0)
