#!/usr/bin/env bash
# Orijinal atölye dosyasından: (1) editör özelliklerini ekle, (2) yol ağını üretip DEFAULT_OBJECTS'e göm.
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/patch_html_editor.py input/koy-vaziyet-atolyesi.orig.html /tmp/_stage.html tools/editor_block.js
python3 village_network_generator.py --html input/koy-vaziyet-atolyesi.orig.html \
    --inject-from /tmp/_stage.html --inject-html koy-vaziyet-atolyesi.html \
    --out-json koy-yerlesim-koordinatlari.json --preview onizleme.svg
