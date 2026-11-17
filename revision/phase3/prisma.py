"""Redraw the PRISMA diagram (original prsm_new.png) with the post-extraction de-duplication step."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import glob, json
# Search/screening counts (2039, 290, 1249, 500, 221) come from the original search log (fixed);
# the post-extraction counts are derived from the data.
_inc = lambda folder: sum(json.load(open(f, encoding='utf-8')).get('relevance') == 'include' for f in glob.glob(folder + '/*.json'))
import os
_orig = next(d for d in ['../phase1_repro/jsons_test', '../../jsons_w_citekey'] if os.path.isdir(d))  # local layout / GitHub layout
N_EXTRACTED = _inc(_orig)   # included before de-duplication (original corpus)
N_FINAL = _inc('../data/jsons_dedup')
N_DUP = len(open('../data/removed_duplicates.txt', encoding='utf-8-sig').read().strip().split(','))
BLUE, NAVY = '#428bb5', '#1f2d6b'
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"]})
fig, ax = plt.subplots(figsize=(9.8, 12.6)); ax.set_xlim(0, 100); ax.set_ylim(0, 128); ax.axis('off')

def box(x, y, w, h, head, body, fs=15):
    ax.add_patch(Rectangle((x, y + h / 2), w, h / 2, fc=BLUE, ec='black', lw=1.5))
    ax.add_patch(Rectangle((x, y), w, h / 2, fc='white', ec='black', lw=1.5))
    ax.text(x + w / 2, y + 3 * h / 4, head, ha='center', va='center', color='white', fontsize=fs, fontweight='bold')
    ax.text(x + w / 2, y + h / 4, body, ha='center', va='center', fontsize=fs)
def side(x, y, w, h, text, fs=14):
    ax.add_patch(Rectangle((x, y), w, h, fc='white', ec='black', lw=1.5))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, linespacing=1.4)
def stage(y, h, label):
    ax.add_patch(Rectangle((0, y), 6, h, fc=BLUE, ec='black', lw=1.5))
    ax.text(3, y + h / 2, label, rotation=90, ha='center', va='center', color='white', fontsize=16, fontweight='bold')
def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.5))

ax.add_patch(Rectangle((16, 118), 74, 9, fc=BLUE, ec='black', lw=1.5))
ax.text(53, 122.5, 'Identification of new studies via database', ha='center', va='center', color='white', fontsize=17, fontweight='bold')
X, W, H, SX, SW = 11, 47, 10, 61.5, 38.5
rows = [  # y, head, body, side text
    (101, 'Records identified from database:', 'OpenAlex (n = 2039)', 'Records removed before screening:\nDuplicate records (n = 290)'),
    (84, 'Records screened', '(n = 1749)', 'Records marked as ineligible\nby automation tools (n = 1249)'),
    (67, 'Records sought for retrieval', '(n = 500)', None),
    (50, 'Records assessed for eligibility', '(n = 500)', 'Records excluded: failed manual\nrelevance check (n = 221)'),
    (33, 'Full-text records extracted', f'(n = {N_EXTRACTED})', f'Duplicate full-text records\nidentified after extraction (n = {N_DUP})'),
    (14, 'New studies included in review', f'(n = {N_FINAL})', None)]
assert 2039 - 290 == 1749 and 1749 - 1249 == 500 and 500 - 221 == N_EXTRACTED and N_EXTRACTED - N_DUP == N_FINAL
for i, (y, head, body, s) in enumerate(rows):
    box(X, y, W, H, head, body)
    if s:
        side(SX, y + 0.5, SW, H - 1, s); arrow(X + W, y + H / 2, SX, y + H / 2)
    if i + 1 < len(rows): arrow(X + W / 2, y, X + W / 2, rows[i + 1][0] + H)
stage(95, 21, 'Identification'); stage(31, 63, 'Screening'); stage(12, 17, 'Included')
plt.savefig('figures/prisma_revised.png', dpi=400, bbox_inches='tight'); print('ok')
