"""Phase 3 analyses for Reviewer 1.
  R1.4  hardware telemetry (latency, energy) â€” unit normalisation + reporting statistics
  R1.5  multimodal fusion vs unimodal â€” robustness evidence and lab-to-field decay
  R1.3  corpus table of all 263 included studies (CSV, XLSX, LaTeX longtable)
Run from this folder:  python -X utf8 analysis_phase3.py
Inputs: ../data/jsons_dedup (jsons_w_citekey minus 16 duplicate records). Outputs: figures/, tables/, numbers_phase3.json
"""
import matplotlib
matplotlib.use('Agg')
import os, json, glob, re
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
from scipy import stats

os.makedirs('figures', exist_ok=True); os.makedirs('tables', exist_ok=True)
sns.set_theme(style="whitegrid")
FS = 22
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": FS,
                     "axes.labelsize": FS, "xtick.labelsize": FS - 2, "ytick.labelsize": FS - 2,
                     "legend.fontsize": FS - 4, "figure.dpi": 100})
PAL = sns.color_palette("viridis", 5)
NUM = {}

def lbl(axes, y=-0.25):
    for i, ax in enumerate(axes):
        ax.text(0.5, y, f'({"abcd"[i]})', transform=ax.transAxes, ha='center', va='top', fontsize=FS + 2, fontweight='bold')
def save(n):
    plt.tight_layout(); plt.savefig(f'figures/{n}', dpi=400, bbox_inches='tight'); plt.close()
def f(v):
    if isinstance(v, list): v = v[0] if v else None
    if isinstance(v, dict): v = v.get('value')
    try: return float(v)
    except (TypeError, ValueError): return None

P = [json.load(open(p, encoding='utf-8')) for p in glob.glob('../data/jsons_dedup/*.json')]
P = sorted([p for p in P if p.get('relevance') == 'include'], key=lambda p: (str(p.get('year')), str(p.get('citekey'))))
N = len(P); NUM['N'] = N
pct = lambda k: round(k / N * 100, 1)

# ---------- shared per-paper fields (same definitions as phase2/analysis_revised.py) ----------
NOT_PAIRED = {'Camara_2023'}
def tier(p):
    g = p.get('real_world_gap') or {}
    a, b = f(g.get('lab_performance_value')), f(g.get('real_world_performance_value'))
    if p.get('citekey') not in NOT_PAIRED and a is not None and b is not None: return 'Paired'
    if g.get('environments_compared'): return 'Compared'
    if p.get('real_world_tested') or any((d or {}).get('collection_setting') == 'in-the-wild' for d in (p.get('data') or [])):
        return 'Field only'
    return 'Lab-only'
def repro(r):
    s = 2 * bool(r.get('code_available'))
    s += 2 if r.get('datasets_all_public') else (1 if r.get('datasets_any_public') else 0)
    return s + bool(r.get('benchmark_used'))

# ---------- R1.4 unit normalisation ----------
TIME_MS = {'ms': 1, 'milliseconds': 1, 's': 1000, 'sec': 1000, 'second': 1000, 'seconds': 1000,
           'minute': 60000, 'minutes': 60000, 'µs': 0.001}
POWER_MW = {'mW': 1, 'µW': 0.001, 'μW': 0.001}
ENERGY_MJ = {'mJ': 1, 'J': 1000, 'µJ': 0.001}
def energy_class(u):
    if u in POWER_MW: return 'Power (mW)'
    if u in ENERGY_MJ: return 'Energy per operation (mJ)'
    if re.search(r'mAh|mA|µA', u): return 'Current / charge'
    if re.search(r'%|percent', u, re.I): return 'Battery drain (%)'
    if re.search(r'hour|day', u, re.I) and not re.search(r'J', u): return 'Battery lifetime'
    return 'Other'

rows = []
for p in P:
    u = p.get('usability') or {}
    lat = [f(x) * TIME_MS[str(x.get('unit')).strip()] for x in (u.get('latency') or [])
           if isinstance(x, dict) and f(x) is not None and str(x.get('unit')).strip() in TIME_MS]
    lat_other = any(isinstance(x, dict) and f(x) is not None and str(x.get('unit')).strip() not in TIME_MS
                    for x in (u.get('latency') or []))
    en = [(str(x.get('unit')).strip(), f(x)) for x in (u.get('energy_consumption') or [])
          if isinstance(x, dict) and f(x) is not None]
    fu = p.get('fusion') or {}
    g = p.get('real_world_gap') or {}
    a, b = f(g.get('lab_performance_value')), f(g.get('real_world_performance_value'))
    tr = tier(p)
    perf = p.get('performance_analysis') or {}
    temp = p.get('temporal_robustness') or {}
    eer = next((f(e.get('value')) for e in (p.get('evaluation') or []) if str(e.get('metric')).upper() == 'EER' and f(e.get('value')) is not None), None)  # first non-null EER, as reported (%)
    subs = sum(f(d.get('num_subjects')) or 0 for d in (p.get('data') or []))
    bio = p.get('biometric') or {}
    rows.append(dict(
        citekey=p.get('citekey'), doi=p.get('doi'), venue=p.get('venue'), year=pd.to_numeric(p.get('year'), errors='coerce'),
        title=p.get('title'), biometric_type=str(bio.get('type')),
        modality='; '.join(m for m in (bio.get('modality') or []) if m),
        device='; '.join(d for d in (bio.get('device') or []) if d),
        subjects=subs if subs > 0 else None, eer=eer,
        learning=(p.get('method') or {}).get('learning_type') or 'Not reported',
        multimodal=bool(fu.get('is_multimodal')), fusion_level=(fu.get('fusion_level') or 'none') if fu.get('is_multimodal') else 'unimodal',
        tier=tr, lab=a if tr == 'Paired' else None, field=b if tr == 'Paired' else None,
        motion=bool((perf.get('robust_to_motion') or {}).get('is_quantified')),
        noise=bool((perf.get('robust_to_noise') or {}).get('is_quantified')),
        cross_session=bool(temp.get('cross_session_tested')),
        spoofing=bool((p.get('security') or {}).get('spoofing_tested')),
        repro=repro(p.get('reproducibility') or {}),
        latency_ms=float(np.median(lat)) if lat else None, latency_nontime=lat_other and not lat,
        energy_units=sorted({energy_class(u_) for u_, _ in en}),
        power_mw=float(np.median([v * POWER_MW[u_] for u_, v in en if u_ in POWER_MW])) if any(u_ in POWER_MW for u_, _ in en) else None,
        energy_mj=float(np.median([v * ENERGY_MJ[u_] for u_, v in en if u_ in ENERGY_MJ])) if any(u_ in ENERGY_MJ for u_, _ in en) else None))
df = pd.DataFrame(rows)

# ======================= R1.4 TELEMETRY =======================
lat = df['latency_ms'].dropna(); pw = df['power_mw'].dropna(); ej = df['energy_mj'].dropna()
any_lat = df['latency_ms'].notna() | df['latency_nontime']
any_en = df['energy_units'].apply(bool)
NUM['telemetry'] = dict(
    latency_any=[int(any_lat.sum()), pct(any_lat.sum())],
    latency_time_units=dict(n=len(lat), median_ms=round(lat.median(), 1), q1=round(lat.quantile(.25), 1),
                            q3=round(lat.quantile(.75), 1), min=round(lat.min(), 3), max=round(lat.max(), 1),
                            under_500ms=int((lat <= 500).sum()), over_1s=int((lat > 1000).sum())),
    energy_any=[int(any_en.sum()), pct(any_en.sum())],
    energy_unit_classes={k: int(v) for k, v in pd.Series([c for L in df['energy_units'] for c in L]).value_counts().items()},
    power_mw=dict(n=len(pw), median=round(pw.median(), 2) if len(pw) else None, min=round(pw.min(), 3) if len(pw) else None, max=round(pw.max(), 1) if len(pw) else None),
    energy_mj=dict(n=len(ej), median=round(ej.median(), 2) if len(ej) else None),
    both=[int((any_lat & any_en).sum()), pct((any_lat & any_en).sum())],
    neither=[int((~any_lat & ~any_en).sum()), pct((~any_lat & ~any_en).sum())],
    memory_note='memory/RAM was not a field of the extraction schema; not analysed')
NUM['telemetry']['latency_by_type'] = {k: dict(n=int(len(v)), median_ms=round(v.median(), 1))
                                       for k, v in df.dropna(subset=['latency_ms']).groupby('biometric_type')['latency_ms']}
NUM['telemetry']['latency_by_learning'] = {k: dict(n=int(len(v)), median_ms=round(v.median(), 1))
                                           for k, v in df.dropna(subset=['latency_ms']).groupby('learning')['latency_ms'] if len(v) >= 3}

dy = df.dropna(subset=['year']).copy(); dy['year'] = dy['year'].astype(int)
dy['Latency'] = any_lat[dy.index]; dy['Energy'] = any_en[dy.index]
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
yr = dy.groupby('year')[['Latency', 'Energy']].mean() * 100
for c, col, m in zip(['Latency', 'Energy'], [PAL[0], PAL[3]], ['o', 's']):
    sns.lineplot(x=yr.index.astype(str), y=yr[c], marker=m, markersize=10, linewidth=3, color=col, label=f'{c} reported', ax=axes[0])
axes[0].set_ylim(0, 100); axes[0].set_xlabel('Year'); axes[0].set_ylabel('% of Annual Papers'); axes[0].tick_params(axis='x', rotation=45)
axes[0].legend(loc='upper left', title='')
ld = df.dropna(subset=['latency_ms'])
order = ['behavioral', 'physiological', 'hybrid']
sns.boxplot(data=ld, x='biometric_type', y='latency_ms', order=order, ax=axes[1], palette='viridis', hue='biometric_type', legend=False)
sns.stripplot(data=ld, x='biometric_type', y='latency_ms', order=order, ax=axes[1], color='black', size=4, alpha=0.5)
axes[1].set_yscale('log'); axes[1].set_xlabel('Biometric Category'); axes[1].set_ylabel('Reported Latency (ms, log)')
axes[1].axhline(500, ls='--', color='red', alpha=0.5)
axes[1].set_xticks(range(3)); axes[1].set_xticklabels(['Behav.', 'Physiol.', 'Hybrid'])
ec = pd.Series([c for L in df['energy_units'] for c in L]).value_counts()
sns.barplot(x=ec.values, y=[s.replace(' (', '\n(') for s in ec.index], ax=axes[2], palette='viridis', hue=ec.index, legend=False)
axes[2].set_xlabel('Number of Papers'); axes[2].set_ylabel(''); axes[2].tick_params(axis='y', labelsize=16)
lbl(axes, -0.32)
save('R14_Telemetry.png')

# ======================= R1.5 FUSION =======================
df['group'] = np.where(df['multimodal'], 'Multimodal', 'Unimodal')
grp = df.groupby('group')
ev = pd.DataFrame({
    'Any field evidence': grp['tier'].apply(lambda s: (s != 'Lab-only').mean() * 100),
    'Lab vs. field compared': grp['tier'].apply(lambda s: s.isin(['Compared', 'Paired']).mean() * 100),
    'Motion robustness': grp['motion'].mean() * 100,
    'Noise robustness': grp['noise'].mean() * 100,
    'Cross-session': grp['cross_session'].mean() * 100,
    'Spoofing tested': grp['spoofing'].mean() * 100})
NUM['fusion'] = dict(counts={k: int(v) for k, v in df['group'].value_counts().items()},
                     fusion_level={k: int(v) for k, v in df[df.multimodal]['fusion_level'].value_counts().items()},
                     evidence_pct=ev.round(1).to_dict(orient='index'))
# chi-square tests multimodal vs unimodal
tests = {}
for col, ser in [('field', df['tier'] != 'Lab-only'), ('motion', df['motion']), ('noise', df['noise']),
                 ('cross_session', df['cross_session']), ('spoofing', df['spoofing'])]:
    ct = pd.crosstab(df['multimodal'], ser)
    chi2, pv, _, _ = stats.chi2_contingency(ct)
    tests[col] = dict(chi2=round(chi2, 2), p=round(pv, 3))
NUM['fusion']['chi2_multi_vs_uni'] = tests
e = df.dropna(subset=['eer'])
e = e.assign(eer_pct=e['eer'])  # REV: EER as reported (%), same definition as phase2
e = e[(e.eer_pct > 0) & (e.eer_pct <= 20)]
u = stats.mannwhitneyu(e[e.multimodal]['eer_pct'], e[~e.multimodal]['eer_pct'])
NUM['fusion']['lab_eer'] = dict(multi=dict(n=int(e.multimodal.sum()), median=round(e[e.multimodal]['eer_pct'].median(), 2)),
                                uni=dict(n=int((~e.multimodal).sum()), median=round(e[~e.multimodal]['eer_pct'].median(), 2)),
                                mannwhitney_p=round(u.pvalue, 3))
pr = df[df.tier == 'Paired'].copy()
pr['kind'] = np.where(pr[['lab', 'field']].max(axis=1) <= 20, 'Error rate', 'Accuracy-type')
pr['degraded'] = np.where(pr.kind == 'Error rate', pr.field > pr.lab, pr.field < pr.lab)
pr['rel_change'] = np.where(pr.kind == 'Error rate', (pr.field - pr.lab) / pr.lab.replace(0, np.nan),
                            (pr.lab - pr.field) / pr.lab) * 100   # % degradation, positive = worse
NUM['fusion']['paired'] = {g: dict(n=int(len(s)), degraded=int(s.degraded.sum()),
                                   err_pairs=int((s.kind == 'Error rate').sum()),
                                   err_ratio_median=round((s[s.kind == 'Error rate'].field / s[s.kind == 'Error rate'].lab.replace(0, np.nan)).median(), 2),
                                   acc_drop_median_pts=round((s[s.kind == 'Accuracy-type'].lab - s[s.kind == 'Accuracy-type'].field).median(), 2) if (s.kind == 'Accuracy-type').any() else None)
                           for g, s in pr.groupby('group')}
NUM['fusion']['paired_by_level'] = {g: dict(n=int(len(s)), degraded=int(s.degraded.sum()))
                                    for g, s in pr.groupby('fusion_level')}
NUM['fusion']['paired_list'] = pr[['citekey', 'group', 'fusion_level', 'kind', 'lab', 'field']].values.tolist()

fig, axes = plt.subplots(1, 2, figsize=(18, 6.5), gridspec_kw=dict(width_ratios=[1.5, 1]))
evl = ev.T.reset_index().melt(id_vars='index', var_name='Group', value_name='pct')
sns.barplot(data=evl, y='index', x='pct', hue='Group', ax=axes[0], palette=[PAL[1], PAL[3]], hue_order=['Unimodal', 'Multimodal'])
axes[0].set_xlabel('% of Papers'); axes[0].set_ylabel(''); axes[0].set_xlim(0, 100)
axes[0].legend(title='', loc='lower right')
er = pr[pr.kind == 'Error rate'].copy(); er['ratio'] = er.field / er.lab.replace(0, np.nan)
er = er.dropna(subset=['ratio'])
lvl_order = ['unimodal', 'feature', 'score', 'decision']
er['level'] = pd.Categorical(er.fusion_level, [l for l in lvl_order if l in set(er.fusion_level)])
sns.stripplot(data=er, x='level', y='ratio', ax=axes[1], size=14, palette='viridis', hue='level', legend=False, jitter=0.1)
axes[1].axhline(1, ls='--', color='black', alpha=0.5)
axes[1].set_yscale('log'); axes[1].set_xlabel('Fusion Level'); axes[1].set_ylabel('Field / Lab Error Rate (log)')
axes[1].set_xticks(range(len(er.level.cat.categories)))
axes[1].set_xticklabels([f'{c}\n(n={int((er.level == c).sum())})' for c in er.level.cat.categories])
lbl(axes, -0.34)
save('R15_Fusion.png')

# ======================= R1.3 CORPUS TABLE =======================
tab = df[['citekey', 'year', 'title', 'venue', 'doi', 'biometric_type', 'modality', 'device', 'subjects', 'learning',
          'fusion_level', 'tier', 'lab', 'field', 'eer', 'repro', 'latency_ms', 'power_mw']].copy()
tab['year'] = tab['year'].astype('Int64')
tab = tab.sort_values(['year', 'citekey'], na_position='last').reset_index(drop=True)
tab.index += 1
tab.to_csv('tables/S1_corpus_263.csv', index_label='No')
tab.to_excel('tables/S1_corpus_263.xlsx', index_label='No') if __import__('importlib').util.find_spec('openpyxl') else None

def tex(s):
    return re.sub(r'([&%#_$])', r'\\\1', str(s)) if s is not None else ''
def short(s, n):
    s = str(s or '').strip(); return s if len(s) <= n else s[:n - 1] + '.'
TIER_S = {'Lab-only': 'L', 'Field only': 'F', 'Compared': 'C', 'Paired': 'P'}
FU_S = {'unimodal': 'U', 'feature': 'Fe', 'score': 'Sc', 'decision': 'De', 'hybrid': 'Hy', 'none': 'M'}
lines = []
for i, r in tab.iterrows():
    val = lambda v, d=2: '--' if v is None or (isinstance(v, float) and np.isnan(v)) else (lambda s: s.rstrip('0').rstrip('.') if '.' in s else s)(f'{v:.{d}f}')  # REV: never strip zeros of integers
    lines.append(' & '.join([str(i), tex(str(r.citekey).replace('_', ' ')), str(r.year) if pd.notna(r.year) else '--',
                             {'behavioral': 'B', 'physiological': 'P', 'hybrid': 'H'}.get(r.biometric_type, '--'),
                             tex(short(r.modality, 32)), val(r.subjects, 0),
                             {'supervised': 'Sup', 'unsupervised': 'Uns', 'few-shot': 'FS', 'transfer': 'TL',
                              'self-supervised': 'SSL', 'semi-supervised': 'Semi'}.get(r.learning, 'NR'),
                             FU_S.get(r.fusion_level, 'M'),
                             TIER_S[r.tier], val(r.eer, 3), str(r.repro)]) + r' \\')
open('tables/S1_corpus_rows.tex', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
NUM['corpus_table_rows'] = len(tab)
json.dump(NUM, open('numbers_phase3.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in NUM.items() if k != 'fusion'} | {'fusion': {k: v for k, v in NUM['fusion'].items() if k != 'paired_list'}},
                 indent=1, ensure_ascii=False, default=str))

