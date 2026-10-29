#!/usr/bin/env bash
# 2B son sürüm: v6 dosyalarına dokunmadan 2d-final/ altına yeni çıktılar üretir.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p 2d-final
python3 tools/patch_html_editor.py input/koy-vaziyet-atolyesi.orig.html /tmp/_stage2.html tools/editor_block.js
# yalnız 2B-son sürüme özel yama: seçili alanın işlevi (purpose) denetçi panelinde görünür
python3 - <<'PY'
p='/tmp/_stage2.html'; t=open(p,encoding='utf-8').read()
old="<p>${o.pts?'Noktaları tek tek sürükleyerek çizgiyi/alanı biçimlendir.':"
assert t.count(old)==1
t=t.replace(old,"${o.purpose?`<p><b>İşlev:</b> ${esc(o.purpose)}</p>`:''}"+old)
open(p,'w',encoding='utf-8').write(t)
PY
python3 village_network_generator_2dfinal.py --html input/koy-vaziyet-atolyesi.orig.html \
    --inject-from /tmp/_stage2.html --inject-html 2d-final/koy-vaziyet-atolyesi_2d-final.html \
    --out-json 2d-final/koy-yerlesim_2d-final.json --preview 2d-final/onizleme_2d-final.svg
