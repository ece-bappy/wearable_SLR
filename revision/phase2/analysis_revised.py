"""Revised analysis (Phase 2). Based verbatim on analysis.ipynb; every change is marked `# REV:`.

REV summary
  R1.1  single denominator N=263 (after de-duplication); mutually exclusive real-world evidence tiers (Fig 6).
  R1.2  Fig 10 axis labels ("None" -> "Attack Type", "year" -> "Year");
        Fig 4(b) null learning type shown as "Not reported", overlapping labels fixed.
  Per-year panels necessarily use the 276 papers with a known year (stated in captions).
Run from this folder:  $env:PYTHONUTF8='1'; python analysis_revised.py
Outputs: figures/*.png, numbers.json
"""
import matplotlib
matplotlib.use('Agg')
import os, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from matplotlib.patches import Ellipse
from matplotlib.ticker import ScalarFormatter

OUT = 'figures'                                   # REV: separate output folder
os.makedirs(OUT, exist_ok=True)
NUMBERS = {}                                      # REV: every number quoted in the text

# --- GLOBAL JOURNAL STYLING (unchanged) ---
plt.close('all')
sns.set_theme(style="whitegrid")
GLOBAL_FONT_SIZE = 22
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman"],
    "font.size": GLOBAL_FONT_SIZE, "axes.titlesize": GLOBAL_FONT_SIZE + 2,
    "axes.labelsize": GLOBAL_FONT_SIZE, "xtick.labelsize": GLOBAL_FONT_SIZE - 2,
    "ytick.labelsize": GLOBAL_FONT_SIZE - 2, "legend.fontsize": GLOBAL_FONT_SIZE - 2,
    "figure.dpi": 100, "axes.titleweight": "bold"})   # REV: layout dpi only (Windows MemoryError); savefig stays 400
GLOBAL_PALETTE = "viridis"
PAL_VIRIDIS = sns.color_palette("viridis", 5)
PAL_MAGMA = sns.color_palette("magma", 5)
FIG_SIZE = (16, 6)
LEG = dict(title="", handlelength=0.8, handleheight=0.6, labelspacing=0.2, borderpad=0.2, handletextpad=0.3)

def add_subplot_labels(axes, y_offset=-0.25):
    axes = [axes] if not isinstance(axes, (list, np.ndarray)) else np.array(axes).flatten()
    if len(axes) > 1:
        for idx, ax in enumerate(axes):
            ax.text(0.5, y_offset, '(abcd'[idx + 1].join('()'), transform=ax.transAxes,
                    ha='center', va='top', fontsize=GLOBAL_FONT_SIZE + 2, fontweight='bold')

def save(name):
    plt.tight_layout(); plt.savefig(os.path.join(OUT, name), dpi=400, bbox_inches='tight'); plt.close()

# --- 1. LOAD DATA ---
json_folder = '../data/jsons_dedup'               # REV: jsons_w_citekey minus 16 duplicate records (see ../data/removed_duplicates.txt)
data_list = []
for filename in sorted(os.listdir(json_folder)):
    if filename.endswith('.json'):
        with open(os.path.join(json_folder, filename), 'r', encoding='utf-8') as f:
            content = json.load(f)
            if content.get('relevance') == 'include':
                data_list.append(content)
print(f"Successfully loaded {len(data_list)} relevant papers.")

def to_float_safe(val):
    if val is None: return None
    if isinstance(val, list): val = val[0] if len(val) > 0 else None
    if isinstance(val, dict): val = val.get('value', val.get('eer', val.get('result')))
    try: return float(val)
    except (ValueError, TypeError): return None

def compute_repro_score(repr_info):
    score = 0
    if repr_info.get('code_available'): score += 2
    if repr_info.get('datasets_all_public'): score += 2
    elif repr_info.get('datasets_any_public'): score += 1
    if repr_info.get('benchmark_used'): score += 1
    return score

normalization_map = {
    'ECG': 'ECG', 'PPG': 'PPG', 'Accelerometer': 'Accelerometer', 'Gyroscope': 'Gyroscope',
    'IMU': 'IMU', 'motion': 'Motion', 'EDA': 'EDA/GSR', 'EMG': 'EMG', 'EEG': 'EEG',
    'Voice': 'Voice/Acoustic', 'speech': 'Voice/Acoustic', 'acoustic': 'Voice/Acoustic',
    'Keystroke dynamics': 'Keystroke', 'typing': 'Keystroke', 'touch': 'Touch/Swipe',
    'Gesture': 'Gestures', 'gait': 'Gait', 'fingerprint': 'Physical Biometrics',
    'CNN': 'CNN', 'ResNet': 'ResNet', 'LSTM': 'LSTM', 'RNN': 'RNN', 'SVM': 'SVM',
    'Random Forest': 'Random Forest', 'Decision Tree': 'Decision Tree',
    'K-Nearest Neighbor': 'k-NN', 'DNN': 'DNN/MLP'}

def clean_labels(label_list):
    if not isinstance(label_list, list): return []
    return list(set([normalization_map.get(item.strip(), item.strip()) for item in label_list if item]))

# REV (R1.1): mutually exclusive, nested evidence tiers
TIERS = ['Lab-only', 'Field data, no comparison', 'Lab vs. field compared', 'Paired lab/field values']
# REV: manual PDF verification (PHASE2_NOTES.md). Camara_2023 values are FAR on two different
# datasets, not a lab-vs-field pair -> paired values discarded.
NOT_PAIRED = {'Camara_2023'}
def paired_values(p):
    gap = p.get('real_world_gap') or {}
    if p.get('citekey') in NOT_PAIRED: return None, None
    a, b = to_float_safe(gap.get('lab_performance_value')), to_float_safe(gap.get('real_world_performance_value'))
    return (a, b) if a is not None and b is not None else (None, None)
def evidence_tier(p):
    gap = p.get('real_world_gap') or {}
    paired = paired_values(p)[0] is not None
    compared = bool(gap.get('environments_compared'))
    wild = any((d or {}).get('collection_setting') == 'in-the-wild' for d in (p.get('data') or []))
    field = bool(p.get('real_world_tested')) or wild
    if paired: return TIERS[3]
    if compared: return TIERS[2]
    if field: return TIERS[1]
    return TIERS[0]

def first_eer_std(p):
    """REV: one EER per paper, identical in every analysis: the FIRST extracted non-null EER entry,
    taken AS REPORTED in percent. (The original <1 -> x100 rule was dropped: spot checks, e.g. Hwang_2021 = 0.77%,
    show sub-1 values are genuine percentages.)"""
    v = next((to_float_safe(e.get('value')) for e in (p.get('evaluation') or [])
              if str(e.get('metric')).upper() == 'EER' and to_float_safe(e.get('value')) is not None), None)
    if v is None: return None
    return v

rows = []
for p in data_list:
    eval_metrics = {m['metric'].upper(): m['value'] for m in p.get('evaluation', []) if m['value'] is not None}
    gap = p.get('real_world_gap') or {}
    temp = p.get('temporal_robustness') or {}
    perf = p.get('performance_analysis') or {}
    sec = p.get('security') or {}
    repr_info = p.get('reproducibility') or {}
    lt = p.get('method', {}).get('learning_type')
    rows.append({
        'title': p.get('title'), 'citekey': p.get('citekey'),
        'year': pd.to_numeric(p.get('year'), errors='coerce'),
        'biometric_type': str(p.get('biometric', {}).get('type')).strip(),
        'modalities': clean_labels(p.get('biometric', {}).get('modality', [])),
        'learning_type': str(lt).strip() if lt else 'Not reported',      # REV (R1.2): no "None" category
        'models': clean_labels(p.get('method', {}).get('model', [])),
        'eer': first_eer_std(p),                                          # REV: first EER entry, as reported (%)
        'rw_tested': bool(p.get('real_world_tested', False)),
        'tier': evidence_tier(p),                                         # REV (R1.1)
        'lab_eer': paired_values(p)[0],                                   # REV: verified pairs only
        'wild_eer': paired_values(p)[1],
        'Cross-Session': bool(temp.get('cross_session_tested')),
        'Motion Robustness': bool((perf.get('robust_to_motion') or {}).get('is_quantified')),
        'Noise Robustness': bool((perf.get('robust_to_noise') or {}).get('is_quantified')),
        'spoofing': bool(sec.get('spoofing_tested')),
        'liveness': bool(sec.get('liveness_detection')),
        'attacks': sec.get('attack_types') or [],
        'repro_raw': compute_repro_score(repr_info)})
df_all = pd.DataFrame(rows)                                               # REV: N=263 for all totals
N = len(df_all)
df = df_all.dropna(subset=['year']).copy()                                # per-year panels only
df['year'] = df['year'].astype(int)
NUMBERS.update(N=N, N_with_year=len(df))
pct = lambda k: round(k / N * 100, 2)

# ===================== RQ1 =====================
fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
order = ['behavioral', 'physiological', 'hybrid']
sns.countplot(data=df_all, x='biometric_type', order=order, ax=axes[0], palette=GLOBAL_PALETTE, hue='biometric_type', legend=False)
axes[0].set_xlabel("Biometric Category"); axes[0].set_ylabel("Number of Papers")
eer_df = df_all[df_all['eer'].notnull()].copy()
lt_order = eer_df['learning_type'].value_counts().index.tolist()
lt_order = [l for l in lt_order if l != 'Not reported'] + (['Not reported'] if 'Not reported' in lt_order else [])
sns.boxplot(data=eer_df, x='learning_type', y='eer', order=lt_order, ax=axes[1], palette=GLOBAL_PALETTE, hue='learning_type', legend=False)
axes[1].set_xlabel("Learning Type"); axes[1].set_ylabel("EER (%)")
axes[1].set_ylim(0, eer_df['eer'].quantile(0.95))
axes[1].set_xticks(range(len(lt_order)))                                  # REV (R1.2): no overlap
LT_LBL = {'supervised': 'Super-\nvised', 'unsupervised': 'Unsuper-\nvised', 'self-supervised': 'Self-\nsupervised',
          'semi-supervised': 'Semi-\nsupervised', 'Not reported': 'Not\nreported', 'few-shot': 'Few-\nshot', 'transfer': 'Transfer'}
axes[1].set_xticklabels([LT_LBL.get(l, l) for l in lt_order], fontsize=15)
add_subplot_labels(axes, y_offset=-0.42)
save('RQ1_Fig1_Categories.png')
NUMBERS['biometric_type'] = {k: int(v) for k, v in df_all['biometric_type'].value_counts().items()}

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
mod_counts = df_all.explode('modalities')['modalities'].value_counts().head(10)
sns.barplot(x=mod_counts.values, y=mod_counts.index, ax=axes[0], palette=GLOBAL_PALETTE, hue=mod_counts.index, legend=False)
axes[0].set_xlabel("Number of Papers"); axes[0].set_ylabel("Modality")
model_counts = df_all.explode('models')['models'].value_counts().head(10)
sns.barplot(x=model_counts.values, y=model_counts.index, ax=axes[1], palette=GLOBAL_PALETTE, hue=model_counts.index, legend=False)
axes[1].set_xlabel("Number of Papers"); axes[1].set_ylabel("Model Architecture")
add_subplot_labels(axes)
save('RQ1_Fig2_TopTech.png')

df_score = df[df['year'].between(2017, 2026)].copy()
fig, axes = plt.subplots(1, 3, figsize=FIG_SIZE)
sns.histplot(df_all['repro_raw'], bins=6, kde=False, ax=axes[0], color=PAL_MAGMA[2])
axes[0].set_xlabel("Reproducibility Score"); axes[0].set_ylabel("Number of Papers")
sns.boxplot(data=df_score, x='year', y='repro_raw', palette=GLOBAL_PALETTE, hue='year', legend=False, ax=axes[1])
axes[1].set_xlabel("Year"); axes[1].set_ylabel("Score"); axes[1].tick_params(axis='x', rotation=45)
mean_scores = df_score.groupby('year')['repro_raw'].mean().reset_index()
sns.lineplot(data=mean_scores, color='black', x='year', y='repro_raw', marker='o', ax=axes[2], linewidth=3)
axes[2].set_xlabel("Year"); axes[2].set_ylabel("Mean Score"); axes[2].set_ylim(0, 5)
axes[2].set_xticks(mean_scores['year'].astype(int)); axes[2].tick_params(axis='x', rotation=45)
add_subplot_labels(axes, y_offset=-0.47)
save('RQ1_Fig_3_Score.png')

# ===================== RQ2 =====================
# REV (R1.1): Fig 6 now shows the four evidence tiers on N=263
TIER_COL = [PAL_VIRIDIS[0], PAL_VIRIDIS[1], PAL_VIRIDIS[3], PAL_VIRIDIS[4]]
fig, axes = plt.subplots(1, 3, figsize=(18, 6.5))
tc = df_all['tier'].value_counts().reindex(TIERS, fill_value=0)
NUMBERS['tiers'] = {t: [int(v), pct(v)] for t, v in tc.items()}
field_any = int(tc[TIERS[1:]].sum()); compared_any = int(tc[TIERS[2:]].sum())
NUMBERS['field_any'] = [field_any, pct(field_any)]
NUMBERS['compared_any'] = [compared_any, pct(compared_any)]
NUMBERS['rw_tested_flag'] = [int(df_all['rw_tested'].sum()), pct(df_all['rw_tested'].sum())]
wedges, _ = axes[0].pie(tc.values, colors=TIER_COL, startangle=90, counterclock=False,
                        wedgeprops=dict(edgecolor='white'))
axes[0].legend(wedges, [f'{t}: {v} ({v / N * 100:.1f}%)' for t, v in tc.items()], loc='upper center',
               bbox_to_anchor=(0.5, -0.02), frameon=False, fontsize=16, handlelength=0.8)

trend = pd.crosstab(df['year'], df['tier']).reindex(columns=TIERS, fill_value=0)
trend.plot(kind='bar', stacked=True, ax=axes[1], color=TIER_COL, alpha=0.9, legend=False)
axes[1].set_ylabel("Number of Papers"); axes[1].set_xlabel("Year"); axes[1].tick_params(axis='x', rotation=45)

share = pd.DataFrame({
    'Any field evidence': trend[TIERS[1:]].sum(axis=1) / trend.sum(axis=1) * 100,
    'Paired lab/field values': trend[TIERS[3]] / trend.sum(axis=1) * 100})
for (col, s), c, m in zip(share.items(), ['teal', PAL_VIRIDIS[4]], ['o', 's']):
    sns.lineplot(x=s.index.astype(str), y=s.values, marker=m, markersize=10, ax=axes[2], color=c, linewidth=3, label=col)
axes[2].set_ylabel("% of Annual Papers"); axes[2].set_xlabel("Year"); axes[2].set_ylim(0, 105)
axes[2].tick_params(axis='x', rotation=45); axes[2].legend(fontsize=16, loc='upper left', **LEG)
add_subplot_labels(axes, y_offset=-0.62)
save('RQ2_Fig1_Testing_Landscape.png')

# REV (R1.1): Fig 7 now separates error-rate pairs (lower is better) from accuracy-type pairs
# (accuracy/F1/BAC, higher is better; verified in PDFs). Nothing is silently dropped.
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
def categorize_pair(row):
    if pd.isnull(row['lab_eer']) or pd.isnull(row['wild_eer']): return 'No paired values'
    return 'Error rate' if max(row['lab_eer'], row['wild_eer']) <= 20 else 'Accuracy-type'
df_all['pair_type'] = df_all.apply(categorize_pair, axis=1)
avail = df_all['pair_type'].value_counts().reindex(['No paired values', 'Error rate', 'Accuracy-type'], fill_value=0)
NUMBERS['pair_availability'] = {k: int(v) for k, v in avail.items()}
XL = ['Not\nreported', 'Error\nrate', 'Accuracy\n-type']
bars = sns.barplot(x=XL, y=avail.values, ax=axes[0], palette=GLOBAL_PALETTE, hue=XL, legend=False)
axes[0].set_ylim(0, 290)
for i, v in enumerate(avail.values): axes[0].text(i, v + 3, str(v), ha='center', fontsize=18)
axes[0].set_ylabel("Number of Papers"); axes[0].set_xlabel("Paired Lab/Field Values")
pairs = df_all[df_all['pair_type'] != 'No paired values']
err, acc = pairs[pairs['pair_type'] == 'Error rate'], pairs[pairs['pair_type'] == 'Accuracy-type']
NUMBERS['paired_n'] = len(pairs); NUMBERS['paired_pct'] = pct(len(pairs))
NUMBERS['error_rate_pairs'] = dict(n=len(err), degrade=int((err.wild_eer > err.lab_eer).sum()),
                                   unchanged=int((err.wild_eer == err.lab_eer).sum()), improve=int((err.wild_eer < err.lab_eer).sum()),
                                   median_lab=round(err.lab_eer.median(), 2), median_field=round(err.wild_eer.median(), 2))
NUMBERS['accuracy_pairs'] = dict(n=len(acc), degrade=int((acc.wild_eer < acc.lab_eer).sum()),
                                 unchanged=int((acc.wild_eer == acc.lab_eer).sum()), improve=int((acc.wild_eer > acc.lab_eer).sum()),
                                 median_lab=round(acc.lab_eer.median(), 2), median_field=round(acc.wild_eer.median(), 2))
NUMBERS['paired_list'] = pairs[['citekey', 'pair_type', 'lab_eer', 'wild_eer']].values.tolist()

sns.scatterplot(data=err, x='lab_eer', y='wild_eer', s=150, ax=axes[1], alpha=0.7)
axes[1].plot([0, 20], [0, 20], 'k--', alpha=0.4)
axes[1].fill_between([0, 20], [0, 20], 20, color='red', alpha=0.05)
axes[1].set_xlim(0, 20); axes[1].set_ylim(0, 20)
axes[1].set_xlabel("Lab Error Rate (%)"); axes[1].set_ylabel("Field Error Rate (%)")

sns.scatterplot(data=acc, x='lab_eer', y='wild_eer', s=150, ax=axes[2], alpha=0.7, color=PAL_VIRIDIS[3], marker='s')
axes[2].plot([60, 100], [60, 100], 'k--', alpha=0.4)
axes[2].fill_between([60, 100], 60, [60, 100], color='red', alpha=0.05)
axes[2].set_xlim(60, 101); axes[2].set_ylim(60, 101)
axes[2].set_xlabel("Lab Accuracy-type (%)"); axes[2].set_ylabel("Field Accuracy-type (%)")
add_subplot_labels(axes, y_offset=-0.30)
save('RQ2_Fig2_Performance_Penalty.png')

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
rob_cols = ['Motion Robustness', 'Noise Robustness', 'Cross-Session']
NUMBERS['robustness'] = {c: [int(df_all[c].sum()), pct(df_all[c].sum())] for c in rob_cols}
df.groupby('year')[rob_cols].sum().plot(kind='bar', stacked=True, ax=axes[0], color=PAL_VIRIDIS[:3], alpha=0.85)
axes[0].set_ylabel("Number of Papers"); axes[0].set_xlabel("Year"); axes[0].tick_params(axis='x', rotation=45)
axes[0].legend(fontsize=18, **{**LEG, 'handleheight': 0.4})
yearly_trends = df.groupby('year')[rob_cols].mean() * 100
for i, column in enumerate(rob_cols):
    sns.lineplot(x=yearly_trends.index.astype(str), y=yearly_trends[column], marker='os^'[i], markersize=10,
                 color=PAL_VIRIDIS[i], linewidth=3, label=column, ax=axes[1])
axes[1].set_ylabel("% of Annual Papers (%)"); axes[1].set_xlabel("Year"); axes[1].set_ylim(0, 105)
axes[1].tick_params(axis='x', rotation=45); axes[1].legend(fontsize=19, **LEG)
add_subplot_labels(axes, y_offset=-0.45)
save('RQ2_Fig3_Robustness_Evolution.png')

fig, ax = plt.subplots(1, 1, figsize=(8, 8))
corr_rows = []
for p in data_list:
    total_subs = sum([to_float_safe(ds.get('num_subjects')) for ds in p.get('data', []) if to_float_safe(ds.get('num_subjects'))])
    eer_val = first_eer_std(p)   # REV: same EER definition as everywhere else
    if eer_val and total_subs > 0:
        if 0 < eer_val <= 20:
            corr_rows.append({'num_subjects': total_subs, 'eer': eer_val})
df_corr = pd.DataFrame(corr_rows)
rho, pv = stats.spearmanr(df_corr['num_subjects'], df_corr['eer'])
NUMBERS['spearman'] = dict(rho=round(rho, 3), p=round(pv, 3), n=len(df_corr))
sns.regplot(data=df_corr, x='num_subjects', y='eer', ax=ax, scatter_kws={'alpha': 0.7, 's': 100}, line_kws={'lw': 3})
ax.set_xscale('log'); ax.xaxis.set_major_formatter(ScalarFormatter())
x_log = np.log10(df_corr['num_subjects'])
w = 10 ** (x_log.mean() + x_log.std()) - 10 ** (x_log.mean() - x_log.std())
ax.add_patch(Ellipse((10 ** x_log.mean(), df_corr['eer'].mean()), width=w, height=2 * df_corr['eer'].std(),
                     edgecolor='black', facecolor='none', linestyle='--', linewidth=2))
ax.set_xlabel("Total Number of Subjects (Log Scale)"); ax.set_ylabel("Reported EER (%)")
save('RQ2_Fig4_subpool.png')

# ===================== RQ3 =====================
fig, axes = plt.subplots(1, 3, figsize=FIG_SIZE)
sec_summary = df_all[['spoofing', 'liveness']].sum()
NUMBERS['spoofing'] = [int(sec_summary['spoofing']), pct(sec_summary['spoofing'])]
NUMBERS['liveness'] = [int(sec_summary['liveness']), pct(sec_summary['liveness'])]
sns.barplot(x=['Spoofing', 'Liveness'], y=sec_summary.values, ax=axes[0], palette=PAL_VIRIDIS[:2], hue=['Spoofing', 'Liveness'], legend=False)
axes[0].set_ylabel("Number of Papers")
df.groupby('year')[['spoofing', 'liveness']].sum().plot(kind='bar', stacked=True, ax=axes[1], color=[PAL_VIRIDIS[0], PAL_VIRIDIS[2]], alpha=0.85)
axes[1].set_ylabel("Number of Papers"); axes[1].set_xlabel("Year"); axes[1].tick_params(axis='x', rotation=45)
axes[1].legend(fontsize=18, **LEG)
sec_pct = df.groupby('year')[['spoofing', 'liveness']].mean() * 100
sns.lineplot(data=sec_pct, markers=True, dashes=False, palette=[PAL_VIRIDIS[0], PAL_VIRIDIS[2]], linewidth=3, ax=axes[2])
axes[2].set_ylabel("Annual Prevalence (%)"); axes[2].set_xlabel("Year"); axes[2].set_ylim(0, 105)
axes[2].set_xticks(sec_pct.index.astype(int)); axes[2].tick_params(axis='x', rotation=45)
axes[2].legend(fontsize=18, **LEG)
add_subplot_labels(axes, y_offset=-0.50)
save('RQ3_Fig1_Security_Evolution.png')

def score_to_label(s):
    return 'high' if s >= 4 else ('medium' if s >= 2 else 'low')
df_all['repro_cat'] = df_all['repro_raw'].apply(score_to_label); df['repro_cat'] = df['repro_raw'].apply(score_to_label)
fig, axes = plt.subplots(1, 3, figsize=FIG_SIZE)
repro_prop = df_all['repro_cat'].value_counts(normalize=True).reindex(['low', 'medium', 'high'])
NUMBERS['repro'] = {k: [int((df_all['repro_cat'] == k).sum()), round(v * 100, 2)] for k, v in repro_prop.items()}
NUMBERS['repro_mean'] = round(df_all['repro_raw'].mean(), 2)
sns.barplot(x=repro_prop.index, y=repro_prop.values * 100, palette=[PAL_VIRIDIS[0], PAL_VIRIDIS[1], PAL_VIRIDIS[3]], hue=repro_prop.index, legend=False, ax=axes[0])
axes[0].set_ylabel("Percentage of Papers (%)"); axes[0].set_ylim(0, 100)
repro_trend = pd.crosstab(df['year'], df['repro_cat']).reindex(columns=['low', 'medium', 'high'], fill_value=0)
repro_trend.plot(kind='bar', stacked=True, ax=axes[1], color=[PAL_VIRIDIS[0], PAL_VIRIDIS[1], PAL_VIRIDIS[3]], alpha=0.9)
axes[1].set_ylabel("Number of Papers"); axes[1].set_xlabel("Year"); axes[1].tick_params(axis='x', rotation=45)
axes[1].legend(fontsize=17, **LEG)
rs = df.groupby('year')['repro_raw'].agg(['mean', 'std']).reset_index()
axes[2].errorbar(x=rs['year'].astype(str), y=rs['mean'], yerr=rs['std'], fmt='-o', color='black', linewidth=2, capsize=4)
axes[2].set_ylabel("Mean Reproducibility \n Score"); axes[2].set_xlabel("Year"); axes[2].set_ylim(0, 5)
axes[2].tick_params(axis='x', rotation=45)
add_subplot_labels(axes, y_offset=-0.50)
save('RQ3_Fig2_Reproducibility_Improved.png')

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
all_attacks = [a for L in df_all['attacks'] for a in (L if isinstance(L, list) else [L]) if a != 'none']
attack_counts = pd.Series(all_attacks).value_counts().head(6)
n_sec = int(df_all['attacks'].apply(lambda L: bool([a for a in (L or []) if a != 'none'])).sum())
NUMBERS['attack_papers'] = n_sec
NUMBERS['attacks'] = {a: [int(df_all['attacks'].apply(lambda L: a in (L or [])).sum()),
                          pct(df_all['attacks'].apply(lambda L: a in (L or [])).sum()),
                          round(df_all['attacks'].apply(lambda L: a in (L or [])).sum() / n_sec * 100, 1)]
                      for a in attack_counts.index}
sns.barplot(x=attack_counts.values, y=attack_counts.index, ax=axes[0], palette=GLOBAL_PALETTE, hue=attack_counts.index, legend=False)
axes[0].set_xlabel("Number of Mentions"); axes[0].set_ylabel("Attack Type")       # REV (R1.2): was "None"
attack_list = [{'year': r['year'], 'attack': a} for _, r in df.iterrows()
               for a in (r['attacks'] if isinstance(r['attacks'], list) else [r['attacks']]) if a and a != 'none']
df_atk = pd.DataFrame(attack_list)
top = df_atk['attack'].value_counts().head(5).index
atk_matrix = pd.crosstab(df_atk[df_atk['attack'].isin(top)]['attack'], df_atk[df_atk['attack'].isin(top)]['year']) \
               .div(df['year'].value_counts(), axis=1) * 100
sns.heatmap(atk_matrix.fillna(0), annot=False, cmap="viridis", ax=axes[1], cbar_kws={'label': '% of Papers'})
axes[1].set_ylabel(""); axes[1].set_xlabel("Year")                                # REV (R1.2): was "year"
axes[1].tick_params(axis='x', rotation=45)
add_subplot_labels(axes, y_offset=-0.60)
save('RQ3_Fig3_Deployment_Attacks.png')

# REV: abstract numbers not computed in the original notebook — recomputed here for traceability
e = df_all['eer'].dropna()                         # as reported, percent (first_eer_std)
NUMBERS['eer_reported'] = dict(n=len(e), median=round(e.median(), 2), q1=round(e.quantile(.25), 2), q3=round(e.quantile(.75), 2))
ratio = (err.wild_eer / err.lab_eer).replace([np.inf], np.nan).dropna()
NUMBERS['error_pair_ratio'] = dict(n=len(ratio), mean=round(ratio.mean(), 2), median=round(ratio.median(), 2),
                                   excluded_zero_lab=int((err.lab_eer == 0).sum()))
ratio_old = []
for p in data_list:   # original definition: all 20 raw pairs, as in submitted paper (for comparison only)
    g = p.get('real_world_gap') or {}
    a, b = to_float_safe(g.get('lab_performance_value')), to_float_safe(g.get('real_world_performance_value'))
    if a and b: ratio_old.append(b / a)
NUMBERS['ratio_original_definition'] = dict(n=len(ratio_old), mean=round(float(np.mean(ratio_old)), 2))
subs = []
for p in data_list:
    s = sum(to_float_safe(d.get('num_subjects')) or 0 for d in (p.get('data') or []))
    if s > 0: subs.append(s)
NUMBERS['subjects'] = dict(n=len(subs), median=float(np.median(subs)))
NUMBERS['supervised'] = [int((df_all['learning_type'] == 'supervised').sum()), pct((df_all['learning_type'] == 'supervised').sum())]
NUMBERS['learning_type'] = {k: int(v) for k, v in df_all['learning_type'].value_counts().items()}

json.dump(NUMBERS, open('numbers.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(json.dumps(NUMBERS, indent=2, ensure_ascii=False))
