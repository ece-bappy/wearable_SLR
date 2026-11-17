"""Editor item: Highlights (docx, <=85 chars each). The graphical abstract is produced by make_ga_v4.py.
Numbers come from revision/phase2/numbers.json and revision/phase3/numbers_phase3.json (N=263)."""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from docx import Document

OUT = 'revision/editor'; os.makedirs(OUT, exist_ok=True)
n2 = json.load(open('revision/phase2/numbers.json', encoding='utf-8'))
n3 = json.load(open('revision/phase3/numbers_phase3.json', encoding='utf-8'))
assert n2['N'] == 263 and n3['N'] == 263

tel = n3['telemetry']
n_fmt = len([k for k in tel['energy_unit_classes'] if k != 'Other'])
H = [  # every number computed from the JSON outputs
    f"Audit of {n2['N']} wearable biometric studies: {n2['tiers']['Lab-only'][1]:.1f}% are evaluated only in the lab",
    f"Only {n2['paired_pct']:.1f}% report paired lab/field results; field error is "
    f"{n2['error_pair_ratio']['median']:.2f}x the lab value",
    "Multimodal fusion is field-tested more often but still degrades in the field",
    f"Only {tel['latency_any'][1]:.0f}% report latency and {tel['energy_any'][1]:.0f}% energy, "
    f"in {n_fmt}+ incompatible formats",
    f"{n2['repro']['low'][1]:.1f}% show low reproducibility; reported EER is unrelated to subject-pool size",
]
for h in H:
    assert len(h) <= 85, (len(h), h)
d = Document(); d.add_heading('Highlights', level=1)
for h in H: d.add_paragraph(h, style='List Bullet')
d.save(f'{OUT}/Highlights_revised.docx')
print('highlights:', [len(h) for h in H])

# Graphical abstract: see make_ga_v4.py (final version).
