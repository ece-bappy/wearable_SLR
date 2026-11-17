"""Explore overlap of real-world evidence flags across the 279 included papers."""
import json, glob, os
P = [json.load(open(f, encoding="utf-8")) for f in glob.glob("../data/jsons_dedup/*.json")]
P = [p for p in P if p.get("relevance") == "include"]

def num(v):
    if isinstance(v, list): v = v[0] if v else None
    if isinstance(v, dict): v = v.get("value")
    try: return float(v)
    except (TypeError, ValueError): return None

rows = []
for p in P:
    g = p.get("real_world_gap") or {}
    rows.append(dict(
        rw=bool(p.get("real_world_tested")),
        wild=any((d or {}).get("collection_setting") == "in-the-wild" for d in (p.get("data") or [])),
        semi=any((d or {}).get("collection_setting") == "semi-controlled" for d in (p.get("data") or [])),
        cmp=bool(g.get("environments_compared")),
        paired=num(g.get("lab_performance_value")) is not None and num(g.get("real_world_performance_value")) is not None,
    ))
N = len(rows); c = lambda f: sum(1 for r in rows if f(r))
print("N", N)
for k in ["rw", "wild", "semi", "cmp", "paired"]: print(k, c(lambda r: r[k]))
print("field = rw or wild:", c(lambda r: r["rw"] or r["wild"]))
print("comparative = cmp or paired:", c(lambda r: r["cmp"] or r["paired"]))
print("paired but not rw:", c(lambda r: r["paired"] and not r["rw"]), " paired not cmp:", c(lambda r: r["paired"] and not r["cmp"]))
print("cmp not field:", c(lambda r: r["cmp"] and not (r["rw"] or r["wild"])))
print("rw but no wild dataset:", c(lambda r: r["rw"] and not r["wild"]), " wild but not rw:", c(lambda r: r["wild"] and not r["rw"]))
