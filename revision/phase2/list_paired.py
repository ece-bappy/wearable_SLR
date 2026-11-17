"""List the 20 papers reporting both lab and real-world performance values."""
import json, glob, os

def num(v):
    if isinstance(v, list): v = v[0] if v else None
    if isinstance(v, dict): v = v.get('value')
    try: return float(v)
    except (TypeError, ValueError): return None

for f in sorted(glob.glob('../data/jsons_dedup/*.json'), key=lambda s: int(os.path.basename(s)[:-5])):
    p = json.load(open(f, encoding='utf-8'))
    if p.get('relevance') != 'include': continue
    g = p.get('real_world_gap') or {}
    a, b = num(g.get('lab_performance_value')), num(g.get('real_world_performance_value'))
    if a is None or b is None: continue
    fu = p.get('fusion') or {}
    print(f"{os.path.basename(f):>9} {str(p.get('citekey')):<24} lab={a:<7} wild={b:<7} "
          f"{'wild>=lab' if b >= a else 'WILD<LAB':<9} multimodal={fu.get('is_multimodal')!s:<5} "
          f"fusion={fu.get('fusion_level')!s:<8} drop%={g.get('drop_percentage')}")
