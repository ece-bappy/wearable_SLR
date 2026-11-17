"""Graphical abstract v4 — drawn at true print size (13 cm wide) so it is readable at 13 cm (Elsevier GA rule).
Vector PDF (preferred) + 600-dpi TIFF. Text in solid colours only; min font 7 pt at final size.
Layout units: data coordinates 0..W x 0..H (unchanged geometry idea from v3), fonts in real points.
All numbers from revision/phase2/numbers.json (N = 263)."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

n2 = json.load(open('revision/phase2/numbers.json', encoding='utf-8'))
N = n2['N']; T = {k: v[0] for k, v in n2['tiers'].items()}
lab_only, field_only = T['Lab-only'], T['Field data, no comparison']
compared_only, paired = T['Lab vs. field compared'], T['Paired lab/field values']
field_any, compared_any = n2['field_any'][0], n2['compared_any'][0]
er, ac = n2['error_rate_pairs'], n2['accuracy_pairs']
degrade = er['degrade'] + ac['degrade']; not_degrade = paired - degrade
assert lab_only + field_any == N and field_only + compared_any == field_any and compared_only + paired == compared_any

INK, ACC, RED = '#111111', '#1f4e79', '#b22222'          # text colours: solid only
BAND_DROP, BAND_ACC = '#cfd3d8', '#2f6496'              # shapes may be tinted
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "text.color": INK,
                     "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42})
CM = 1 / 2.54
FIG_W, FIG_H = 13 * CM, 5.6 * CM                         # true size
W, H = 13.0, 5.6                                         # layout units = cm
F_HEAD, F_NUM, F_TXT = 9.5, 9, 7.5                       # points at final size (>= 7 pt)

fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor='white')
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')

TOP, BOT = 4.55, 0.35
U = (TOP - BOT - 0.55) / N                               # cm per study (0.55 cm of gaps)

def band(x0, y0, x1, y1, h, color):
    t = np.linspace(0, 1, 80); s = 3 * t**2 - 2 * t**3
    xs = x0 + (x1 - x0) * t; lo = y0 + (y1 - y0) * s
    ax.fill_between(xs, lo, lo + h, color=color, lw=0)
def node(x, y, h, color):
    ax.add_patch(plt.Rectangle((x - 0.03, y), 0.06, h, color=color, lw=0))
def label(x, y, num, txt, color=INK, ha='left'):
    ax.text(x, y + 0.03, num, ha=ha, va='bottom', fontsize=F_NUM, color=color, fontweight='bold')
    ax.text(x, y + 0.01, txt, ha=ha, va='top', fontsize=F_TXT, color=color, linespacing=1.05)

X = [1.05, 2.45, 3.85, 5.25, 6.45]
y0 = TOP - N * U
node(X[0], y0, N * U, INK)
# lab-only branch
yf1 = TOP - field_any * U; y_lab = BOT
band(X[0], y0 + lab_only * U, X[1], yf1, field_any * U, BAND_ACC)
band(X[0], y0, X[1], y_lab, lab_only * U, BAND_DROP)
node(X[1], yf1, field_any * U, ACC); node(X[1], y_lab, lab_only * U, INK)
# field-only branch
yc2 = TOP - compared_any * U; y_fo = yf1 - 0.3 - (field_only - compared_any) * U * 0.0
y_fo = yc2 - 0.3 - field_only * U
band(X[1], yf1 + field_only * U, X[2], yc2, compared_any * U, BAND_ACC)
band(X[1], yf1, X[2], y_fo, field_only * U, BAND_DROP)
node(X[2], yc2, compared_any * U, ACC); node(X[2], y_fo, field_only * U, INK)
# compared-only branch
yp3 = TOP - paired * U; y_co = yp3 - 0.3 - compared_only * U
band(X[2], yc2 + compared_only * U, X[3], yp3, paired * U, BAND_ACC)
band(X[2], yc2, X[3], y_co, compared_only * U, BAND_DROP)
node(X[3], yp3, paired * U, ACC); node(X[3], y_co, compared_only * U, INK)
# outcome
yd4 = TOP - degrade * U; y_nd = yd4 - 0.22 - not_degrade * U
band(X[3], yp3 + not_degrade * U, X[4], yd4, degrade * U, RED)
band(X[3], yp3, X[4], y_nd, not_degrade * U, BAND_DROP)
node(X[4], yd4, degrade * U, RED); node(X[4], y_nd, not_degrade * U, INK)

label(X[0] - 0.1, y0 + N * U / 2, f'{N}', 'studies', ha='right')
label(X[1] + 0.1, y_lab + lab_only * U / 2, f'{lab_only}', 'lab only')
label(X[2] + 0.1, y_fo + field_only * U / 2 - 0.05, f'{field_only}', 'field data,\nno comparison')
label(X[3] + 0.1, y_co + compared_only * U / 2 - 0.1, f'{compared_only}', 'compared,\nno paired values')
label(X[4] + 0.1, yd4 + degrade * U / 2 - 0.08, f'{degrade} of {paired}', 'worse in\nthe field', color=RED)
for x, t in zip(X[1:4], ['field data', 'lab vs. field', 'paired']):
    ax.text(x, TOP + 0.08, t, ha='center', va='bottom', fontsize=F_TXT, color=ACC, style='italic')

ax.text(0.2, H - 0.32, 'Most wearable biometric results never leave the lab; the few that do get worse.',
        fontsize=F_HEAD, va='center', fontweight='bold')

# ---- slope chart (13 verified error-rate pairs) ----
x_ax, w_ax = 8.55, 4.05
a2 = fig.add_axes([x_ax / W, 0.75 / H, w_ax / W, 3.35 / H])
pairs = [p for p in n2['paired_list'] if p[1] == 'Error rate']
for _, _, a, b in pairs:
    a2.plot([0, 1], [a, b], color=RED if b > a else '#555555', lw=0.7, marker='o', ms=1.8, alpha=0.85)
ma, mb = er['median_lab'], er['median_field']
a2.plot([0, 1], [ma, mb], color=INK, lw=1.6, marker='o', ms=3)
a2.text(1.07, mb, f'{mb:.1f}%', va='center', fontsize=F_TXT, fontweight='bold')
a2.text(-0.07, ma, f'{ma:.1f}%', va='center', ha='right', fontsize=F_TXT, fontweight='bold')
a2.set_xticks([0, 1]); a2.set_xticklabels(['lab', 'field'], fontsize=F_TXT)
a2.set_xlim(-0.45, 1.45); a2.set_ylim(-0.5, 19.5)
a2.set_yticks([0, 5, 10, 15]); a2.tick_params(axis='y', labelsize=F_TXT, colors=INK, length=0, pad=1)
a2.tick_params(axis='x', length=0, pad=2, colors=INK)
for s in ['top', 'right', 'left']: a2.spines[s].set_visible(False)
a2.spines['bottom'].set_color(INK); a2.spines['bottom'].set_linewidth(0.6)
a2.set_ylabel('error rate (%)', fontsize=F_TXT, color=INK, labelpad=1)
ax.text(x_ax - 0.35, 4.62, f'{er["n"]} paired error-rate studies:', fontsize=F_TXT, va='center')
ax.text(x_ax - 0.35, 4.25, f'field error = {n2["error_pair_ratio"]["median"]:.2f}$\\times$ lab (median)',
        fontsize=F_TXT, va='center', color=RED, fontweight='bold')

fig.savefig('revision/editor/Graphical_Abstract.pdf', facecolor='white')
fig.savefig('revision/editor/Graphical_Abstract.tiff', dpi=600, facecolor='white', pil_kwargs={'compression': 'tiff_lzw'})
fig.savefig('revision/editor/Graphical_Abstract.png', dpi=300, facecolor='white')
print('saved; size px @600dpi =', round(FIG_W * 600), 'x', round(FIG_H * 600))
