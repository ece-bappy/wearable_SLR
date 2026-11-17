"""Explore raw latency / energy / memory fields (read-only)."""
import json, glob, re, collections
P = [json.load(open(f, encoding="utf-8")) for f in glob.glob("../data/jsons_dedup/*.json")]
P = [p for p in P if p.get("relevance") == "include"]
lat_u, en_u = collections.Counter(), collections.Counter()
for p in P:
    u = p.get("usability") or {}
    for x in (u.get("latency") or []):
        if isinstance(x, dict) and x.get("value") is not None: lat_u[str(x.get("unit")).strip()] += 1
    for x in (u.get("energy_consumption") or []):
        if isinstance(x, dict) and x.get("value") is not None: en_u[str(x.get("unit")).strip()] += 1
print("LATENCY UNITS", lat_u.most_common())
print("ENERGY UNITS", en_u.most_common())
print("non-dict latency entries:", sum(1 for p in P for x in ((p.get('usability') or {}).get('latency') or []) if not isinstance(x, dict)))
mem = [p.get("citekey") for p in P if re.search(r"\b(RAM|memory|footprint|model size|parameters)\b", json.dumps(p), re.I)]
print("memory/model-size mentions:", len(mem))
print("gap tags HIGH_LATENCY / HIGH_ENERGY_COST:",
      sum("HIGH_LATENCY" in ((p.get('insights') or {}).get('gap_category') or []) for p in P),
      sum("HIGH_ENERGY_COST" in ((p.get('insights') or {}).get('gap_category') or []) for p in P))
