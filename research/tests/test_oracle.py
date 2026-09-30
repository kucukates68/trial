"""Oracle sanity: a winning sequence is all 'safe'; a mistake is labelled latent/sealed and never 'safe'."""
import json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from human_test_oracle import Oracle

HT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'human_test', 'levels.json')


def main():
    data = json.load(open(HT))
    rng = random.Random(0)
    n_mistake_levels = 0
    for lv in data['levels']:
        o = Oracle(lv['grid'], lv['W'])
        rows, summ = o.annotate(lv['example_winning_sequence'])
        assert summ['finished'] and all(r['label'] == 'safe' for r in rows), lv['id']
        # first move safety list matches the stored one
        assert sorted(o.safe_colors(0)) == sorted(lv['safe_first_colors']), lv['id']
        # force one mistake
        s = 0; seq = []
        for step in range(40):
            sealed, mv = o.L.info(s)
            if sealed or not mv or s == o.L.full:
                break
            bad = [(o.L.letters[k], t) for k, t in mv if o.nwin(t) == 0]
            if bad and step >= 1:
                seq.append(bad[0][0]); s = bad[0][1]; break
            c, t = rng.choice([(o.L.letters[k], t) for k, t in mv if o.nwin(t) > 0]); seq.append(c); s = t
        rows, summ = o.annotate(seq)
        if summ['first_mistake_step'] is not None:
            n_mistake_levels += 1
            assert rows[summ['first_mistake_step']]['label'] in ('latent', 'sealed'), lv['id']
    print('levels checked', len(data['levels']), '| levels where a mistake could be forced', n_mistake_levels)


if __name__ == '__main__':
    main()
