import templates as T
CANDS = {}
LB1 = {'A': 'Kapı A', 'B': 'Kapı B', 'C': 'Kapı C', 'D': 'Kapı D', '1': 'Oda 1', '2': 'Oda 2', '3': 'Oda 3', 'p': 'Tepe 1', 'q': 'Tepe 2', 'r': 'Tepe 3'}
LB2 = {'A': 'Kapı A', 'B': 'Kapı B', 'C': 'Kapı C', '1': 'Oda 1', '2': 'Oda 2', 'p': 'Tepe 1', 'q': 'Tepe 2', 'l': 'Sol sütun', 'r': 'Sağ sütun', 'u': 'Üst bar'}
LB3 = {'L': 'Sol alt', 'l': 'Sol orta', 'k': 'Sol üst', 'R': 'Sağ alt', 'r': 'Sağ orta', 'K': 'Sağ üst', 'X': 'Köprü', 'D': 'Tepe'}
LB4 = {'v': 'Üst çubuk', 'a': 'Sol üst', 'b': 'Sol alt', 'c': 'Sağ üst', 'd': 'Sağ alt', 'm': 'Merkez üst', 'n': 'Merkez alt'}
LB5 = {'A': 'Kapı A', 'B': 'Kapı B', 'C': 'Kapı C', '1': 'Oda 1', '2': 'Oda 2'}
def hexmap(names, base):
    return {n: base[n] for n in names}
G = dict(A='#e8833a', B='#d9a441', C='#c4572e', D='#b8793a')
# X01: dört kapı, üç oda, üç tepe (T3)
x01c = dict(A='#e8833a', B='#d9a441', C='#c4572e', D='#a8693a', **{'1': '#4f8fd6', '2': '#3aa6a6', '3': '#6a74d6'}, p='#a9ccf0', q='#a4ddd8', r='#bcc2f2')
CANDS['x01'] = ('X01 · Üç oda', T.T3, [['B', 'q', '2', 'p'], ['C', '1', 'A'], ['D', 'r', '3']], x01c, 'dört kapı, üç ortak oda, üç tepe', LB1)
# X02: Taç (C2)
x02c = dict(A='#e8833a', B='#d9a441', C='#c4572e', **{'1': '#4f8fd6', '2': '#3aa6a6'}, p='#a9ccf0', q='#a4ddd8', l='#5aa469', r='#7bbf6a', u='#b6dd8f')
CANDS['x02'] = ('X02 · Taç', T.C2, [['u', 'r', 'l', 'A'], ['C', 'p', '1'], ['B', 'q', '2']], x02c, 'U şekilli oda iki kapıya bağlı', LB2)
# X03: Köprü (C4b)
x03c = dict(L='#e8833a', l='#d9a441', k='#e6c14a', R='#c4572e', r='#b8793a', K='#d66aa6', X='#8a5fd0', D='#4f8fd6')
CANDS['x03'] = ('X03 · Köprü', T.C4b, [['K', 'r', 'R'], ['k', 'D', 'X'], ['l', 'L']], x03c, 'iki sütun + köprü', LB3)
# X04: Halka (C3)
x04c = dict(v='#4f8fd6', a='#e8833a', b='#d9a441', c='#c4572e', d='#b8793a', m='#5aa469', n='#8fcf8a')
CANDS['x04'] = ('X04 · Halka', T.C3, [['v', 'd', 'n'], ['c', 'm'], ['a', 'b']], x04c, 'iki yol, merkez cep', LB4)
# X05: Üç kapı (C1s) mini
x05c = dict(A='#e8833a', B='#d9a441', C='#c4572e', **{'1': '#4f8fd6', '2': '#3aa6a6'})
CANDS['x05'] = ('X05 · Üç kapı', T.C1s, [['A', '1'], ['C', '2'], ['B']], x05c, 'mini', LB5)
