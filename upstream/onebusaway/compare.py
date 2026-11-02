"""Compare baseline and patched audit folders; write SUMMARY.md and print GitHub annotations."""
import json, sys
from pathlib import Path

def findings(root: Path):
    out = {}
    for rep in sorted(root.rglob("report.json")):
        try:
            data = json.loads(rep.read_text())
        except Exception:
            continue
        screens = data if isinstance(data, list) else data.get("screens", [])
        for s in screens:
            name = s.get("target") or rep.parent.name
            for f in s.get("findings", []):
                key = (rep.parent.name, Path(str(name)).stem.replace(".large", ""), f.get("wcag", ""), f.get("element", "")[:60])
                out[key] = f
    return out

base, patched, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
b, p = findings(base), findings(patched)
gone = sorted(set(b) - set(p)); new = sorted(set(p) - set(b)); same = sorted(set(b) & set(p))
lines = ["# OneBusAway audit summary", "", f"Baseline findings: {len(b)}", f"Patched findings: {len(p)}",
         f"Resolved by the patches: {len(gone)}", f"New in patched build: {len(new)}", f"Unchanged: {len(same)}", ""]
for title, keys, src in (("Resolved", gone, b), ("New", new, p), ("Unchanged", same, p)):
    lines += [f"## {title}", ""]
    for k in keys:
        f = src[k]
        lines.append(f"- [{k[0]}/{k[1]}] {k[2]} {k[3]}: {f.get('message', '')[:200]}")
    lines.append("")
out.write_text("\n".join(lines))
print(f"::notice title=OBA audit::baseline {len(b)}, patched {len(p)}, resolved {len(gone)}, new {len(new)}")
for k in same + new:
    f = p[k]
    print(f"::warning title=OBA {k[0]}/{k[1]} {k[2]}::{k[3]} | {f.get('message','')[:300]}")
