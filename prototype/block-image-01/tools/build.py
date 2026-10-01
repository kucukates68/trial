"""css + engine + level + vectors + ui → TEK dosya dist/block-image-01.html"""
import os
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, '..', 'src'); D = os.path.join(H, '..', 'dist'); os.makedirs(D, exist_ok=True)
rd = lambda n: open(os.path.join(S, n), encoding='utf-8').read(); html = rd('template.html')
for key, fn in [('CSS', 'style.css'), ('ENGINE', 'engine.js'), ('LEVEL', 'level.js'), ('VECTORS', 'vectors.js'), ('UI', 'ui.js')]: html = html.replace(f'/*__{key}__*/', rd(fn).replace('</script>', '<\\/script>'))
out = os.path.join(D, 'block-image-01.html'); open(out, 'w', encoding='utf-8').write(html); print('yazıldı:', out, round(os.path.getsize(out) / 1024), 'KB')
