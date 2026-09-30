"""Inlines css + engine + data + ui into ONE standalone html: prototype/dist/colorbuild.html"""
import os
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, '..', 'src'); D = os.path.join(H, '..', 'dist')
os.makedirs(D, exist_ok=True)
rd = lambda n: open(os.path.join(S, n), encoding='utf-8').read()
html = rd('template.html')
for key, fn in [('CSS', 'style.css'), ('ENGINE', 'engine.js'), ('LEVELS', 'levels_data.js'), ('VECTORS', 'vectors_data.js'), ('UI', 'ui.js')]:
    html = html.replace(f'/*__{key}__*/', rd(fn).replace('</script>', '<\\/script>'))
out = os.path.join(D, 'colorbuild.html')
open(out, 'w', encoding='utf-8').write(html)
print('yazıldı:', out, round(os.path.getsize(out) / 1024), 'KB')
