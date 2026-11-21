"""Graphical abstract v5 — Elsevier 'visual abstract' layout (title bar, method strip, three result panels,
conclusion box), in the same viridis theme as the manuscript figures. Drawn at true size (13 cm wide),
min font 7 pt, solid text colours. Vector icons drawn with matplotlib patches (no third-party art).
Outputs: revision/editor/Graphical_Abstract.{pdf,tiff,png}. Numbers from phase2/phase3 json (N = 263)."""
import json
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Wedge, Circle

n2 = json.load(open('revision/phase2/numbers.json', encoding='utf-8'))
n3 = json.load(open('revision/phase3/numbers_phase3.json', encoding='utf-8'))
N = n2['N']; assert N == 263
er, ac = n2['error_rate_pairs'], n2['accuracy_pairs']
degrade = er['degrade'] + ac['degrade']; paired = n2['paired_n']

def soft(c, f=0.28):                                      # blend toward white: calmer viridis
    r, g, b = matplotlib.colors.to_rgb(c); return matplotlib.colors.to_hex((r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f))
V = [soft(c) for c in sns.color_palette('viridis', 5).as_hex()]   # manuscript palette, softened
DARK, MID, TEAL, GREEN, LIME = V
SLATE = '#2f3e5c'                                         # accent text colour (solid)
INK, WHITE, LIGHT, RED = '#1a1a1a', '#ffffff', '#f4f6f9', '#b5473c'
LINE, TAB, CORAL = '#c8cfda', '#e8edf4', '#e0857a'
TIER_C = [V[0], V[1], V[3], V[4]]                         # same tier colours as Fig. 6
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "text.color": INK,
                     "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42})
CM = 1 / 2.54; W, H = 13.0, 7.4
fig = plt.figure(figsize=(W * CM, H * CM), facecolor='white')
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
FT, FH, FB, FS = 9.5, 8, 7.5, 7      # title, headers, body, small (pt at final size)

def rbox(x, y, w, h, fc, ec='none', r=0.12, lw=0.8, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw, zorder=z))

# ---------------- title bar ----------------
ax.text(0.25, H - 0.34, 'The Reality Gap in wearable biometric authentication', color=SLATE, fontsize=FT + 1,
        fontweight='bold', va='center')
ax.text(0.25, H - 0.72, f'A meta-analytical audit of robustness, reproducibility and deployability in {N} studies',
        color=INK, fontsize=FB, va='center')
ax.add_patch(Rectangle((0.25, H - 0.98), W - 0.5, 0.035, fc=TEAL, lw=0))

# ---------------- method strip with icons ----------------
sy, sh = H - 2.35, 1.3
ax.add_patch(Rectangle((0, sy), W, sh, fc=LIGHT, lw=0))
def icon_db(cx, cy, c):
    for dy in (0.22, 0.0, -0.22):
        ax.add_patch(Ellipse((cx, cy + dy), 0.62, 0.2, fc=c, ec=WHITE, lw=0.8, zorder=3))
def icon_funnel(cx, cy, c):
    ax.add_patch(Polygon([[cx - 0.33, cy + 0.27], [cx + 0.33, cy + 0.27], [cx + 0.07, cy - 0.05],
                          [cx + 0.07, cy - 0.3], [cx - 0.07, cy - 0.22], [cx - 0.07, cy - 0.05]], fc=c, lw=0, zorder=3))
def icon_doc(cx, cy, c):
    ax.add_patch(Polygon([[cx - 0.24, cy - 0.32], [cx + 0.24, cy - 0.32], [cx + 0.24, cy + 0.2],
                          [cx + 0.12, cy + 0.32], [cx - 0.24, cy + 0.32]], fc=c, lw=0, zorder=3))
    for k in range(3):
        ax.plot([cx - 0.15, cx + 0.15], [cy + 0.14 - k * 0.12] * 2, color=WHITE, lw=0.9, zorder=4)
    ax.plot([cx - 0.1, cx - 0.02, cx + 0.14], [cy - 0.2, cy - 0.27, cy - 0.12], color=LIME, lw=1.4, zorder=4)
def icon_watch(cx, cy, c):
    ax.add_patch(Rectangle((cx - 0.1, cy - 0.34), 0.2, 0.68, fc=c, lw=0, zorder=2))
    rbox(cx - 0.21, cy - 0.21, 0.42, 0.42, fc=c, ec=WHITE, r=0.08, lw=0.8, z=3)
    ax.plot([cx - 0.11, cx - 0.04, cx + 0.02, cx + 0.07, cx + 0.12], [cy, cy, cy + 0.1, cy - 0.08, cy],
            color=LIME, lw=1.1, zorder=4)
steps = [(icon_db, '2,039 records', 'OpenAlex search'),
         (icon_funnel, 'PRISMA screening', 'and de-duplication'),
         (icon_doc, 'LLM extraction', 'human-verified'),
         (icon_watch, f'{N} studies', '2017–2026')]
xs = np.linspace(1.15, W - 1.6, len(steps))
for i, (fn, a, b) in enumerate(steps):
    fn(xs[i] - 0.55, sy + sh / 2, [DARK, MID, TEAL, GREEN][i])
    ax.text(xs[i] - 0.1, sy + sh / 2 + 0.13, a, fontsize=FB, fontweight='bold', va='center')
    ax.text(xs[i] - 0.1, sy + sh / 2 - 0.17, b, fontsize=FS, va='center')
    if i < len(steps) - 1:
        xa = (xs[i] + xs[i + 1]) / 2 + 0.68
        ax.annotate('', xy=(xa + 0.22, sy + sh / 2), xytext=(xa - 0.22, sy + sh / 2),
                    arrowprops=dict(arrowstyle='-|>,head_width=0.25,head_length=0.35', color=MID, lw=1.6))

# ---------------- three result panels ----------------
py, ph = 1.4, 3.45
pw, gap = (W - 0.5 - 2 * 0.2) / 3, 0.2
heads = ['Where are systems evaluated?', 'What happens in the field?', 'Is the evidence deployable?']
PX = [0.25 + k * (pw + gap) for k in range(3)]
for k in range(3):
    rbox(PX[k], py, pw, ph, fc=WHITE, ec=LINE, lw=0.6)
    ax.add_patch(FancyBboxPatch((PX[k] + 0.02, py + ph - 0.47), pw - 0.04, 0.45, boxstyle='round,pad=0,rounding_size=0.1',
                                fc=TAB, lw=0, zorder=2))
    ax.add_patch(Rectangle((PX[k] + 0.02, py + ph - 0.47), pw - 0.04, 0.2, fc=TAB, lw=0, zorder=2))
    ax.text(PX[k] + pw / 2, py + ph - 0.245, heads[k], color=SLATE, fontsize=FH, fontweight='bold',
            ha='center', va='center', zorder=3)

# panel 1: donut of evidence tiers
tiers = n2['tiers']; cnt = [v[0] for v in tiers.values()]
cx, cy, R = PX[0] + 1.05, py + 1.62, 0.92
start = 90
for c, col in zip(cnt, TIER_C):
    ang = 360 * c / N
    ax.add_patch(Wedge((cx, cy), R, start - ang, start, width=0.36, fc=col, ec=WHITE, lw=0.8, zorder=3))
    start -= ang
ax.text(cx, cy + 0.1, f"{tiers['Lab-only'][1]:.1f}%", ha='center', va='center', fontsize=FH + 1, fontweight='bold')
ax.text(cx, cy - 0.2, 'lab-only', ha='center', va='center', fontsize=FS)
leg = ['Lab-only', 'Field only', 'Compared', 'Paired']
for i, (t, c, col) in enumerate(zip(leg, cnt, TIER_C)):
    yy = py + 2.42 - i * 0.38
    ax.add_patch(Rectangle((PX[0] + 2.1, yy - 0.09), 0.18, 0.18, fc=col, lw=0))
    ax.text(PX[0] + 2.35, yy, f'{t} ({c})', fontsize=FS, va='center')
ax.text(PX[0] + pw / 2, py + 0.3, f'Only {n2["paired_pct"]:.1f}% report paired results',
        ha='center', va='center', fontsize=FB, fontweight='bold', color=SLATE)

# panel 2: slope chart
a2 = fig.add_axes([(PX[1] + 0.85) / W, (py + 0.85) / H, (pw - 1.3) / W, (ph - 1.55) / H])
for _, _, a, b in [p for p in n2['paired_list'] if p[1] == 'Error rate']:
    a2.plot([0, 1], [a, b], color=CORAL if b > a else '#9aa3b0', lw=0.7, marker='o', ms=1.6)
a2.plot([0, 1], [er['median_lab'], er['median_field']], color=SLATE, lw=1.6, marker='o', ms=3)
a2.text(1.1, er['median_field'], f"{er['median_field']:.1f}%", fontsize=FS, va='center', fontweight='bold', color=SLATE)
a2.text(-0.1, er['median_lab'], f"{er['median_lab']:.1f}%", fontsize=FS, va='center', ha='right', fontweight='bold', color=SLATE)
a2.set_xticks([0, 1]); a2.set_xticklabels(['Lab', 'Field'], fontsize=FB)
a2.set_xlim(-0.6, 1.6); a2.set_ylim(-1.5, 19.5); a2.set_yticks([0, 10, 20][:2])
a2.tick_params(axis='y', labelsize=FS, length=0, pad=2, colors=INK); a2.tick_params(axis='x', length=0, pad=2, colors=INK)
a2.set_ylabel('Error rate (%)', fontsize=FS, labelpad=1)
for s in ['top', 'right', 'left']: a2.spines[s].set_visible(False)
a2.spines['bottom'].set_linewidth(0.6); a2.spines['bottom'].set_color(LINE)
ax.text(PX[1] + pw / 2, py + 0.3, f"{degrade} of {paired} degrade; error ×{n2['error_pair_ratio']['median']:.2f}",
        ha='center', va='center', fontsize=FB, fontweight='bold', color=RED)

# panel 3: reporting bars
tel = n3['telemetry']
B = [('Field data', n2['field_any'][1]), ('Latency', tel['latency_any'][1]), ('Spoofing tests', n2['spoofing'][1]),
     ('Energy', tel['energy_any'][1]), ('Reproducible', n2['repro']['high'][1]),
     ('Synthetic attacks', n2['attacks']['synthetic/deepfake'][1])]
# (no 'Memory' bar: memory/RAM was not part of the extraction schema, so no reporting rate exists)
bx, bw = PX[2] + 2.05, pw - 2.65
for i, (t, v) in enumerate(B):
    yy = py + 2.4 - i * 0.3          # 6 bars, vertically centred where the 7-bar layout was
    ax.add_patch(Rectangle((bx, yy - 0.08), bw, 0.16, fc=LIGHT, lw=0))
    if v > 0:
        ax.add_patch(Rectangle((bx, yy - 0.08), bw * v / 100, 0.16, fc=TEAL if v >= 20 else MID, lw=0))
    ax.text(bx - 0.12, yy, t, fontsize=FS, ha='right', va='center')
    ax.text(bx + bw * v / 100 + 0.1, yy, f'{v:.0f}%', fontsize=FS, va='center', fontweight='bold')
ax.text(PX[2] + pw / 2, py + 0.3, f'% of {N} studies reporting each',
        ha='center', va='center', fontsize=FS, style='italic', color=INK)

# ---------------- conclusion ----------------
rbox(0.25, 0.15, W - 0.5, 1.05, fc=LIGHT, ec='none')
ax.add_patch(Rectangle((0.25, 0.15), 0.07, 1.05, fc=TEAL, lw=0))
ax.text(0.5, 0.88, 'CONCLUSION:', fontsize=FH, fontweight='bold', color=SLATE, va='center')
ax.text(2.65, 0.88, 'Laboratory accuracy is not evidence of deployability. Studies should report paired',
        fontsize=FB, va='center')
ax.text(0.5, 0.48, 'lab/field results, cross-session tests, telemetry (ms, mW, kB), active-attacker tests, and open data.',
        fontsize=FB, va='center')

fig.savefig('revision/editor/Graphical_Abstract.pdf', facecolor='white')
fig.savefig('revision/editor/Graphical_Abstract.tiff', dpi=600, facecolor='white', pil_kwargs={'compression': 'tiff_lzw'})
fig.savefig('revision/editor/Graphical_Abstract.png', dpi=300, facecolor='white')
print('saved', round(W * CM * 600), 'x', round(H * CM * 600), 'px @600dpi')
