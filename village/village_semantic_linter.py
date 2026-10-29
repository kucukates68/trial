#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Köy Mantık ve Semantik Denetimcisi  (village_semantic_linter.py)
================================================================
Yerleşim JSON'unu (veya atölye HTML'ini) bir seviye tasarımcısı gibi 7 kurala karşı denetler.
Aynı 7 kural HTML editöründe canlı çalışır (sağ panel: "Tasarım Mantık Denetimi: X / 7").

  1  Su kıyısı zorunluluğu   kayık hangarları kıyıdan <= 4 m ve cephesi suya uygun; değirmen çarkı suda
  2  Çiftlik bütünlüğü       samanlık ahıra <= 18 m; otlak göle >= 12 m ve ahıra <= 15 m
  3  Tarım coğrafyası        ekin/meyve parselleri z 52..165 arasında ve birbirine komşu; kuzey/güney dolgusunda ekin yok
  4  Zanaat / liman komşuluğu nalbant (M04) atölyeye <= 30 m; balıkçı dükkânları (M06/M09/M10) pazarın güney yarısında
  5  Çeşitlilik (anti copy-paste) evler >= 4.6x4.0 m ve >= 3 farklı ölçü; ardışık 3'lüde kademe (>=1.5 m) ve açı farkı
  6  Meydan bütünlüğü        çeşme meydanın içinde; L1/L2 yol çeşmenin 4 m yakınından geçmez; tezgâhlar çeşmeye bakar
  7  Sıfır çarpışma + erişim  bina-bina / bina-su / yol-bina / yol-su = 0; tek bağlı ağ; 56/56 kapı patikası ağa değer
     (Su değirmeni çarkı suya girmek zorunda olduğundan bina-su kuralında muaftır.)

Kullanım:  python3 village_semantic_linter.py koy-yerlesim-koordinatlari.json   (çıkış kodu = kalan kural sayısı)
"""
import json
import math
import re
import sys

from village_network_generator import (
    in_poly, poly_edge_dist, seg_closest, world_xy, rect_dist, facing, is_item, is_parcel, centroid,
    sample_poly, nearest_on_poly, line_components, load_objects, door_node)

N_RULES = 7
TARGET_RE = re.compile(r'(W_House|Market_Shop|Stall_|Dock_Build|Boat_House|E_House|Farm_Barn|Crop_Plot|Pasture_Area|'
                       r'Orchard_Plot|Hay_Storage|Watermill|Repair_Workshop)')


class _Map:
    """Denetim için hafif harita görünümü (ızgara hesabı yok)."""

    def __init__(self, objects):
        self.objs = objects
        self.by = {o['id']: o for o in objects if 'id' in o}
        self.items = [o for o in objects if is_item(o)]
        self.river = next((o for o in objects if o.get('type') == 'river'), None)
        self.lake = next((o for o in objects if o.get('type') == 'lake'), None)
        self.rpts = [(p['x'], p['z']) for p in self.river['pts']] if self.river else []
        self.rhw = (self.river.get('strokeW', 12) / 2.0) if self.river else 0
        self.lpoly = [(p['x'], p['z']) for p in self.lake['pts']] if self.lake else []
        self.bridges = [o for o in objects if o.get('type') == 'bridge']
        self.piers = [o for o in objects if o.get('type') == 'pier']
        self.fountains = [o for o in objects if o.get('type') == 'fountain']
        self.lines = [o for o in objects if o.get('kind') == 'path' and o.get('type') in ('road', 'path')]
        self.plaza = next((o for o in objects if o.get('id') == 'Market_Plaza'), None)

    def river_d(self, x, z):
        if not self.rpts:
            return 99.0
        return min(seg_closest(x, z, self.rpts[k][0], self.rpts[k][1], self.rpts[k + 1][0], self.rpts[k + 1][1])[3]
                   for k in range(len(self.rpts) - 1)) - self.rhw

    def lake_d(self, x, z):
        if not self.lpoly:
            return 99.0
        d = poly_edge_dist(x, z, self.lpoly)
        return -d if in_poly(x, z, self.lpoly) else d

    def water_d(self, x, z):
        return min(self.river_d(x, z), self.lake_d(x, z))

    def in_ramp(self, x, z):
        for b in self.bridges:
            r = dict(b)
            r['w'] = b['w'] + 6.0
            if rect_dist(r, x, z) <= 0.05:
                return True
        return any(rect_dist(p, x, z) <= 0.05 for p in self.piers)


def boundary(o, step=0.5):
    hw, hd = o['w'] / 2, o['d'] / 2
    out = []
    edges = [(-hw, -hd, hw, -hd), (hw, -hd, hw, hd), (hw, hd, -hw, hd), (-hw, hd, -hw, -hd)]
    for ax, az, bx, bz in edges:
        n = max(1, int(math.hypot(bx - ax, bz - az) / step))
        for i in range(n):
            t = i / n
            out.append(world_xy(o, ax + (bx - ax) * t, az + (bz - az) * t))
    return out


def rect_gap(a, b):
    best = 99.0
    for src, dst in ((a, b), (b, a)):
        for x, z in boundary(src, 0.4):
            d = rect_dist(dst, x, z)
            if d < best:
                best = d
    return best


def _lake_d_rect(m, o):
    return min(m.lake_d(x, z) for x, z in boundary(o))


# ---------------------------------------------------------------- kurallar ---
def rule1(m):
    msgs = []
    for bid in ('Boat_House_01', 'Boat_House_02'):
        o = m.by.get(bid)
        if not o:
            msgs.append('%s yok' % bid)
            continue
        pts = boundary(o)
        best = min(pts, key=lambda p: m.water_d(*p))
        d = m.water_d(*best)
        if d < -0.05:
            msgs.append('%s suyun içinde' % bid)
        elif d > 4.0:
            msgs.append('%s kıyıdan %.1f m uzak (en çok 4 m)' % (bid, d))
        else:
            # en yakın su noktasına doğru yön
            wx, wz = _nearest_water_point(m, o)
            vx, vz = wx - o['x'], wz - o['z']
            L = math.hypot(vx, vz) or 1.0
            fx, fz = facing(o)
            if (fx * vx + fz * vz) / L < -0.2:
                msgs.append('%s cephesi sudan uzağa bakıyor' % bid)
    mill = m.by.get('Watermill_01')
    if not mill:
        msgs.append('Watermill_01 yok')
    else:
        depth = -min(m.river_d(x, z) for x, z in boundary(mill, 0.25))
        if depth < 1.0:
            msgs.append('Watermill_01 çarkı suya %.1f m giriyor (en az 1.0 m)' % max(depth, 0))
    return msgs


def _nearest_water_point(m, o):
    """Yapının merkezinden en yakın su noktası (halka halka tarama)."""
    for r in range(1, 60):
        rr = r * 0.5
        hits = []
        for k in range(36):
            a = k * math.pi / 18
            x, z = o['x'] + math.cos(a) * rr, o['z'] + math.sin(a) * rr
            if m.water_d(x, z) <= 0.3:
                hits.append((x, z))
        if hits:
            return hits[0]
    return (o['x'], o['z'])


def rule2(m):
    msgs = []
    hay, pa = m.by.get('Hay_Storage'), m.by.get('Pasture_Area_01')
    barns = [m.by[i] for i in ('Farm_Barn_01', 'Farm_Barn_02') if i in m.by]
    if not (hay and pa and barns):
        return ['çiftlik öğeleri eksik']
    dh = min(rect_gap(hay, b) for b in barns)
    if dh > 18:
        msgs.append('Samanlık ahırdan %.1f m uzak (en çok 18 m)' % dh)
    dl = _lake_d_rect(m, pa)
    if dl < 12:
        msgs.append('Otlak göle %.1f m yakın (en az 12 m)' % dl)
    dp = min(rect_gap(pa, b) for b in barns)
    if dp > 15:
        msgs.append('Otlak ahırlardan %.1f m uzak (en çok 15 m)' % dp)
    return msgs


def rule3(m):
    msgs = []
    plots = [m.by[i] for i in ('Crop_Plot_01', 'Crop_Plot_02', 'Crop_Plot_03', 'Orchard_Plot') if i in m.by]
    for p in plots:
        if not (52 <= p['z'] <= 165):
            msgs.append('%s z=%.0f: tarım kuşağı dışında (52..165)' % (p['id'], p['z']))
    for p in plots:
        if len(plots) > 1 and min(rect_gap(p, q) for q in plots if q is not p) > 15:
            msgs.append('%s diğer tarım parsellerine komşu değil' % p['id'])
    for o in m.objs:
        if o.get('gen') and o.get('kind') == 'area' and o.get('type') in ('crop', 'orchard') and 'pts' in o:
            cz = centroid([(p['x'], p['z']) for p in o['pts']])[1]
            if cz > 140 or cz < 52:
                msgs.append('%s (%s) z=%.0f: ekin/meyve olamaz' % (o['id'], o['type'], cz))
    return msgs


def rule4(m):
    msgs = []
    ws, nal = m.by.get('Repair_Workshop_01'), m.by.get('Market_Shop_04')
    if ws and nal:
        d = math.hypot(ws['x'] - nal['x'], ws['z'] - nal['z'])
        if d > 30:
            msgs.append('Nalbant (M04) atölyeden %.0f m uzak (en çok 30 m)' % d)
    cz = centroid([(p['x'], p['z']) for p in m.plaza['pts']])[1] if m.plaza else 96.5
    for sid in ('Market_Shop_06', 'Market_Shop_09', 'Market_Shop_10'):
        s = m.by.get(sid)
        if s and s['z'] >= cz:
            msgs.append('%s pazarın kuzey yarısında (balıkçı dükkânları güneyde olmalı)' % sid)
    return msgs


TRIPLES = [('W_House_%02d', (1, 2, 3)), ('W_House_%02d', (4, 5, 6)), ('E_House_%02d', (1, 2, 3)),
           ('E_House_%02d', (5, 6, 7)), ('E_House_%02d', (8, 9, 10)), ('E_House_%02d', (11, 12, 13)),
           ('Dock_Build_%02d', (1, 2, 3)), ('Dock_Build_%02d', (2, 3, 4)),
           ('Dock_Build_%02d', (5, 6, 7)), ('Dock_Build_%02d', (6, 7, 8))]


def rule5(m):
    msgs = []
    houses = [o for o in m.items if o.get('type') == 'house']
    small = [o['id'] for o in houses if o['w'] < 4.6 or o['d'] < 4.0]
    if small:
        msgs.append('Kulübe boyutu (<4.6x4.0 m): ' + ', '.join(small[:5]) + ('…' if len(small) > 5 else ''))
    sizes = {(round(o['w'], 1), round(o['d'], 1)) for o in houses}
    if len(sizes) < 3:
        msgs.append('Ev ölçüsü çeşitliliği yetersiz (%d tür, en az 3)' % len(sizes))
    for fmt, ids in TRIPLES:
        tri = [m.by.get(fmt % i) for i in ids]
        if any(t is None for t in tri):
            continue
        zr = max(t['z'] for t in tri) - min(t['z'] for t in tri)
        rr = max(t.get('rot', 0) for t in tri) - min(t.get('rot', 0) for t in tri)
        if zr < 1.5 or rr < 5:
            msgs.append('%s..: asker sırası (z farkı %.1f m, açı farkı %.0f°)' % (tri[0]['id'], zr, rr))
    return msgs


def rule6(m):
    msgs = []
    f = m.fountains[0] if m.fountains else None
    if not f:
        return ['Village_Fountain yok']
    if m.plaza and not in_poly(f['x'], f['z'], [(p['x'], p['z']) for p in m.plaza['pts']]):
        msgs.append('Çeşme meydanın dışında')
    for l in m.lines:
        if l.get('deck') or l.get('forId'):
            continue
        d = nearest_on_poly([(p['x'], p['z']) for p in l['pts']], f['x'], f['z'])[0]
        if d < 4.0:
            msgs.append('%s çeşmeye %.1f m yakın (en az 4 m)' % (l.get('id'), d))
    for sid in ('Stall_A', 'Stall_B'):
        s = m.by.get(sid)
        if s:
            vx, vz = f['x'] - s['x'], f['z'] - s['z']
            L = math.hypot(vx, vz) or 1.0
            fx, fz = facing(s)
            if (fx * vx + fz * vz) / L < 0.5:
                msgs.append('%s çeşmeye bakmıyor' % sid)
    return msgs


def rule7(m):
    msgs = []
    its = m.items
    for i in range(len(its)):
        for j in range(i + 1, len(its)):
            a, b = its[i], its[j]
            if math.hypot(a['x'] - b['x'], a['z'] - b['z']) > (math.hypot(a['w'], a['d']) + math.hypot(b['w'], b['d'])) / 2:
                continue
            if rect_gap(a, b) <= 0.0:
                msgs.append('çarpışma: %s ↔ %s' % (a['id'], b['id']))
    for o in its:
        if o.get('kind') != 'building' or o.get('type') == 'mill':
            continue
        if any(m.water_d(x, z) < -0.05 for x, z in boundary(o)):
            msgs.append('%s suyun içinde' % o['id'])
    solids = [o for o in its if o.get('kind') == 'building'] + m.fountains
    n_b = n_w = 0
    for l in m.lines:
        hs = l.get('strokeW', 2) / 2.0
        pts = [(p['x'], p['z']) for p in l['pts']]
        for x, z in sample_poly(pts, 0.5):
            if not m.in_ramp(x, z) and m.water_d(x, z) < 0:
                n_w += 1
            for o in solids:
                if abs(o['x'] - x) > o['w'] / 2 + o['d'] / 2 + 3 and abs(o['z'] - z) > o['w'] / 2 + o['d'] / 2 + 3:
                    continue
                if rect_dist(o, x, z) < hs - 0.02:
                    n_b += 1
                    break
    if n_b:
        msgs.append('yol-bina kesişimi: %d örnek nokta' % n_b)
    if n_w:
        msgs.append('yol-su kesişimi: %d örnek nokta' % n_w)
    lines = [{'pts': [(p['x'], p['z']) for p in l['pts']]} for l in m.lines]
    comps = line_components(lines)
    if len(comps) > 1:
        msgs.append('ağ %d parçaya bölünmüş' % len(comps))
    acc = {l.get('forId'): l for l in m.lines if l.get('forId')}
    l12 = [[(p['x'], p['z']) for p in l['pts']] for l in m.lines if not l.get('forId') and not l.get('deck')]
    miss = []
    for o in its:
        if not TARGET_RE.match(o['id']):
            continue
        l = acc.get(o['id'])
        if not l:
            miss.append(o['id'])
            continue
        e = l['pts'][-1]
        if min(nearest_on_poly(pl, e['x'], e['z'])[0] for pl in l12) > 0.3:
            miss.append(o['id'])
    if miss:
        msgs.append('yola bağlanmayan kapı patikası: ' + ', '.join(miss[:6]))
    return msgs


RULES = [
    ('Su kıyısı zorunluluğu', rule1), ('Çiftlik ve hayvancılık bütünlüğü', rule2),
    ('Tarım ve coğrafya uyumu', rule3), ('Zanaat ve liman komşuluğu', rule4),
    ('Organik çeşitlilik (anti copy-paste)', rule5), ('Meydan ve odak noktası', rule6),
    ('Sıfır çarpışma + %100 erişim', rule7),
]


def lint(objects):
    m = _Map(objects)
    res = []
    for k, (name, fn) in enumerate(RULES, 1):
        msgs = fn(m)
        res.append(dict(rule=k, name=name, ok=not msgs, messages=msgs))
    return res


def report(res, out=sys.stdout):
    ok = sum(1 for r in res if r['ok'])
    print('Tasarım Mantık Denetimi: %d / %d kural geçti' % (ok, len(res)), file=out)
    for r in res:
        print('  %s %d. %s' % ('GEÇTİ' if r['ok'] else 'KALDI', r['rule'], r['name']), file=out)
        for msg in r['messages'][:12]:
            print('       - ' + msg, file=out)
    return ok


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'koy-yerlesim-koordinatlari.json'
    objs, _, _ = load_objects(path)
    ok = report(lint(objs))
    sys.exit(len(RULES) - ok)
