#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orijinal koy-vaziyet-atolyesi.html dosyasına "Yol Mantık Editörü" özelliklerini ekler:
   (1) Yolları Otomatik Ör / Yenile, (2) kapı yönü işareti + mıknatıs, (3) bağlantı denetimi.
   Kullanım: python3 tools/patch_html_editor.py girdi.html cikti.html tools/editor_block.js"""
import sys

src, dst, blockf = sys.argv[1:4]
t = open(src, encoding='utf-8').read()
block = open(blockf, encoding='utf-8').read()


def rep(old, new, count=1):
    global t
    n = t.count(old)
    if n != count:
        raise SystemExit('Beklenen %d eşleşme, bulunan %d:\n%s' % (count, n, old[:120]))
    t = t.replace(old, new)


# --- CSS -----------------------------------------------------------------
rep('.top-actions label{font-size:12px;color:var(--muted);display:flex;gap:4px;align-items:center}',
    '.top-actions label{font-size:12px;color:var(--muted);display:flex;gap:4px;align-items:center}.top-actions input[type=checkbox]{width:auto}.stat-bad{color:#b7503d}.stat-ok{color:#2d7a4b}')

# --- üst bar ---------------------------------------------------------------
rep('<button id="applySize">Harita ölçüsünü uygula</button>',
    '<button id="applySize">Harita ölçüsünü uygula</button>'
    '<button id="autoRoute" class="primary" title="Tüm kapı önü patikalarını bina içinden ve nehir üstünden geçmeden, en yakın ana sokağa yeniden hesaplar">Yolları Otomatik Ör / Yenile</button>'
    '<label title="Bir yapıyı sürükleyip bırakınca kapı patikası otomatik yeniden örülür"><input type="checkbox" id="autoOnDrop" checked> sürükleyince yenile</label>'
    '<label title="Yenilerken yapının kapısı en yakın sokağa bakacak şekilde döner"><input type="checkbox" id="autoAlign" checked> kapıyı yola çevir</label>')

# --- depolama anahtarı (yeni ağ eski taslağın üstüne binmesin) -------------------
rep("STORAGE='village-layout-studio-v2'", "STORAGE='village-layout-studio-v3'")

# --- editör bloğu ------------------------------------------------------------
rep('palette();\ntry{const saved=localStorage.getItem(STORAGE)', block + "\n$('autoRoute').addEventListener('click',()=>refreshAll($('autoAlign').checked));\npalette();\ntry{const saved=localStorage.getItem(STORAGE)")

# başlangıç yükleme: eski göç kodunu sadeleştir
a = t.index("try{const saved=localStorage.getItem(STORAGE)")
b = t.index("\n})();\n</script>")
t = t[:a] + ("try{const saved=localStorage.getItem(STORAGE);if(saved)loadState(JSON.parse(saved));else{objects=JSON.parse(JSON.stringify(DEFAULT_OBJECTS));render();persist()}}"
             "catch{objects=JSON.parse(JSON.stringify(DEFAULT_OBJECTS));render()}") + t[b:]

# --- loadState: uid garanti -----------------------------------------------------
rep("objects=Array.isArray(data.objects)?data.objects:[];selected=null;",
    "objects=(Array.isArray(data.objects)?data.objects:[]).map((o,i)=>o.uid?o:{...o,uid:genId()+i});selected=null;")

# --- ipuçları -------------------------------------------------------------------
rep("road:'Haritaya sırayla tıklayarak yol köşe noktalarını koy. “Çizimi bitir” veya Enter ile tamamla.'",
    "road:'Haritaya sırayla tıklayarak yol köşe noktalarını koy. Mevcut yol düğümüne, bina kapısına ve yol kenarına mıknatıs gibi yapışır. “Çizimi bitir” veya Enter ile tamamla.'")
rep("path:'Haritaya sırayla tıklayarak patika noktalarını koy. “Çizimi bitir” veya Enter ile tamamla.'",
    "path:'Haritaya sırayla tıklayarak patika noktalarını koy. Yol düğümüne ve bina kapısına yapışır (turuncu halka = kapı, yeşil = düğüm, mavi = yol kenarı). “Çizimi bitir” veya Enter ile tamamla.'")
rep("drawPts=[];const hints=", "drawPts=[];hover=null;const hints=")

# --- render ------------------------------------------------------------------------
rep("function render(){const vbW=mapW*S,vbH=mapH*S;", "function render(){connBad=computeConn();const vbW=mapW*S,vbH=mapH*S;")
rep("</g>${drawPts.length?`<polyline", "</g><g id=\"overlay\" pointer-events=\"none\"></g>${drawPts.length?`<polyline")
rep("updateInspector();updateStats();$('mapCaption')", "drawOverlay();updateInspector();updateStats();$('mapCaption')")

# yol etiketleri: kapı önü patikalarında etiket yok, üretilmişlerde yalnız ad
rep("if(mid)s+=`<text x=\"${mapPx(mid.x)}\" y=\"${mapPy(mid.z)-3}\" text-anchor=\"middle\" class=\"map-label\">${esc(o.label)} ${esc(o.id)}</text>`",
    "if(mid&&!isAccess(o))s+=`<text x=\"${mapPx(mid.x)}\" y=\"${mapPy(mid.z)-3}\" text-anchor=\"middle\" class=\"map-label\">${esc(o.label)}${o.gen?'':' '+esc(o.id)}</text>`")
# üretilmiş alanlar: ince, kesiksiz kenar
rep("fill-opacity=\".82\" stroke=\"${st.edge}\" stroke-width=\"1.4\" stroke-dasharray=\"${o.type==='lake'?'':'4 2'}\"/>",
    "fill-opacity=\"${o.gen?.9:.82}\" stroke=\"${st.edge}\" stroke-width=\"${o.gen?.5:1.4}\" stroke-dasharray=\"${o.type==='lake'||o.gen?'':'4 2'}\"/>")
# kapı yönü işareti + bağlantı uyarısı
rep(" s+=`</g><text x=\"${x}\" y=\"${y+3}\" text-anchor=\"middle\" class=\"map-id\">",
    " if(isItem(o)){s+=`<path d=\"M-6 ${d/2+1.5}L0 ${d/2+10}L6 ${d/2+1.5}Z\" fill=\"#e0573c\" stroke=\"#fff\" stroke-width=\".8\"/><rect x=\"-7\" y=\"${d/2-1.4}\" width=\"14\" height=\"3\" rx=\"1\" fill=\"#e0573c\" stroke=\"#fff\" stroke-width=\".7\"/>`;if(connBad.has(o.id))s+=`<rect x=\"${-w/2-4}\" y=\"${-d/2-4}\" width=\"${w+8}\" height=\"${d+8}\" rx=\"3\" fill=\"none\" stroke=\"#d11a2a\" stroke-width=\"2.4\"><title>${esc(o.id)}: ${esc(connBad.get(o.id))}</title></rect>`}\n s+=`</g><text x=\"${x}\" y=\"${y+3}\" text-anchor=\"middle\" class=\"map-id\">")

# alan etiketi: etiket boşsa (üretilmiş bahçe/orman parçaları) hiçbir şey yazma
rep("class=\"map-label\">${esc(o.label)}${o.elevation?` · ${o.elevation}m`:''}</text>", "class=\"map-label\">${o.label?esc(o.label)+(o.elevation?` · ${o.elevation}m`:''):''}</text>")

# köy çeşmesi: palet + renk
rep('{"id":"Market_Plaza_Stamp","label":"Meydan / avlu","kind":"area","type":"plaza","w":20,"d":20}',
    '{"id":"Market_Plaza_Stamp","label":"Meydan / avlu","kind":"area","type":"plaza","w":20,"d":20},{"id":"Village_Fountain","label":"Köy çeşmesi","kind":"utility","type":"fountain","w":4,"d":4}')
rep("else if(o.kind==='utility'){fill='#91a4a2';edge='#506965'}", "else if(o.kind==='utility'){fill=o.type==='fountain'?'#7fc4cf':'#91a4a2';edge=o.type==='fountain'?'#2f7f8c':'#506965'}")

# --- istatistik ------------------------------------------------------------------
rep("$('stats').innerHTML=`<b>Yerleştirme özeti</b><div><span>56 öğelik listeden yerleşen</span><strong>${placedTarget} / ${target.length}</strong></div>",
    "const badN=[...connBad.keys()].filter(id=>TARGET_IDS.has(id)).length,lv={1:0,2:0,3:0};for(const o of objects)if(o.kind==='path'&&lv[o.lvl]!==undefined)lv[o.lvl]++;"
    "$('stats').innerHTML=`<b>Yerleştirme özeti</b><div><span>56 öğelik listeden yerleşen</span><strong>${placedTarget} / ${target.length}</strong></div>"
    "<div><span>Yol bağlantısı olmayan bina</span><strong class=\"${badN?'stat-bad':'stat-ok'}\">${badN} / ${target.length}</strong></div>"
    "<div><span>Ana yol / sokak / kapı patikası</span><strong>${lv[1]} / ${lv[2]} / ${lv[3]}</strong></div>")

# --- işaretçi olayları --------------------------------------------------------------
rep("if(drag.kind==='vertex'){o.pts[drag.index]=snap(p);render()}", "if(drag.kind==='vertex'){o.pts[drag.index]=snapDraw(p,o.uid);render()}")
rep("drag.last=p;render()}return}});",
    "drag.last=p;render()}return}if(['road','path','river','area'].includes(mode)||drawPts.length){const p=xyFromEvent(e);cursor=snap(p);const t=snapTarget(p);setHover(t?{...t}:null,cursor)}else if(hover){hover=null;drawOverlay()}});")
rep("board.addEventListener('pointerup',e=>{if(drag){const before=drag.before;const after=JSON.stringify({mapW,mapH,objects});if(before!==after){undoStack.push(before);if(undoStack.length>30)undoStack.shift()}drag=null;persist()}});",
    "board.addEventListener('pointerup',e=>{if(drag){const before=drag.before;const after=JSON.stringify({mapW,mapH,objects});const moved=before!==after;if(moved){undoStack.push(before);if(undoStack.length>30)undoStack.shift()}const d=drag;drag=null;"
    "if(moved&&d.kind==='item'&&isItem(d.obj)&&$('autoOnDrop').checked){const ok=refreshItem(d.obj,$('autoAlign').checked);setStatus(ok?'Kapı patikası yeniden örüldü':'Rota bulunamadı: kapı patikası silindi')}render();persist()}});")
rep("const p=snap(xyFromEvent(e));if(mode==='stamp'&&activeTemplate)",
    "const raw=xyFromEvent(e),p=['road','path','river','area'].includes(mode)?snapDraw(raw):snap(raw);if(mode==='stamp'&&activeTemplate)")

# --- SVG dışa aktarma: yer paylaşımı olmasın ---------------------------------------------
rep("const clone=board.cloneNode(true);", "const clone=board.cloneNode(true);clone.querySelector('#overlay')?.remove();")

# --- bilgi kutusu -------------------------------------------------------------------------
rep('<div class="warn"><b>56 öğe taslağı:</b> 54 önceki öğeye değirmen ve usta atölyesi eklendi. Konumlar referansa göre öneridir; hepsini sürükleyip değiştirebilirsin.</div>',
    '<div class="warn"><b>Yol ağı üretildi:</b> Ana yol (L1) → mahalle sokağı/halka (L2) → kapı önü patikası (L3). Her yapının kapısı <b>turuncu ok</b> ile gösterilir; ok yola bakar. Bir yapıyı sürüklersen kapı patikası bina içinden ve nehir üstünden geçmeden yeniden örülür (üstteki <b>Yolları Otomatik Ör / Yenile</b> tüm ağı yeniler). Yola 3 m’den uzak veya ana ağdan kopuk yapı <b style="color:#d11a2a">kırmızı çerçeve</b> alır.</div>'
    '<div class="warn"><b>Köprüler:</b> Batı–doğu geçişi yalnız Üst ve Alt köprüden olur; nehir kesin engeldir. Köprü boyları nehri iki yakada kıyıya oturacak şekilde uzatıldı (merkezler aynı).</div>')

open(dst, 'w', encoding='utf-8').write(t)
print('ok ->', dst, len(t), 'bayt')
