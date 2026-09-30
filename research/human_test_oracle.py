"""Post-hoc oracle for human test sessions.

Replays a player's colour choices on a level and labels every move with solver ground truth:
  safe    the move keeps the level winnable
  latent  the move made the level unwinnable but nothing is unreachable yet (hidden doom)
  sealed  the move left some unfilled cell unreachable (geometrically visible failure)
plus the colours that WERE safe at that state, the wave size actually placed, progress, and - for a first
mistake - how many further moves the player actually made before the seal appeared (observed horizon).

session token list: colour letters ('A','B','C') and 'U' = undo last wave.

usage:  python3 human_test_oracle.py human_test/levels.json L_ID  A B A C ...
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puzzle_engine import Level


class Oracle:
    def __init__(self, grid: str, W: int):
        self.L = Level(grid, W)
        self._nwin = {}

    def nwin(self, s):
        r = self._nwin.get(s)
        if r is not None:
            return r
        L = self.L
        if s == L.full:
            r = 1
        else:
            sealed, mv = L.info(s)
            r = 0 if sealed else sum(self.nwin(t) for _, t in mv)
        self._nwin[s] = r
        return r

    def safe_colors(self, s):
        return [self.L.letters[k] for k, t in self.L.info(s)[1] if self.nwin(t) > 0]

    def legal_colors(self, s):
        return [self.L.letters[k] for k, _ in self.L.info(s)[1]]

    def annotate(self, tokens):
        L = self.L
        s = 0
        hist = []          # stack of previous states
        rows = []
        first_mistake = None
        for i, tok in enumerate(tokens):
            if tok.upper() == 'U':
                if hist:
                    s = hist.pop()
                rows.append(dict(step=i, token='U', label='undo', progress=bin(s).count('1') / L.n))
                continue
            sealed, mv = L.info(s)
            nxt = dict((L.letters[k], t) for k, t in mv).get(tok)
            if nxt is None:
                rows.append(dict(step=i, token=tok, label='illegal', legal=self.legal_colors(s)))
                continue
            safe_before = self.safe_colors(s)
            win = self.nwin(nxt) > 0
            sealed_after = L.info(nxt)[0]
            label = 'safe' if win else ('sealed' if sealed_after else 'latent')
            placed = bin(nxt).count('1') - bin(s).count('1')
            row = dict(step=i, token=tok, label=label, safe_before=safe_before, legal_before=self.legal_colors(s),
                       unsafe_when_safe_existed=(not win and len(safe_before) > 0), placed=placed,
                       progress=bin(nxt).count('1') / L.n)
            if not win and first_mistake is None:
                first_mistake = i
                row['first_mistake'] = True
            rows.append(row)
            hist.append(s)
            s = nxt
        summary = dict(moves=sum(1 for r in rows if r['label'] in ('safe', 'latent', 'sealed')), finished=(s == L.full),
                       first_mistake_step=first_mistake, final_label=('won' if s == L.full else ('sealed' if L.info(s)[0] else 'open')))
        if first_mistake is not None:
            seal_step = next((r['step'] for r in rows if r['step'] >= first_mistake and r.get('label') == 'sealed'), None)
            summary['observed_horizon_moves'] = None if seal_step is None else sum(
                1 for r in rows if first_mistake <= r['step'] <= seal_step and r['label'] in ('safe', 'latent', 'sealed'))
            summary['moves_made_while_doomed_before_seal'] = None if seal_step is None else summary['observed_horizon_moves'] - 1
        return rows, summary


def main():
    path, lid, toks = sys.argv[1], sys.argv[2], sys.argv[3:]
    data = json.load(open(path))
    lv = next(l for l in data['levels'] if l['id'] == lid)
    rows, summ = Oracle(lv['grid'], lv['W']).annotate(toks)
    for r in rows:
        print(r)
    print(summ)


if __name__ == '__main__':
    main()
