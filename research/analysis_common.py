"""Shared helpers for the analysis scripts."""
from __future__ import annotations
import os, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
SUM = os.path.join(RES, 'summary')
os.makedirs(SUM, exist_ok=True)


def _read(name):
    p = os.path.join(RES, f'{name}.jsonl')
    if os.path.exists(p):
        return pd.read_json(p, lines=True)
    return pd.read_csv(os.path.join(RES, f'{name}.csv.gz'), low_memory=False)


def load(name, solvable=True):
    df = _read(name)
    if 'error' in df:
        df = df[df['error'].isna()]
    df = df[df['solv'].notna()].copy()
    df['solv'] = df['solv'].astype(bool)
    if solvable:
        df = df[df['solv']].copy()
    if 'greedy_deep' in df:
        df['greedy_fail'] = (~df['greedy_deep'].fillna(True).astype(bool)).astype(float)
    return df


def save(df, name):
    df.to_csv(os.path.join(SUM, name + '.csv'))


def anova_eta(df, resp, factors, inter=True, typ=2):
    """eta^2 (share of total SS) and partial eta^2 of every term; unbalanced-safe (type II)."""
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    terms = ' + '.join(f'C({f})' for f in factors)
    formula = f'{resp} ~ ({terms})**2' if inter else f'{resp} ~ {terms}'
    m = smf.ols(formula, data=df).fit()
    a = sm.stats.anova_lm(m, typ=typ)
    tot = ((df[resp] - df[resp].mean()) ** 2).sum()
    out = pd.DataFrame({'ss': a['sum_sq'], 'df': a['df']})
    out['eta2'] = out['ss'] / tot
    resid = out.loc['Residual', 'ss']
    out['partial_eta2'] = out['ss'] / (out['ss'] + resid)
    out.loc['Residual', 'partial_eta2'] = np.nan
    out.index = [i.replace('C(', '').replace(')', '') for i in out.index]
    return out, m.rsquared


def shannon(counts):
    c = np.asarray([x for x in counts if x > 0], float)
    p = c / c.sum()
    return float(-(p * np.log2(p)).sum())


def chao1(counts):
    c = np.asarray(counts)
    s = (c > 0).sum()
    f1 = (c == 1).sum()
    f2 = (c == 2).sum()
    if f2 > 0:
        return s + f1 * f1 / (2 * f2)
    return s + f1 * (f1 - 1) / 2
