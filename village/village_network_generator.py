#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosedürel Köy Yol ve Alan Örücü  (village_network_generator.py)
================================================================

`koy-vaziyet-atolyesi.html` (veya ondan indirilen JSON) içindeki yapıları okur ve
binaların içinden / nehrin üstünden geçmeyen, hiyerarşik bir yol ağı ile
bomboş alanları dolduran bahçe / orman / teras poligonlarını üretir.

Koordinat sistemi (HTML ile aynı): metre; X doğu, Z kuzey; yapı koordinatı =
merkez; `rot` derece, saat yönünün tersi (+). rot=0 iken kapı güneye (-Z) bakar,
yani yönelim vektörü = (sin rot, -cos rot).

Algoritma
---------
1. 1x1 m'lik maliyet ızgarası: bina taban alanları (tam döndürülmüş dikdörtgen
   mesafesi), göl, nehir, parseller. Köprü / iskele tabanları geçilebilir.
   Nehir kesin engeldir => batı-doğu geçişi yalnız köprü uçlarından mümkündür.
2. Her yapı için "Kapı Düğümü": cephenin 1.5 m dışı (rot dikkate alınır).
3. Üç kademe:  L1 ana arter (road, 3.8-4.5 m)  ->  L2 mahalle sokağı/halka
   (path, 2.2-2.8 m)  ->  L3 kapı önü patikası (path, 1.2 m).
   Rotalar A* / Dijkstra ile çizilir, görüş hattı (string-pulling) ile sadeleştirilir,
   Chaikin köşe kesme ile yumuşatılır; yumuşatılmış hat tekrar çarpışma testinden
   geçer, geçemezse daha az yumuşatılır.
4. Binalar en yakın sokağa paralel dönecek şekilde döndürülür; yola çok uzak
   binalar sokağa yaklaştırılır (iteratif).
5. Boş alan doldurucu: her yapıya bahçe/avlu; kalan ölü hücreler en büyük
   dikdörtgen yöntemiyle orman / teras / çayır / ekin / otlak / meyve bahçesi.

Kullanım
--------
    python3 village_network_generator.py --html koy-vaziyet-atolyesi.html \
        --out-json koy-yerlesim-koordinatlari.json \
        --inject-html koy-vaziyet-atolyesi.html --preview onizleme.svg

Yalnız standart kütüphane gerekir (Python >= 3.9).
"""
import argparse
import heapq
import json
import math
import os
import re
import sys
import zlib
from collections import defaultdict

SQ2 = math.sqrt(2.0)
DEFAULT_W, DEFAULT_H = 160, 200

# --------------------------------------------------------------------------
#  Yol sınıfları: stroke = çizim kalınlığı (m), cb = merkez çizgisinin bina
#  taban alanına, cw = suya, cp = parsele en az mesafesi (m)
# --------------------------------------------------------------------------
CLS = {
    1: dict(stroke=4.2, cb=2.5, cw=2.4, cp=0.8, type='road'),
    2: dict(stroke=2.5, cb=1.6, cw=1.5, cp=0.5, type='path'),
    3: dict(stroke=1.2, cb=0.9, cw=1.0, cp=0.0, type='path'),
}
PLAN_EXTRAS = (0.8, 0.4, 0.0)       # planlama payı: önce geniş, sonra dar
DOOR_OFF = 1.5                      # kapı düğümü cepheden dışarı (m)
GATE_OFF = 1.2                      # parsel girişi
MAX_L3 = 9.0                        # kapı önü patika uzunluğu hedefi (m)
ITEM_GAP = 1.2                      # yapılar arası asgari boşluk (m)
PARCEL_TYPES = ('crop', 'pasture', 'orchard')


# ==========================================================================
#  Geometri yardımcıları
# ==========================================================================
def local_xy(o, px, pz):
    a = math.radians(o.get('rot') or 0.0)
    c, s = math.cos(a), math.sin(a)
    dx, dz = px - o['x'], pz - o['z']
    return dx * c + dz * s, -dx * s + dz * c


def world_xy(o, lx, lz):
    a = math.radians(o.get('rot') or 0.0)
    c, s = math.cos(a), math.sin(a)
    return o['x'] + lx * c - lz * s, o['z'] + lx * s + lz * c


def rect_dist(o, px, pz):
    lx, lz = local_xy(o, px, pz)
    return math.hypot(max(abs(lx) - o['w'] / 2, 0.0), max(abs(lz) - o['d'] / 2, 0.0))


def facing(o):
    a = math.radians(o.get('rot') or 0.0)
    return math.sin(a), -math.cos(a)


def is_parcel(o):
    return o.get('kind') == 'area' and o.get('type') in PARCEL_TYPES and 'x' in o


def is_item(o):
    return 'x' in o and 'w' in o and (o.get('kind') == 'building' or is_parcel(o))


def door_node(o, off=None):
    if off is None:
        off = GATE_OFF if is_parcel(o) else DOOR_OFF
    fx, fz = facing(o)
    r = o['d'] / 2 + off
    return o['x'] + fx * r, o['z'] + fz * r


def rot_from_facing(fx, fz):
    return math.degrees(math.atan2(fx, -fz))


def snap_deg(d, step=5.0):
    d = round(d / step) * step
    d = ((d + 180.0) % 360.0) - 180.0
    return 0.0 if d == 0 else d


def seg_closest(px, pz, ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    l2 = dx * dx + dz * dz
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
    cx, cz = ax + t * dx, az + t * dz
    return cx, cz, t, math.hypot(px - cx, pz - cz)


def nearest_on_poly(pts, px, pz):
    best = None
    for k in range(len(pts) - 1):
        cx, cz, t, d = seg_closest(px, pz, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1])
        if best is None or d < best[0]:
            best = (d, cx, cz, k)
    return best


def poly_len(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def sample_poly(pts, step=0.5):
    out = [pts[0]]
    for k in range(len(pts) - 1):
        ax, az = pts[k]
        bx, bz = pts[k + 1]
        L = math.hypot(bx - ax, bz - az)
        n = max(1, int(math.ceil(L / step)))
        for i in range(1, n + 1):
            t = i / n
            out.append((ax + (bx - ax) * t, az + (bz - az) * t))
    return out


def in_poly(x, z, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def poly_edge_dist(x, z, poly):
    best = 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        d = seg_closest(x, z, a[0], a[1], b[0], b[1])[3]
        if d < best:
            best = d
    return best


def centroid(poly):
    return sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)


def seeded(key):
    return (zlib.crc32(str(key).encode('utf-8')) & 0xffffffff) / 4294967295.0


def chaikin_open(pts, iters):
    for _ in range(iters):
        n = len(pts)
        if n < 3:
            break
        new = [pts[0]]
        for k in range(n - 1):
            a, b = pts[k], pts[k + 1]
            if k > 0:
                new.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            if k < n - 2:
                new.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        new.append(pts[-1])
        pts = new
    return pts


def chaikin_closed(pts, iters):
    for _ in range(iters):
        n = len(pts)
        new = []
        for k in range(n):
            a, b = pts[k], pts[(k + 1) % n]
            new.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            new.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = new
    return pts


def densify(pts, maxseg):
    out = [pts[0]]
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / maxseg)))
        for i in range(1, n + 1):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def thin(pts, tol=0.04):
    """Neredeyse doğrusal ara noktaları at (dosya boyutu)."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b = out[-1], pts[k + 1]
        d = seg_closest(pts[k][0], pts[k][1], a[0], a[1], b[0], b[1])[3]
        if d > tol:
            out.append(pts[k])
    out.append(pts[-1])
    return out


# ==========================================================================
#  Girdi / çıktı
# ==========================================================================
def load_objects(path):
    txt = open(path, encoding='utf-8').read()
    if path.lower().endswith('.json'):
        data = json.loads(txt)
        m = data.get('map') or {}
        W = int(data.get('mapW') or m.get('width') or DEFAULT_W)
        H = int(data.get('mapH') or m.get('depth') or DEFAULT_H)
        objs = data['objects']
        for i, o in enumerate(objs):
            o.setdefault('uid', 'u%d_%s' % (i, o.get('id')))
        return objs, W, H
    k = txt.index('const DEFAULT_OBJECTS=')
    start = txt.index('[', k)
    objs, _ = json.JSONDecoder().raw_decode(txt[start:])
    mw = re.search(r'let mapW=(\d+),mapH=(\d+)', txt)
    W = int(mw.group(1)) if mw else DEFAULT_W
    H = int(mw.group(2)) if mw else DEFAULT_H
    return objs, W, H


def inject_html(src, dst, objects):
    txt = open(src, encoding='utf-8').read()
    k = txt.index('const DEFAULT_OBJECTS=')
    start = txt.index('[', k)
    _, end = json.JSONDecoder().raw_decode(txt[start:])
    blob = json.dumps(objects, ensure_ascii=False, separators=(',', ':'))
    out = txt[:start] + blob + txt[start + end:]
    for o in objects:                       # palet şablonlarındaki ev ölçüleri de yeni ayak izleriyle eşleşsin
        if o.get('type') == 'house' and 'w' in o:
            out = re.sub(r'("id":"%s","label":"[^"]*","kind":"building","type":"house","w":)[\d.]+(,"d":)[\d.]+' % re.escape(o['id']),
                         lambda mm, o=o: '%s%s%s%s' % (mm.group(1), o['w'], mm.group(2), o['d']), out)
    out = out.replace('__LAYOUT_VER__', '%08x' % (zlib.crc32(blob.encode('utf-8')) & 0xffffffff))
    open(dst, 'w', encoding='utf-8').write(out)


def export_json(path, objects, W, H):
    data = {
        'format': 'village-layout-studio-v1',
        'units': 'meters',
        'coordinateSystem': {'origin': 'northwest/top-left', 'x': 'east/right', 'z': 'north/up',
                             'footprintPosition': 'center'},
        'map': {'width': W, 'depth': H, 'area': W * H, 'gridSnap': 1},
        'mapW': W, 'mapH': H,
        'objects': objects,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


# ==========================================================================
#  Dünya: ızgara alanları ve yönlendirme
# ==========================================================================
class World:
    def __init__(self, objs, W, H):
        self.W, self.H = W, H
        self.N = W * H
        self.objs = objs
        self.items = [o for o in objs if is_item(o)]
        self.bld = [o for o in self.items if o['kind'] == 'building']
        self.parcels = [o for o in self.items if is_parcel(o)]
        self.river = next(o for o in objs if o.get('type') == 'river')
        self.lake = next(o for o in objs if o.get('type') == 'lake')
        self.rpts = [(p['x'], p['z']) for p in self.river['pts']]
        self.rhw = self.river.get('strokeW', 12) / 2.0
        self.lpoly = [(p['x'], p['z']) for p in self.lake['pts']]
        self.bridges = {o['id']: o for o in objs if o.get('type') == 'bridge'}
        self.piers = [o for o in objs if o.get('type') == 'pier']
        self.fountains = [o for o in objs if o.get('type') == 'fountain']
        self.static_areas = [o for o in objs if o.get('kind') == 'area' and 'pts' in o]
        self._pas = {}
        self.compute_fields()

    # -- alan hesapları ------------------------------------------------------
    def rect_cells(self, o, margin):
        W, H = self.W, self.H
        r = math.hypot(o['w'], o['d']) / 2 + margin
        for j in range(max(0, int(o['z'] - r)), min(H, int(o['z'] + r) + 1)):
            for i in range(max(0, int(o['x'] - r)), min(W, int(o['x'] + r) + 1)):
                yield i, j

    def river_edge_dist(self, x, z):
        return min(seg_closest(x, z, self.rpts[k][0], self.rpts[k][1],
                               self.rpts[k + 1][0], self.rpts[k + 1][1])[3]
                   for k in range(len(self.rpts) - 1)) - self.rhw

    def lake_signed(self, x, z):
        d = poly_edge_dist(x, z, self.lpoly)
        return -d if in_poly(x, z, self.lpoly) else d

    def water_dist(self, x, z):
        return min(self.river_edge_dist(x, z), self.lake_signed(x, z))

    def compute_fields(self):
        W, H, N = self.W, self.H, self.N
        self.bd = [99.0] * N      # bina taban alanına mesafe
        self.pd = [99.0] * N      # parsele mesafe
        self.wd = [99.0] * N      # suya mesafe (nehir kenarı / göl kıyısı)
        self.ov = bytearray(N)    # köprü / iskele tabanı
        self.soft = [1.0] * N
        for o in self.items + self.fountains:
            arr = self.bd if o['kind'] in ('building', 'utility') else self.pd
            for i, j in self.rect_cells(o, 8):
                d = rect_dist(o, i + .5, j + .5)
                idx = j * W + i
                if d < arr[idx]:
                    arr[idx] = d
        for j in range(H):
            for i in range(W):
                self.wd[j * W + i] = self.water_dist(i + .5, j + .5)
        for o in list(self.bridges.values()) + self.piers:
            ob = self.ramp_rect(o) if o in self.bridges.values() else o
            for i, j in self.rect_cells(ob, 1):
                if rect_dist(ob, i + .5, j + .5) <= 0.0:
                    self.ov[j * W + i] = 1
        forests = [[(p['x'], p['z']) for p in a['pts']] for a in self.static_areas if a['type'] == 'forest']
        for j in range(H):
            for i in range(W):
                idx = j * W + i
                c = 1.0
                if self.ov[idx]:
                    c = 0.7
                else:
                    b = self.bd[idx]
                    if b < 4.0:
                        c += (4.0 - b) * 0.35
                    if self.pd[idx] <= 0.0:
                        c += 2.5
                    for fp in forests:
                        if in_poly(i + .5, j + .5, fp):
                            c += 1.5
                            break
                self.soft[idx] = c

    def passable(self, cls, extra):
        key = (cls, round(extra, 2))
        if key in self._pas:
            return self._pas[key]
        c = CLS[cls]
        cb, cw, cp = c['cb'] + extra, c['cw'] + extra, c['cp'] + (extra if c['cp'] else 0)
        arr = bytearray(self.N)
        bd, wd, pd, ov = self.bd, self.wd, self.pd, self.ov
        for idx in range(self.N):
            if ov[idx] or (bd[idx] >= cb and wd[idx] >= cw and pd[idx] >= cp):
                arr[idx] = 1
        self._pas[key] = arr
        return arr

    # -- ham mesafe sorgusu (kesin) -----------------------------------------
    def exact_bd(self, x, z):
        best = 99.0
        for o in self.bld + self.fountains:
            r = math.hypot(o['w'], o['d']) / 2
            if abs(o['x'] - x) - r > best or abs(o['z'] - z) - r > best:
                continue
            d = rect_dist(o, x, z)
            if d < best:
                best = d
        return best

    def exact_pd(self, x, z):
        best = 99.0
        for o in self.parcels:
            d = rect_dist(o, x, z)
            if d < best:
                best = d
        return best

    RAMP = 3.0      # köprü uçlarında kıyıya inen rampa (m)

    def ramp_rect(self, b):
        r = dict(b)
        r['w'] = b['w'] + 2 * self.RAMP
        return r

    def in_override(self, x, z, ramp=True):
        for o in self.bridges.values():
            if rect_dist(self.ramp_rect(o) if ramp else o, x, z) <= 0.05:
                return True
        for o in self.piers:
            if rect_dist(o, x, z) <= 0.05:
                return True
        return False

    # -- A* / Dijkstra ------------------------------------------------------
    NEI = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
           (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]

    def cell_of(self, p):
        return min(self.W - 1, max(0, int(p[0]))), min(self.H - 1, max(0, int(p[1])))

    def nearest_passable(self, idx, pas, rad=5):
        W = self.W
        ci, cj = idx % W, idx // W
        best, bd = None, 1e9
        for dj in range(-rad, rad + 1):
            for di in range(-rad, rad + 1):
                i, j = ci + di, cj + dj
                if 0 <= i < W and 0 <= j < self.H and pas[j * W + i]:
                    d = di * di + dj * dj
                    if d < bd:
                        bd, best = d, j * W + i
        return best

    def find_path(self, start, goal=None, targets=None, cls=2, extra=0.0):
        """Hücre merkezlerinden geçen yol; [start, ..., goal/hedef hücre merkezi]."""
        W, H, N = self.W, self.H, self.N
        pas = self.passable(cls, extra)
        soft = self.soft
        si, sj = self.cell_of(start)
        s = sj * W + si
        if not pas[s]:
            s = self.nearest_passable(s, pas)
            if s is None:
                return None
            start = (s % W + .5, s // W + .5)
        g = None
        gi = gj = 0
        if goal is not None:
            gi, gj = self.cell_of(goal)
            g = gj * W + gi
            if not pas[g]:
                g = self.nearest_passable(g, pas)
                if g is None:
                    return None
                gi, gj = g % W, g // W
                goal = (gi + .5, gj + .5)
        INF = 1e18
        G = [INF] * N
        par = [-1] * N
        closed = bytearray(N)
        G[s] = 0.0
        heap = [(0.0, 0.0, s)]
        found = -1
        NEI = self.NEI
        while heap:
            f, gc, u = heapq.heappop(heap)
            if closed[u]:
                continue
            closed[u] = 1
            if (g is not None and u == g) or (targets is not None and targets[u]):
                found = u
                break
            ui, uj = u % W, u // W
            su = soft[u]
            for di, dj, m in NEI:
                vi, vj = ui + di, uj + dj
                if vi < 0 or vj < 0 or vi >= W or vj >= H:
                    continue
                v = vj * W + vi
                if closed[v] or not pas[v]:
                    continue
                if di and dj and not (pas[uj * W + vi] and pas[vj * W + ui]):
                    continue
                ng = gc + m * (soft[v] + su) * 0.5
                if ng < G[v]:
                    G[v] = ng
                    par[v] = u
                    if g is not None:
                        dx, dz = abs(vi - gi), abs(vj - gj)
                        h = 0.7 * (dx + dz + (SQ2 - 2.0) * min(dx, dz))
                    else:
                        h = 0.0
                    heapq.heappush(heap, (ng + h, ng, v))
        if found < 0:
            return None
        cells = []
        u = found
        while u != -1:
            cells.append(u)
            u = par[u]
        cells.reverse()
        pts = [(float(start[0]), float(start[1]))] + [(c % W + .5, c // W + .5) for c in cells]
        if goal is not None:
            pts.append((float(goal[0]), float(goal[1])))
        return pts

    # -- görüş hattı + yumuşatma -------------------------------------------
    def seg_clear(self, a, b, pas, step=0.4):
        W = self.W
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for i in range(n + 1):
            t = i / n
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            ci, cj = int(x), int(z)
            if ci < 0 or cj < 0 or ci >= W or cj >= self.H or not pas[cj * W + ci]:
                return False
        return True

    def simplify(self, pts, pas):
        out = [pts[0]]
        i = 0
        n = len(pts)
        while i < n - 1:
            j = n - 1
            while j > i + 1 and not self.seg_clear(pts[i], pts[j], pas):
                j -= 1
            out.append(pts[j])
            i = j
        return out

    def path_ok(self, pts, cls, tol=0.25, skip_ends=0.0):
        """Kesin mesafelerle doğrula (bina / su / parsel)."""
        c = CLS[cls]
        L = poly_len(pts)
        for k, (x, z) in enumerate(sample_poly(pts, 0.5)):
            if skip_ends and (math.hypot(x - pts[0][0], z - pts[0][1]) < skip_ends):
                continue
            if self.in_override(x, z):
                continue
            if self.exact_bd(x, z) < c['cb'] - tol:
                return False
            if self.water_dist(x, z) < c['cw'] - tol:
                return False
            if c['cp'] and self.exact_pd(x, z) < c['cp'] - tol:
                return False
        return True

    def smooth(self, pts, cls, extra, closed=False, maxseg=8.0, legs=None):
        """LoS sadeleştirme -> Chaikin; doğrulama başarısızsa daha az yumuşat.
        legs verilirse ara noktalar korunur (her bacak ayrı sadeleştirilir)."""
        pas = self.passable(cls, extra)
        raw = pts
        if legs:
            simp = list(self.simplify(legs[0], pas))
            for lg in legs[1:]:
                simp += self.simplify(lg, pas)[1:]
        elif closed:
            # halka: başlangıç = bitiş olduğundan iki yarıyı ayrı sadeleştir
            m = len(raw) // 2
            simp = self.simplify(raw[:m + 1], pas)[:-1] + self.simplify(raw[m:], pas)
        else:
            simp = self.simplify(raw, pas)
        if closed:
            body = simp[:-1] if simp[0] == simp[-1] else simp
            for it in (2, 1, 0):
                cand = chaikin_closed(densify_ring(body, maxseg), it) if it else body
                ring = cand + [cand[0]]
                if self.path_ok(ring, cls):
                    return thin(ring)
            return thin(simp)
        for it in (3, 2, 1):
            cand = chaikin_open(densify(simp, maxseg), it)
            if self.path_ok(cand, cls):
                return thin(cand)
        if self.path_ok(simp, cls):
            return thin(simp)
        return thin(raw)


def densify_ring(pts, maxseg):
    out = []
    n = len(pts)
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        m = max(1, int(math.ceil(L / maxseg)))
        for i in range(m):
            t = i / m
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


# ==========================================================================
#  Yerleşim ayarları (yapı konumu / yönü optimizasyonu)
# ==========================================================================
# Başlangıç konum düzeltmeleri: (x, z). Açıklamalar README / rapor çıktısında.
POSITION_TWEAKS = {
    # liman: ön sıra (kordon–arka sıra–servis sokağı–ön sıra) + hafif kademe (stagger)
    'Dock_Build_01': (44, 61.8), 'Dock_Build_02': (54, 60.3), 'Dock_Build_03': (64, 61.2), 'Dock_Build_04': (74, 62.3),
    'Dock_Build_05': (44, 49.0), 'Dock_Build_06': (55, 50.6), 'Dock_Build_07': (66, 49.4), 'Dock_Build_08': (77, 51.2),
    'Market_Shop_08': (51, 69), 'Market_Shop_09': (39, 69),
    # nalbant (M04) usta atölyesine yakın batı yakaya; sebze tezgâh evi (M11) onun yerine
    'Market_Shop_04': (24, 86), 'Market_Shop_11': (59, 105),
    'W_House_06': (49, 162.5),
    'E_House_02': (121, 178), 'E_House_03': (134, 172.5), 'E_House_14': (119, 117),
    'Stall_A': (40.5, 99.5), 'Stall_B': (53, 91.5),
    # tarım kuşağı (z 75-110): iki sıra, aralarında bahçe yolu (z~93)
    'Crop_Plot_01': (113, 103), 'Orchard_Plot': (133, 101.5), 'Crop_Plot_02': (113, 87), 'Crop_Plot_03': (128, 87),
    # çiftlik kümesi: ahırlar + samanlık ortak avluya, otlak avlunun güneyinde
    'Farm_Barn_01': (142, 89), 'Farm_Barn_02': (153, 90.5), 'Hay_Storage': (154, 79), 'Pasture_Area_01': (146, 64),
}
# sabit yön (derece) ve parsellerin kanonik ölçüsü: kümeler birbirine bakar
FIXED_ROT_VALUES = {'Farm_Barn_01': 0, 'Farm_Barn_02': 0, 'Hay_Storage': -90, 'Pasture_Area_01': 180,
                    'Crop_Plot_01': 0, 'Orchard_Plot': 0, 'Crop_Plot_02': 180, 'Crop_Plot_03': 180,
                    'Boat_House_01': 0, 'Boat_House_02': 0, 'Watermill_01': -90}
CANON_PARCEL = {'Crop_Plot_01': (14, 10), 'Crop_Plot_02': (14, 10), 'Crop_Plot_03': (12, 10),
                'Pasture_Area_01': (25, 20), 'Orchard_Plot': (20, 14)}
HOUSE_SIZES = [(5.2, 4.4), (5.8, 4.8), (6.2, 5.0), (4.8, 4.2), (5.5, 4.6)]   # gerçekçi Alp evi ayak izleri
BOAT_X = {'Boat_House_01': 30, 'Boat_House_02': 19}                          # batı kıyı şeridi
ROT_JITTER = ('house', 'dock', 'barn')                                      # ±5..15° doğal sapma
PIER_X = [50, 62, 74, 86]
BRIDGE_FIX = (21, -12)    # (genişlik boyu w, rot): 12 m'lik nehri her iki yanda >=2.5 m kıyı payıyla aşar
FIXED_ROT = set()
WHEEL_DEPTH = 1.3         # su çarkı: değirmen ayak izi nehre en az bu kadar girer


def shore_z(world, x):
    """Verilen x'te göl kıyısının (kuzey kıyı) z değeri."""
    for zz in [v / 10.0 for v in range(300, 520)]:
        if not in_poly(x, zz, world.lpoly):
            return zz
    return 42.0


def apply_tweaks(world, log):
    by = {o['id']: o for o in world.objs}
    for k, (x, z) in POSITION_TWEAKS.items():
        o = by.get(k)
        if o and 'x' in o:
            if (o['x'], o['z']) != (x, z):
                log.append('konum: %s (%.1f,%.1f) -> (%.1f,%.1f)' % (k, o['x'], o['z'], x, z))
            o['x'], o['z'] = x, z
    # köprüler nehri gerçekten aşsın: merkez sabit, boy ve yön nehre dik/yakın
    for b in world.bridges.values():
        if (b['w'], b['rot']) != BRIDGE_FIX:
            log.append('köprü: %s w=%s rot=%s -> w=%s rot=%s' % ((b['id'], b['w'], b['rot']) + BRIDGE_FIX))
        b['w'], b['rot'] = BRIDGE_FIX
    # parsel kanonik ölçüleri + sabit yönler
    for k, (w, d) in CANON_PARCEL.items():
        if k in by:
            by[k]['w'], by[k]['d'] = w, d
    for k, r in FIXED_ROT_VALUES.items():
        if k in by:
            by[k]['rot'] = r
            FIXED_ROT.add(k)
    # evler: gerçekçi, çeşitli ayak izleri
    for o in world.objs:
        if o.get('type') == 'house' and o.get('kind') == 'building':
            o['w'], o['d'] = HOUSE_SIZES[int(seeded('size' + o['id']) * len(HOUSE_SIZES)) % len(HOUSE_SIZES)]
    # kayık hangarları: batı göl kıyısı, cephe suya bakar, kıyıdan 3.8 m (kordon arada kalır)
    for bid, x in BOAT_X.items():
        o = by.get(bid)
        if o:
            o['x'], o['z'] = x, round(shore_z(world, x) + 3.8 + o['d'] / 2.0, 1)
            log.append('kayık hangarı: %s -> (%.1f,%.1f) kıyı' % (bid, o['x'], o['z']))
    # su değirmeni: batı kıyısında, ayak izinin doğu ucu nehre WHEEL_DEPTH kadar girer (çark suyun içinde)
    mill = by.get('Watermill_01')
    if mill:
        mill['z'] = 171.0
        x = 38.0
        while x < 70:
            mill['x'] = x
            hw, hd = mill['w'] / 2, mill['d'] / 2
            depth = -min(world.river_edge_dist(*world_xy(mill, lx, lz)) for lx in (-hw, hw) for lz in (-hd, 0, hd))
            if depth >= WHEEL_DEPTH:
                break
            x += 0.1
        mill['x'] = round(x, 1)
        log.append('değirmen: çark nehre %.1f m girer (%.1f,%.1f)' % (depth, mill['x'], mill['z']))
    # iskeleler göl kıyısına otursun, nehir ağzından uzak kalsın
    piers = sorted(world.piers, key=lambda p: p['x'])
    for p, px in zip(piers, PIER_X):
        shore = shore_z(world, px)
        newz = round(shore + 1.0 - p['d'] / 2.0, 1)
        if (p['x'], p['z']) != (px, newz):
            log.append('iskele: %s (%.1f,%.1f) -> (%.1f,%.1f)' % (p['id'], p['x'], p['z'], px, newz))
        p['x'], p['z'] = px, newz


def rect_gap(a, b):
    """İki döndürülmüş dikdörtgen arasındaki yaklaşık en kısa mesafe (iç içeyse 0)."""
    ra, rb = math.hypot(a['w'], a['d']) / 2, math.hypot(b['w'], b['d']) / 2
    cd = math.hypot(a['x'] - b['x'], a['z'] - b['z'])
    if cd - ra - rb > 6:
        return 99.0
    best = 99.0
    for src, dst in ((a, b), (b, a)):
        hw, hd = src['w'] / 2, src['d'] / 2
        edges = [(-hw, -hd, hw, -hd), (hw, -hd, hw, hd), (hw, hd, -hw, hd), (-hw, hd, -hw, -hd)]
        for ex0, ez0, ex1, ez1 in edges:
            L = math.hypot(ex1 - ex0, ez1 - ez0)
            n = max(1, int(L / 0.4))
            for i in range(n + 1):
                t = i / n
                wx, wz = world_xy(src, ex0 + (ex1 - ex0) * t, ez0 + (ez1 - ez0) * t)
                d = rect_dist(dst, wx, wz)
                if d < best:
                    best = d
                    if best <= 0:
                        return 0.0
    return best


def resolve_overlaps(world, log, gap=ITEM_GAP, iters=40):
    items = world.items
    for _ in range(iters):
        moved = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a.get('type') == 'stall' or b.get('type') == 'stall':
                    g = 0.4
                else:
                    g = gap
                gp = rect_gap(a, b)
                if gp >= g:
                    continue
                mover = a if a['w'] * a['d'] <= b['w'] * b['d'] else b
                other = b if mover is a else a
                dx, dz = mover['x'] - other['x'], mover['z'] - other['z']
                L = math.hypot(dx, dz) or 1.0
                push = g - gp + 0.15
                ox, oz = mover['x'], mover['z']
                mover['x'] = round(mover['x'] + dx / L * push, 2)
                mover['z'] = round(mover['z'] + dz / L * push, 2)
                if world.water_dist(mover['x'], mover['z']) < 1.0:
                    mover['x'], mover['z'] = ox, oz
                    continue
                moved = True
        if not moved:
            break
    return


def line_components(lines, tol=0.8):
    """Örnek noktalarının yakınlığına göre çizgi bileşenleri (liste listesi, indeks)."""
    hashp = defaultdict(list)
    for k, l in enumerate(lines):
        for x, z in sample_poly(l['pts'], 0.5):
            hashp[(int(x // 1.0), int(z // 1.0))].append((k, x, z))
    parent = list(range(len(lines)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for (cx, cz), lst in hashp.items():
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for k2, x2, z2 in hashp.get((cx + dx, cz + dz), []):
                    for k1, x1, z1 in lst:
                        if k1 != k2 and (x1 - x2) ** 2 + (z1 - z2) ** 2 < tol * tol:
                            a, b = find(k1), find(k2)
                            if a != b:
                                parent[a] = b
    comps = defaultdict(list)
    for k in range(len(lines)):
        comps[find(k)].append(k)
    return list(comps.values())



# ==========================================================================
#  Ağ
# ==========================================================================
class Net:
    def __init__(self, world):
        self.w = world
        self.lines = []          # {'id','label','lvl','pts','stroke','deck','closed','forId'}
        self.byid = {o['id']: o for o in world.objs if 'id' in o}
        self.anchors = {}
        self._tmask = None

    # -- noktaları çöz --------------------------------------------------
    def bridge_ends(self, bid):
        b = self.w.bridges[bid]
        a = math.radians(b.get('rot') or 0.0)
        ux, uz = math.cos(a), math.sin(a)
        p1 = (b['x'] - ux * b['w'] / 2, b['z'] - uz * b['w'] / 2)
        p2 = (b['x'] + ux * b['w'] / 2, b['z'] + uz * b['w'] / 2)
        return (p1, p2) if p1[0] <= p2[0] else (p2, p1)      # (batı, doğu)

    def resolve(self, tok):
        if isinstance(tok, tuple):
            return tok
        if tok in self.anchors:
            return self.anchors[tok]
        kind, _, arg = tok.partition(':')
        if kind == 'ON':
            lid, _, xy = arg.partition(':')
            x, z = (float(v) for v in xy.split(','))
            ln = next(l for l in self.lines if l['id'] == lid)
            r = nearest_on_poly(ln['pts'], x, z)
            return (r[1], r[2])
        if kind == 'D':
            o = self.byid[arg]
            return door_node(o, (GATE_OFF if is_parcel(o) else DOOR_OFF) + 0.8)
        if kind == 'BW':
            return self.bridge_ends(arg)[0]
        if kind == 'BE':
            return self.bridge_ends(arg)[1]
        raise KeyError(tok)

    # -- sorgular -------------------------------------------------------------
    def l12(self):
        return [l for l in self.lines if l['lvl'] <= 2 and not l.get('deck')]

    def nearest_l12(self, x, z, exclude=None):
        best = None
        for l in self.l12():
            if exclude and l['id'] == exclude:
                continue
            r = nearest_on_poly(l['pts'], x, z)
            if best is None or r[0] < best[0]:
                k = r[3]
                ax, az = l['pts'][k]
                bx, bz = l['pts'][k + 1]
                L = math.hypot(bx - ax, bz - az) or 1.0
                best = (r[0], r[1], r[2], (bx - ax) / L, (bz - az) / L, l)
        return best

    def target_mask(self):
        W, H = self.w.W, self.w.H
        m = bytearray(W * H)
        for l in self.l12():
            for x, z in sample_poly(l['pts'], 0.5):
                i, j = int(x), int(z)
                if 0 <= i < W and 0 <= j < H:
                    m[j * W + i] = 1
        return m

    # -- ekleme ---------------------------------------------------------------
    def add(self, id_, label, lvl, pts, stroke, **kw):
        d = dict(id=id_, label=label, lvl=lvl, pts=[(float(a), float(b)) for a, b in pts], stroke=stroke)
        d.update(kw)
        self.lines.append(d)
        return d

    def snap_end(self, pts, which, maxd=3.5):
        x, z = pts[0] if which == 0 else pts[-1]
        best = self.nearest_l12(x, z)
        if best and 0.02 < best[0] <= maxd:
            p = (best[1], best[2])
            if which == 0:
                pts.insert(0, p)
            else:
                pts.append(p)
        return pts

    def route(self, wps, lvl, closed=False, hard=False):
        W = self.w
        pts_w = [self.resolve(t) for t in wps]
        for extra in PLAN_EXTRAS:
            seq = pts_w + ([pts_w[0]] if closed else [])
            legs, ok = [], True
            for a, b in zip(seq, seq[1:]):
                p = W.find_path(a, goal=b, cls=lvl, extra=extra)
                if p is None:
                    ok = False
                    break
                legs.append(p)
            if not ok:
                continue
            raw = list(legs[0])
            for l in legs[1:]:
                raw += l[1:]
            sm = W.smooth(raw, lvl, extra, closed=closed, legs=legs if hard else None)
            return sm, extra
        # son çare: ulaşılamayan ara noktaları atla
        extra = PLAN_EXTRAS[-1]
        seq = pts_w + ([pts_w[0]] if closed else [])
        raw, cur, skipped, legs = None, seq[0], 0, []
        for b in seq[1:]:
            p = W.find_path(cur, goal=b, cls=lvl, extra=extra)
            if p is None:
                skipped += 1
                continue
            legs.append(p)
            raw = list(p) if raw is None else raw + p[1:]
            cur = b
        if raw is None or len(raw) < 2:
            return None, None
        if skipped:
            print('  ~ %d ara nokta atlandi' % skipped, file=sys.stderr)
        return W.smooth(raw, lvl, extra, closed=closed and cur == seq[-1], legs=legs if hard else None), extra

    def build_spec(self, sp):
        pts, extra = self.route(sp['wps'], sp['lvl'], sp.get('closed', False), sp.get('hard', False))
        if pts is None:
            print('  ! rota bulunamadi:', sp['id'], file=sys.stderr)
            return None
        if sp.get('optional') and not sp.get('closed'):
            a, b = pts[0], pts[-1]
            if poly_len(pts) > 2.0 * math.hypot(a[0] - b[0], a[1] - b[1]) + 4:
                print('  ~ %s atlandi (dolambacli rota)' % sp['id'], file=sys.stderr)
                return None
        if not sp.get('closed'):
            sn = sp.get('snap', (False, False))
            if sn[0]:
                pts = self.snap_end(list(pts), 0)
            if sn[1]:
                pts = self.snap_end(list(pts), 1)
        return self.add(sp['id'], sp['label'], sp['lvl'], pts, sp['stroke'], closed=sp.get('closed', False),
                        extra=extra)

    def ensure_connected(self):
        """Ana ağdan kopuk kalan L1/L2 bileşenlerini en yakın noktadan L2 ile bağla."""
        W = self.w
        n_added = 0
        for _ in range(8):
            idx = [k for k, l in enumerate(self.lines) if l['lvl'] <= 2]
            sub = [self.lines[k] for k in idx]
            comps = line_components(sub)
            if len(comps) <= 1:
                return n_added
            comps.sort(key=lambda c: -sum(poly_len(sub[k]['pts']) for k in c))
            main = comps[0]
            msamp = [pt for k in main for pt in sample_poly(sub[k]['pts'], 2.0)]
            best = None
            for comp in comps[1:]:
                for k in comp:
                    for p in sample_poly(sub[k]['pts'], 2.0):
                        for q in msamp:
                            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                            if best is None or d < best[0]:
                                best = (d, p, q)
                if best:
                    break
            if not best:
                return n_added
            _, p, q = best
            pts = None
            for extra in PLAN_EXTRAS:
                raw = W.find_path(p, goal=q, cls=2, extra=extra)
                if raw:
                    pts = W.smooth(raw, 2, extra)
                    break
            if pts is None:
                print('  ! baglanti kurulamadi', p, q, file=sys.stderr)
                return n_added
            n_added += 1
            self.add('Street_AutoLink_%02d' % n_added, 'Bağlantı sokağı', 2, pts, 2.2, auto=True)
        return n_added

    # -- L3: kapı önü kılcal patikalar ------------------------------------------
    def build_access(self):
        W = self.w
        mask = self.target_mask()
        res = {}
        for o in W.items:
            door = door_node(o)
            path = None
            for extra in (0.3, 0.0):
                p = W.find_path(door, targets=mask, cls=3, extra=extra)
                if p:
                    path = p
                    break
            if path is None:
                tw = {1: 0.0}
                print('  ! kapi patikasi bulunamadi:', o['id'], file=sys.stderr)
                continue
            end = path[-1]
            near = self.nearest_l12(end[0], end[1])
            pas = W.passable(3, extra)
            simp = W.simplify(path, pas)
            pts = list(simp)
            if math.hypot(pts[0][0] - door[0], pts[0][1] - door[1]) > 0.05:
                pts.insert(0, door)
            if near and near[0] < 2.0:
                pts[-1] = (near[1], near[2])
            sm = chaikin_open(densify(pts, 6.0), 2)
            if not W.path_ok(sm, 3, tol=0.35, skip_ends=2.0):
                sm = pts
            sm = thin(sm)
            if len(sm) < 2:
                sm = [door, (near[1], near[2])]
            ln = self.add('Access_' + o['id'], 'Kapı önü: ' + (o.get('label') or o['id']), 3, sm, 1.2,
                          forId=o['id'])
            res[o['id']] = ln
        return res


# ==========================================================================
#  Yol iskeleti (hiyerarşi)
# ==========================================================================
def offset_polygon(poly, dist):
    n = len(poly)
    cx, cz = centroid(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        a = (p1[0] - p0[0], p1[1] - p0[1])
        b = (p2[0] - p1[0], p2[1] - p1[1])
        la, lb = math.hypot(*a) or 1, math.hypot(*b) or 1
        n1 = (a[1] / la, -a[0] / la)
        n2 = (b[1] / lb, -b[0] / lb)
        nx, nz = n1[0] + n2[0], n1[1] + n2[1]
        ln = math.hypot(nx, nz) or 1
        nx, nz = nx / ln, nz / ln
        if nx * (p1[0] - cx) + nz * (p1[1] - cz) < 0:
            nx, nz = -nx, -nz
        out.append((p1[0] + nx * dist, p1[1] + nz * dist))
    return out


def area_poly(world, aid):
    a = next(o for o in world.objs if o.get('id') == aid)
    return [(p['x'], p['z']) for p in a['pts']]


def ring_order(world, ids, center):
    items = [next(o for o in world.items if o['id'] == i) for i in ids]
    return [o['id'] for o in sorted(items, key=lambda o: math.atan2(o['z'] - center[1], o['x'] - center[0]))]


def build_specs(world, net):
    plaza = area_poly(world, 'Market_Plaza')
    PC = centroid(plaza)
    net.anchors.update({'PC': PC, 'FA_W': (40.0, 55.5), 'HUB_E': (102.0, 141.5)})
    shops = ['Market_Shop_%02d' % i for i in range(1, 13)]
    ring = ring_order(world, shops, PC)
    upper = offset_polygon(area_poly(world, 'Upper_Common_Green'), 4.5)
    lower = offset_polygon(area_poly(world, 'Lower_Common_Green'), 4.5)
    S = []

    def L1(id_, label, wps, stroke=4.2, snap=(False, False)):
        S.append(dict(id=id_, label=label, lvl=1, wps=wps, stroke=stroke, snap=snap))

    def L2(id_, label, wps, stroke=2.5, snap=(True, True), closed=False, hard=False, optional=False):
        S.append(dict(id=id_, label=label, lvl=2, wps=wps, stroke=stroke, snap=snap, closed=closed, hard=hard,
                      optional=optional))

    # Pazar çevre halkası ilk kurulur: ana yollar meydanın içinden değil halkadan bağlanır
    L2('Ring_Market', 'Pazar çevre halkası', ['D:' + i for i in ring], 2.8, snap=(False, False), closed=True, hard=True)

    # ---- Seviye 1: ana arterler (meydan içi yaya alanı + çeşme; yollar halkaya biner) ----
    L1('Road_L1_Arrival', 'Kuzeybatı dağ yolu', [(7, 196), (8, 181), (10, 165), (14, 150), (19, 137), (19, 122),
                                                  (17, 110), (18, 100), 'ON:Ring_Market:30,97'], 4.5)
    L1('Road_L1_Market_UpperBridge', 'Meydan–üst köprü yolu',
       ['ON:Ring_Market:56,108', (59, 117), (61, 127), 'BW:Bridge_Upper'], 4.2)
    L1('Road_L1_Market_LowerBridge', 'Meydan–alt köprü yolu',
       ['ON:Ring_Market:62,90', (70, 86), 'BW:Bridge_Lower'], 4.2)
    L1('Road_L1_Market_Harbor', 'Pazar–liman ana ticaret yolu',
       ['ON:Ring_Market:33,78', (33, 70), (34, 62), (38, 56), 'FA_W'], 4.2)
    L1('Road_L1_East_Upper', 'Üst köprü–doğu mahalle yolu', ['BE:Bridge_Upper', (91, 137), 'HUB_E'], 4.0)
    L1('Road_L1_East_Trunk', 'Doğu mahalle servis yolu',
       ['HUB_E', (104, 128), (103, 112), (101, 96), (99, 82), 'BE:Bridge_Lower'], 4.0)
    L1('Road_L1_East_North', 'Doğu üst mahalle kolu', ['HUB_E', (102, 152), (102, 168)], 3.8)
    L1('Road_L1_Farm_Trunk', 'Güneydoğu çiftlik ana yolu',
       ['BE:Bridge_Lower', (106, 77.5), (122, 78.5), (136, 79.5), (146, 80)], 4.0)

    # ---- Seviye 2: mahalle sokakları / ringler -----------------------------
    # Batı yamaç: eğime paralel teraslı sokaklar + zikzaklı patika
    L2('Street_West_S1', 'Yamaç sokağı 1', [(9, 178), (24, 177.5), (37, 177), (49, 177.5)])
    L2('Street_West_S2', 'Yamaç sokağı 2', [(11, 160.5), (25, 160.5), (38, 160.5), (52, 157)])
    L2('Street_West_S3', 'Yamaç sokağı 3', [(15, 145), (30, 145), (44, 144), (55, 141)])
    L2('Path_West_Zigzag', 'Yamaç zikzak patikası', [(16, 177.5), (27, 173), (30, 166.5), (25, 161), (29, 155),
                                                      (31, 149), (29, 145)], 2.2)
    L2('Path_West_Riverbank', 'Nehir kıyısı patikası', [(49, 177.5), (51, 166), (52, 156), (55, 146), (58, 139),
                                                         'BW:Bridge_Upper'], 2.2, snap=(True, False))
    L2('Street_Market_North', 'Pazar kuzey sokağı', [(19, 123), (30, 127), (43, 128.5), (55, 127), (62, 124)])
    # Pazar çevresi halkası: dükkân kapılarından
    # Liman: sahil kordonu, servis sokağı, ara geçitler
    L2('Promenade_West', 'Batı kıyı kordonu', [(38, 44.4), (30, 44.2), (21, 44.1), (13, 44.0)], 2.5)
    L2('Promenade_Pier', 'Sahil kordonu', [(38, 44.4), (50, 44.3), (62, 44.2), (74, 44.2), (86, 44.4), (88, 45.5)], 2.8)
    L2('Street_Dock_Service', 'Depo arka servis sokağı', [(38, 55.5), (50, 55.5), (62, 55.5), (74, 55.5), (84, 55.5)], 2.5)
    L2('Street_Dock_West', 'Liman batı bağlantısı', [(38, 55.5), (36.5, 50), (38, 44.4)], 2.5)
    L2('Street_Dock_East', 'Liman doğu bağlantısı', [(84, 55.5), (87, 50), (88, 45.5)], 2.5)
    for k, x in enumerate((49.8, 60.3, 71.8), 1):
        L2('Alley_Dock_%d' % k, 'Depo arası geçit %d' % k, [(x, 55.5), (x, 44.3)], 2.2, optional=True)
    # Doğu mahallesi: yeşil alanları saran döngüler
    L2('Street_East_Top', 'Doğu üst sokağı', [(102, 168), (114, 167), (126, 167), (138, 167), (145, 165)])
    L2('Loop_East_Upper', 'Üst ortak yeşil döngüsü', [(round(x, 1), round(z, 1)) for x, z in upper], 2.5,
       snap=(False, False), closed=True, hard=True)
    L2('Loop_East_Lower', 'Alt mahalle avlusu döngüsü', [(round(x, 1), round(z, 1)) for x, z in lower], 2.5,
       snap=(False, False), closed=True, hard=True)
    L2('Street_East_LinkUpper', 'Üst döngü bağlantısı', [(103, 150), (111, 150)])
    L2('Street_East_LinkLower', 'Alt döngü bağlantısı', [(104, 128), (111, 129)])
    L2('Street_East_Mid', 'Doğu mahalle ara sokağı', [(137, 150), (146, 142), (148, 128), (147, 112)])
    L2('Street_East_South', 'Doğu alt sokağı', [(103, 111), (112, 109.7), (124, 109.7), (137, 109.7), (145, 110)])
    L2('Lane_Farm_Garden', 'Bahçe ve çiftlik yolu', [(101, 95), (113, 93.3), (127, 93.3), (136, 93.3)])
    return S


# ==========================================================================
#  Ağ kurulumu + yön / konum optimizasyonu
# ==========================================================================
def build_network(world):
    net = Net(world)
    for bid in sorted(world.bridges):
        e = net.bridge_ends(bid)
        net.add('Road_Crossing_' + bid, 'Köprü geçişi', 1, [e[0], e[1]], 3.8, deck=True)
    specs = build_specs(world, net)
    for sp in specs:
        net.build_spec(sp)
    net.ensure_connected()
    net.l3 = net.build_access()
    return net


def init_rotations(world):
    plaza = area_poly(world, 'Market_Plaza')
    cx, cz = centroid(plaza)
    for o in world.items:
        if o.get('type') in ('shop', 'stall'):
            fx, fz = cx - o['x'], cz - o['z']
            o['rot'] = snap_deg(rot_from_facing(fx, fz))
            FIXED_ROT.add(o['id'])      # pazar yapıları meydana (halka merkezine) bakar


def assign_rotations(world, net):
    changed = 0
    for o in world.items:
        if o['id'] in FIXED_ROT:
            continue
        near = net.nearest_l12(o['x'], o['z'])
        if not near:
            continue
        d, px, pz, ux, uz, _ = near
        vx, vz = px - o['x'], pz - o['z']
        L = math.hypot(vx, vz)
        if L < 1e-6:
            continue
        n = (-uz, ux)
        if n[0] * vx + n[1] * vz < 0:
            n = (uz, -ux)
        cosang = (n[0] * vx + n[1] * vz) / L
        f = n if cosang > 0.75 else (vx / L, vz / L)
        if is_parcel(o):
            cards = [(0, 0, -1), (90, 1, 0), (180, 0, 1), (270, -1, 0)]
            r, _, _ = max(cards, key=lambda c: c[1] * f[0] + c[2] * f[1])
            old = int(round((o.get('rot') or 0) / 90.0)) % 4
            new = int(r // 90)
            if (old % 2) != (new % 2):
                o['w'], o['d'] = o['d'], o['w']
            nr = float(snap_deg(r, 90.0))
        else:
            nr = float(snap_deg(rot_from_facing(*f)))
            if o.get('type') in ROT_JITTER:
                u = seeded('rj' + o['id'])
                nr += (1 if seeded('rs' + o['id']) < .5 else -1) * (5 + 10 * u)
                nr = round(((nr + 180.0) % 360.0) - 180.0, 1)
        if nr != (o.get('rot') or 0):
            changed += 1
        o['rot'] = nr
    return changed


def item_ok_at(world, net, o, x, z):
    """Taşınmış konumda çakışma / yol / su kontrolü."""
    save = (o['x'], o['z'])
    o['x'], o['z'] = x, z
    ok = True
    for other in world.items:
        if other is o:
            continue
        if rect_gap(o, other) < ITEM_GAP:
            ok = False
            break
    if ok:
        hw, hd = o['w'] / 2, o['d'] / 2
        for lx, lz in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd), (0, 0)):
            wx, wz = world_xy(o, lx, lz)
            if world.water_dist(wx, wz) < 1.0:
                ok = False
                break
    if ok:
        for l in net.lines:
            if l['lvl'] > 2:
                continue
            c = CLS[l['lvl']]
            for px, pz in sample_poly(l['pts'], 1.0):
                if abs(px - x) > 14 or abs(pz - z) > 14:
                    continue
                if rect_dist(o, px, pz) < c['cb'] - 0.1 and not world.in_override(px, pz):
                    ok = False
                    break
            if not ok:
                break
    o['x'], o['z'] = save
    return ok


def pull_in(world, net, log):
    moved = 0
    order = sorted(world.items, key=lambda o: -poly_len(net.l3[o['id']]['pts']) if o['id'] in net.l3 else 0)
    for o in order:
        ln = net.l3.get(o['id'])
        if not ln:
            continue
        L = poly_len(ln['pts'])
        if L <= MAX_L3 or o['id'] in FIXED_ROT or o.get('type') in ('stall', 'shop', 'dock', 'boathouse'):
            continue
        a, b = ln['pts'][0], ln['pts'][-1]
        vx, vz = b[0] - a[0], b[1] - a[1]
        D = math.hypot(vx, vz)
        if D < 1e-6:
            continue
        want = min(L - 5.0, D - 2.5, 6.0)
        for f in (1.0, 0.75, 0.5, 0.3):
            s = want * f
            if s < 0.8:
                break
            nx, nz = round(o['x'] + vx / D * s, 1), round(o['z'] + vz / D * s, 1)
            if item_ok_at(world, net, o, nx, nz):
                log.append('yaklaştırıldı: %s (%.1f,%.1f) -> (%.1f,%.1f)' % (o['id'], o['x'], o['z'], nx, nz))
                o['x'], o['z'] = nx, nz
                moved += 1
                break
    return moved


# ==========================================================================
#  Boş alan doldurucu
# ==========================================================================
def road_distance_field(world, net):
    """Hücre merkezinden en yakın yol kenarına (merkez çizgi - stroke/2) mesafe."""
    W, H = world.W, world.H
    rd = [99.0] * (W * H)
    for l in net.lines:
        hs = l['stroke'] / 2.0
        R = int(hs + 3)
        for x, z in sample_poly(l['pts'], 0.5):
            for j in range(max(0, int(z) - R), min(H, int(z) + R + 1)):
                for i in range(max(0, int(x) - R), min(W, int(x) + R + 1)):
                    d = math.hypot(i + .5 - x, j + .5 - z) - hs
                    idx = j * W + i
                    if d < rd[idx]:
                        rd[idx] = d
    return rd


def poly_conflict(world, rd, poly_pts, ignore_id=None, road_pad=0.35):
    xs = [p[0] for p in poly_pts]
    zs = [p[1] for p in poly_pts]
    W, H = world.W, world.H
    n = len(poly_pts)
    pts = []
    for k in range(n):
        a, b = poly_pts[k], poly_pts[(k + 1) % n]
        pts += sample_poly([a, b], 0.6)
    for gx in range(int(min(xs)), int(max(xs)) + 1):
        for gz in range(int(min(zs)), int(max(zs)) + 1):
            if in_poly(gx + .5, gz + .5, poly_pts):
                pts.append((gx + .5, gz + .5))
    for x, z in pts:
        i, j = int(x), int(z)
        if i < 0 or j < 0 or i >= W or j >= H:
            return True
        if rd[j * W + i] < road_pad:
            return True
        if world.water_dist(x, z) < 0.3 and not world.in_override(x, z):
            return True
        for o in world.items:
            if o.get('id') == ignore_id:
                continue
            ext = o['w'] / 2 + o['d'] / 2 + 1
            if abs(o['x'] - x) > ext or abs(o['z'] - z) > ext:
                continue
            if rect_dist(o, x, z) < 0.3:
                return True
    return False


def make_gardens(world, net, rd, statics):
    gardens = []
    court_polys = [[(p['x'], p['z']) for p in a['pts']] for a in statics
                   if a.get('type') in ('plaza', 'courtyard')]
    for o in world.bld:
        if o.get('type') == 'stall':
            continue
        if any(in_poly(o['x'], o['z'], cp) for cp in court_polys):
            continue
        typ = 'meadow' if o.get('type') in ('barn', 'mill', 'boathouse') else 'courtyard'
        w, d = o['w'], o['d']
        done = None
        for side in ('back', 'left', 'right'):
            for depth in (min(6.0, d * 1.3 + 2.5), 4.5, 3.4, 2.6, 1.9):
                for sc in (1.0, 0.8, 0.62, 0.45):
                    pad = 1.0 * sc
                    if side == 'back':
                        loc = [(-w / 2 - pad, d / 2 + 0.3), (w / 2 + pad, d / 2 + 0.3),
                               (w / 2 + pad, d / 2 + 0.3 + depth), (-w / 2 - pad, d / 2 + 0.3 + depth)]
                    else:
                        sg = -1 if side == 'left' else 1
                        x0, x1 = sg * (w / 2 + 0.3), sg * (w / 2 + 0.3 + depth)
                        loc = [(x0, -d / 2 - pad * .3), (x1, -d / 2 - pad * .3), (x1, d / 2 + pad), (x0, d / 2 + pad)]
                    poly = [world_xy(o, *p) for p in loc]
                    if not poly_conflict(world, rd, poly, ignore_id=None):
                        done = poly
                        break
                if done:
                    break
            if done:
                break
        if done:
            gardens.append(dict(uid='gen_garden_' + o['id'], id='Garden_' + o['id'], label='', kind='area',
                                type=typ, elevation=0, gen=True, forId=o['id'],
                                pts=[{'x': round(p[0], 1), 'z': round(p[1], 1)} for p in done]))
    return gardens


def coverage_mask(world, net, areas):
    W, H = world.W, world.H
    cov = bytearray(W * H)
    for a in areas:
        poly = [(p['x'], p['z']) for p in a['pts']]
        xs, zs = [p[0] for p in poly], [p[1] for p in poly]
        for j in range(max(0, int(min(zs))), min(H, int(max(zs)) + 1)):
            for i in range(max(0, int(min(xs))), min(W, int(max(xs)) + 1)):
                if in_poly(i + .5, j + .5, poly):
                    cov[j * W + i] = 1
    for o in world.items:
        for i, j in world.rect_cells(o, 1):
            if rect_dist(o, i + .5, j + .5) <= 0.45:
                cov[j * W + i] = 1
    for idx in range(W * H):
        if world.wd[idx] < 0.35 or world.ov[idx]:
            cov[idx] = 1
    rd = road_distance_field(world, net)
    for idx in range(W * H):
        if rd[idx] < 0.55:
            cov[idx] = 1
    return cov, rd


ZONE_LABELS = {'kuzey_cayir': 'Kuzey Alp çayırı', 'kuzey_orman': 'Kuzey dağ ormanı',
               'nehir_cayir': 'Nehir kıyısı çayırı', 'bati_orman': 'Batı yamaç ormanı'}


def zone_type(world, cx, cz):
    """Hücre merkezi -> (tür, bölge adı). Düşük frekanslı gürültü: sınırlar organik, bölgeler büyük."""
    rv = world.river_edge_dist(cx, cz)
    lk = world.lake_signed(cx, cz)
    n = math.sin(cx * 0.11 + 1.7) + math.cos(cz * 0.09 + 0.4) + math.sin((cx + cz) * 0.05)
    if cz > 188:
        return 'forest', 'kuzey_orman'
    if cx < 16:
        return 'forest', 'bati_orman'
    if cx > 148 and cz > 150:
        return 'forest', ''
    if 62 < cx < 100 and 138 < cz < 190 and rv > 1:          # nehir ile doğu mahalle arası vadi
        return ('forest', 'kuzey_orman') if cz > 181 else ('meadow', 'kuzey_cayir')
    if rv < 6 and cx < 95:
        return ('forest', '') if (n > 1.0 and cz > 140) else ('meadow', 'nehir_cayir')
    if cx < 62 and 128 < cz < 195:                            # batı yamaç
        return ('terrace', '') if n > 0.4 else (('forest', '') if n < -1.0 else ('meadow', ''))
    if cx >= 100 and cz < 118:                                # çiftlik
        if lk < 14:
            return 'meadow', ''
        return ('crop', '') if n > 0.9 else (('orchard', '') if n < -0.9 else ('pasture', ''))
    if lk < 16:
        return 'meadow', ''
    if cx >= 100:                                             # doğu mahalle (ekin/meyve yok: kuzey yamaç gölgeli)
        return ('courtyard', '') if n > 1.0 else (('forest', '') if n < -1.1 else ('meadow', ''))
    if cx < 70 and cz > 60:                                   # pazar çevresi
        return ('courtyard', '') if n > 1.2 else (('forest', '') if n < -1.3 else ('meadow', ''))
    return 'meadow', ''


def _components(cells_by_type):
    """{(i,j): tür} -> [(tür, [hücre...])] (4-komşuluk, aynı tür)."""
    seen, out = set(), []
    for c, ty in cells_by_type.items():
        if c in seen:
            continue
        st, comp = [c], []
        seen.add(c)
        while st:
            i, j = st.pop()
            comp.append((i, j))
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (i + d[0], j + d[1])
                if nb not in seen and cells_by_type.get(nb) == ty:
                    seen.add(nb)
                    st.append(nb)
        out.append((ty, comp))
    return out


def _trace_outer(cells):
    S = set(cells)
    edges = {}

    def add(a, b):
        edges.setdefault(a, []).append(b)
    for (i, j) in S:
        if (i, j - 1) not in S:
            add((i, j), (i + 1, j))
        if (i + 1, j) not in S:
            add((i + 1, j), (i + 1, j + 1))
        if (i, j + 1) not in S:
            add((i + 1, j + 1), (i, j + 1))
        if (i - 1, j) not in S:
            add((i, j + 1), (i, j))
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur = [start], start
        while True:
            outs = edges.get(cur)
            if not outs:
                break
            nxt = outs.pop()
            if not outs:
                del edges[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        if len(loop) >= 3:
            loops.append(loop)

    def sarea(lp):
        return 0.5 * sum(lp[k][0] * lp[(k + 1) % len(lp)][1] - lp[(k + 1) % len(lp)][0] * lp[k][1] for k in range(len(lp)))
    return max(loops, key=lambda lp: abs(sarea(lp))) if loops else None


def _rdp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dmax, k = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = seg_closest(pts[i][0], pts[i][1], a[0], a[1], b[0], b[1])[3]
        if d > dmax:
            dmax, k = d, i
    if dmax > tol:
        return _rdp(pts[:k + 1], tol)[:-1] + _rdp(pts[k:], tol)
    return [a, b]


def fill_regions(world, net, cov, min_cells=5):
    """Ölü hücreleri tür/bölgeye göre birleştirip tek parça, yumuşatılmış poligonlar üretir."""
    W, H = world.W, world.H
    typ, zone = {}, {}
    for j in range(H):
        for i in range(W):
            if not cov[j * W + i]:
                typ[(i, j)], zone[(i, j)] = zone_type(world, i + .5, j + .5)
    for _ in range(3):                                         # küçük parçaları komşu türe kat
        for ty, comp in _components(typ):
            if len(comp) >= 8:
                continue
            votes = defaultdict(int)
            for (i, j) in comp:
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (i + d[0], j + d[1])
                    if nb in typ and typ[nb] != ty:
                        votes[typ[nb]] += 1
            if votes:
                best = max(votes, key=votes.get)
                for c in comp:
                    typ[c] = best
    regions = []
    for ty, comp in _components(typ):
        if len(comp) < min_cells:
            continue
        loop = _trace_outer(comp)
        if not loop:
            continue
        ring = _rdp(loop + [loop[0]], 0.7)[:-1]
        if len(ring) < 3:
            continue
        ring = chaikin_closed(ring, 2)
        zn = max(set(zone[c] for c in comp), key=lambda z: sum(1 for c in comp if zone[c] == z))
        regions.append((len(comp), ty, zn, ring))
    regions.sort(key=lambda r: -r[0])                          # büyükler altta, küçükler üstte
    out = []
    for n, (cnt, ty, zn, ring) in enumerate(regions, 1):
        lab = ZONE_LABELS.get(zn, '') if cnt >= 150 else ''
        out.append(dict(uid='gen_fill_%03d' % n, id='Fill_%s_%03d' % (ty.capitalize(), n), label=lab, kind='area',
                        type=ty, elevation=0, gen=True,
                        pts=[{'x': round(x, 1), 'z': round(z, 1)} for x, z in thin(ring + [ring[0]], 0.08)[:-1]]))
    return out


# ==========================================================================
#  Doğrulama
# ==========================================================================
def validate(world, net, objects):
    rep = {}
    W = world
    viol_bld, viol_water = [], []
    for l in net.lines:
        hs = l['stroke'] / 2.0
        for x, z in sample_poly(l['pts'], 0.5):
            if W.in_override(x, z, ramp=False):
                continue
            bd = W.exact_bd(x, z)
            if bd < hs - 0.02:
                viol_bld.append((l['id'], round(x, 1), round(z, 1), round(bd, 2)))
            wd = W.water_dist(x, z)
            if wd < 0:
                viol_water.append((l['id'], round(x, 1), round(z, 1), round(wd, 2)))
    rep['road_in_building'] = viol_bld
    rep['road_in_water'] = viol_water
    ov = []
    for i in range(len(W.items)):
        for j in range(i + 1, len(W.items)):
            if rect_gap(W.items[i], W.items[j]) <= 0.0:
                ov.append((W.items[i]['id'], W.items[j]['id']))
    rep['item_overlap'] = ov
    comps_idx = line_components(net.lines)
    comps = [[net.lines[k]['id'] for k in c] for c in comps_idx]
    main = max(comps, key=len)
    rep['components'] = len(comps)
    rep['disconnected_lines'] = [i for c in comps if c is not main for i in c]
    lengths = {1: 0.0, 2: 0.0, 3: 0.0}
    for l in net.lines:
        lengths[l['lvl']] += poly_len(l['pts'])
    rep['length_m'] = {k: round(v, 1) for k, v in lengths.items()}
    far = []
    for o in W.items:
        ln = net.l3.get(o['id'])
        if not ln:
            far.append((o['id'], 'L3 yok'))
            continue
        e = ln['pts'][-1]
        nr = net.nearest_l12(e[0], e[1])
        if not nr or nr[0] > 0.3:
            far.append((o['id'], 'L3 ucu yola değmiyor'))
    rep['access_problem'] = far
    rep['l3_len'] = {o['id']: round(poly_len(net.l3[o['id']]['pts']), 1) for o in W.items if o['id'] in net.l3}
    return rep


# ==========================================================================
#  Önizleme (SVG)
# ==========================================================================
AREA_STYLE = {'lake': ('#67bdc6', '#318b9a'), 'forest': ('#78966f', '#587553'), 'meadow': ('#c6dda4', '#92aa72'),
              'terrace': ('#b9cd91', '#829867'), 'courtyard': ('#d8c69e', '#a58c63'), 'crop': ('#d0bd70', '#a18b46'),
              'pasture': ('#a6c57d', '#748f58'), 'orchard': ('#a8c887', '#6e945d'), 'plaza': ('#decda8', '#a48d62')}


def write_svg(path, objects, W, H, S=5):
    def px(x): return x * S
    def pz(z): return (H - z) * S
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W * S, H * S, W * S, H * S),
           '<rect width="100%" height="100%" fill="#e2edcf"/>']
    for o in objects:
        if o['kind'] == 'area' and 'pts' in o:
            f, e = AREA_STYLE.get(o['type'], AREA_STYLE['meadow'])
            pts = ' '.join('%.1f,%.1f' % (px(p['x']), pz(p['z'])) for p in o['pts'])
            if o['type'] == 'forest':
                f = '#6f8f68'
            out.append('<polygon points="%s" fill="%s" fill-opacity=".85" stroke="%s" stroke-width=".8"/>' % (pts, f, e))
    for o in objects:
        if o['kind'] == 'area' and 'x' in o:
            f, e = AREA_STYLE.get(o['type'], AREA_STYLE['meadow'])
            out.append('<g transform="translate(%.1f %.1f) rotate(%.1f)"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                       'fill="%s" fill-opacity=".6" stroke="%s" stroke-dasharray="4 2"/></g>' % (
                           px(o['x']), pz(o['z']), -(o.get('rot') or 0), -o['w'] * S / 2, -o['d'] * S / 2, o['w'] * S, o['d'] * S, f, e))
    for o in objects:
        if o['kind'] == 'path':
            d = ' '.join('%s%.1f,%.1f' % ('L' if i else 'M', px(p['x']), pz(p['z'])) for i, p in enumerate(o['pts']))
            if o['type'] == 'river':
                out.append('<path d="%s" fill="none" stroke="#48adbd" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>' % (d, o['strokeW'] * S))
            else:
                col, edge = ('#e6d2a7', '#987b52') if o['type'] == 'road' else ('#f3e8d1', '#b19a73')
                out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>' % (d, edge, o['strokeW'] * S + 1.2))
                out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>' % (d, col, o['strokeW'] * S))
    for o in objects:
        if o['kind'] in ('building', 'utility'):
            w, d = o['w'] * S, o['d'] * S
            fill = {'house': '#bf805c', 'shop': '#d0a66a', 'dock': '#869da0', 'boathouse': '#869da0',
                    'stall': '#d0a66a'}.get(o.get('type'), '#9d774f')
            if o['kind'] == 'utility':
                fill = '#91a4a2'
            g = '<g transform="translate(%.1f %.1f) rotate(%.1f)"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#4a3626" stroke-width="1"/>' % (
                px(o['x']), pz(o['z']), -(o.get('rot') or 0), -w / 2, -d / 2, w, d, fill)
            if o['kind'] == 'building':
                g += '<path d="M%.1f %.1f L0 %.1f L%.1f %.1f" fill="#ead1a7" stroke="#4a3626" stroke-width=".8"/>' % (-w / 2 + 1, -d / 2 + 2, -d / 2 - min(3, d * .18), w / 2 - 1, -d / 2 + 2)
                g += '<path d="M-5 %.1f L0 %.1f L5 %.1f Z" fill="#e0573c" stroke="#fff" stroke-width=".6"/>' % (d / 2 + 2.5, d / 2 + 9, d / 2 + 2.5)
            out.append(g + '</g>')
            if o['kind'] == 'building':
                out.append('<text x="%.1f" y="%.1f" font-size="5" text-anchor="middle" fill="#fff" stroke="#34483f" stroke-width=".6" paint-order="stroke" font-family="sans-serif">%s</text>' % (
                    px(o['x']), pz(o['z']) + 2, re.sub(r'(_House|_Shop|_Build|Market_|Dock_|Farm_)', '', o['id'])[:7]))
    out.append('</svg>')
    open(path, 'w', encoding='utf-8').write('\n'.join(out))


# ==========================================================================
#  Ana akış
# ==========================================================================
def line_to_obj(l):
    o = dict(uid=('access_' + l['forId']) if l.get('forId') else 'gen_' + l['id'].lower(),
             id=l['id'], label=l['label'], kind='path', type=CLS[l['lvl']]['type'],
             strokeW=l['stroke'],
             pts=[{'x': round(x, 1), 'z': round(z, 1)} for x, z in l['pts']],
             lvl=l['lvl'], gen=True)
    if l.get('forId'):
        o['forId'] = l['forId']
    if l.get('deck'):
        o['deck'] = True
    return o


def main():
    ap = argparse.ArgumentParser(description='Prosedürel köy yol ve alan örücü')
    ap.add_argument('--html', default='input/koy-vaziyet-atolyesi.orig.html', help='kaynak HTML veya JSON')
    ap.add_argument('--out-json', default='koy-yerlesim-koordinatlari.json')
    ap.add_argument('--inject-html', help='DEFAULT_OBJECTS dizisi bu HTML dosyasına gömülür (yazılacak dosya)')
    ap.add_argument('--inject-from', help='gömme için şablon HTML (varsayılan: --html)')
    ap.add_argument('--preview', help='SVG önizleme')
    ap.add_argument('--iters', type=int, default=4)
    a = ap.parse_args()

    objs, W, H = load_objects(a.html)
    # önceki üretimi temizle: yollar, kapı patikaları, üretilmiş alanlar
    objs = [o for o in objs if not (o.get('gen') or (o.get('kind') == 'path' and o.get('type') in ('road', 'path')))]
    if not any(o.get('type') == 'fountain' for o in objs):
        objs.append(dict(uid='fountain_main', id='Village_Fountain', label='Köy çeşmesi', kind='utility',
                         type='fountain', x=47, z=96, w=4, d=4, rot=0))
    log = []
    world = World(objs, W, H)
    apply_tweaks(world, log)
    resolve_overlaps(world, log)
    init_rotations(world)
    net = None
    for it in range(a.iters):
        world.compute_fields()
        world._pas = {}
        net = build_network(world)
        last = it == a.iters - 1
        print('tur %d: L1/L2 çizgi=%d, kapı patikası=%d' % (it + 1, len([l for l in net.lines if l['lvl'] < 3]), len(net.l3)),
              file=sys.stderr)
        if last:
            break
        ch = assign_rotations(world, net)
        mv = pull_in(world, net, log)
        resolve_overlaps(world, log)
        print('   dönen=%d, yaklaşan=%d' % (ch, mv), file=sys.stderr)

    statics = [o for o in objs if o.get('kind') == 'area' and 'pts' in o]
    cov0, rd = coverage_mask(world, net, statics)
    dead0 = sum(1 for v in cov0 if not v)
    gardens = make_gardens(world, net, rd, statics)
    cov1, rd = coverage_mask(world, net, statics + gardens)
    dead1 = sum(1 for v in cov1 if not v)
    fills = fill_regions(world, net, cov1)
    cov2, _ = coverage_mask(world, net, statics + gardens + fills)
    dead2 = sum(1 for v in cov2 if not v)

    rep = validate(world, net, objs)

    static_nonitem = [o for o in objs if o.get('kind') == 'area' and 'pts' in o]
    river = [o for o in objs if o.get('type') == 'river']
    line_objs = [line_to_obj(l) for l in net.lines if l['lvl'] == 1] + \
                [line_to_obj(l) for l in net.lines if l['lvl'] == 2] + \
                [line_to_obj(l) for l in net.lines if l['lvl'] == 3]
    rest = [o for o in objs if o not in static_nonitem and o not in river]
    for o in rest:
        for k in ('x', 'z'):
            if k in o:
                o[k] = round(o[k], 1)
        if 'rot' in o:
            o['rot'] = int(round(o['rot']))
        for k in ('w', 'd'):
            if k in o:
                o[k] = round(o[k], 2)
    final = fills + static_nonitem + gardens + river + line_objs + rest

    export_json(a.out_json, final, W, H)
    if a.inject_html:
        inject_html(a.inject_from or a.html, a.inject_html, final)
    if a.preview:
        write_svg(a.preview, final, W, H)

    import village_semantic_linter as _lint
    lint_res = _lint.lint(final)

    print('\n== RAPOR ==', file=sys.stderr)
    for l in log:
        print('  ' + l, file=sys.stderr)
    print('toplam öğe:', len(final), '| L1/L2/L3 uzunluk (m):', rep['length_m'], file=sys.stderr)
    print('ölü alan (m²): başlangıç=%d, bahçelerden sonra=%d, son=%d (harita %d m²)' % (dead0, dead1, dead2, W * H),
          file=sys.stderr)
    print('yol-bina çakışması:', len(rep['road_in_building']), rep['road_in_building'][:8], file=sys.stderr)
    print('yol-su çakışması:', len(rep['road_in_water']), rep['road_in_water'][:8], file=sys.stderr)
    print('yapı çakışması:', rep['item_overlap'], file=sys.stderr)
    print('bileşen sayısı:', rep['components'], 'kopuk:', rep['disconnected_lines'], file=sys.stderr)
    print('kapı sorunları:', rep['access_problem'], file=sys.stderr)
    _lint.report(lint_res, sys.stderr)
    far = sorted(rep['l3_len'].items(), key=lambda kv: -kv[1])[:6]
    print('en uzun kapı patikaları:', far, file=sys.stderr)


if __name__ == '__main__':
    main()
