"""css + engine + level + vectors + ui → TEK dosya dist/block-image-01.html  (python3 tools/build.py l01 → dist/block-image-L01.html)"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, '..', 'src'); D = os.path.join(H, '..', 'dist'); os.makedirs(D, exist_ok=True)
rd = lambda n: open(os.path.join(S, n), encoding='utf-8').read(); html = rd('template.html')
suf = ('_' + sys.argv[1].lower()) if len(sys.argv) > 1 else ''
for key, fn in [('CSS', 'style.css'), ('ENGINE', 'engine.js'), ('LEVEL', 'level%s.js' % suf), ('VECTORS', 'vectors%s.js' % suf), ('UI', 'ui.js')]: html = html.replace(f'/*__{key}__*/', rd(fn).replace('</script>', '<\\/script>'))
out = os.path.join(D, 'block-image-%s.html' % sys.argv[1].upper() if len(sys.argv) > 1 else 'block-image-01.html'); open(out, 'w', encoding='utf-8').write(html); print('yazıldı:', out, round(os.path.getsize(out) / 1024), 'KB')
