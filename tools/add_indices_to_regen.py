#!/usr/bin/env python
"""
Add `specification_index` and `source_file` to regenerated JSONs.

- Assumes each regenerated file has an array of specs, either under
  "specifications" or "results" (falls back to top-level list).
- Uses the ORIGINALS JSON (your combined.json list) to map
  1-based index -> filename (program_001.py, ...).
- Optionally filters rows to the indices present in a verified-only JSON.

Usage:
  python add_indices_to_regen.py \
    --originals datasets/combined.json \
    --regen "output/regenerate/*.json" \
    --outdir output/regen_indexed \
    --code-field program_specification \
    --extract-python \
    --verified "output/verified_only/*.json"

If you don’t want to filter to verified only, omit --verified.
"""

import json, glob, os, re, argparse
from pathlib import Path

def load_original_index_map(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = obj if isinstance(obj, list) else obj.get("results") or obj.get("data") or obj.get("programs") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    idx2name = {}
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue
        name = r.get("filename") or r.get("source_file") or r.get("file_path") or r.get("name")
        if not name:
            continue
        idx2name[i] = os.path.basename(name)
    if not idx2name:
        raise ValueError("No filenames found in originals JSON.")
    return idx2name

def load_verified_indices(globs):
    idxs = set()
    for pat in globs:
        for p in glob.glob(pat):
            obj = json.loads(Path(p).read_text(encoding="utf-8"))
            rows = obj.get("results", obj if isinstance(obj, list) else [])
            for r in rows:
                si = r.get("specification_index")
                # keep ints only
                try:
                    si = int(si)
                    idxs.add(si)
                except Exception:
                    pass
    return idxs

def extract_python_block(text: str) -> str:
    if not isinstance(text, str):
        return ""
    m = re.search(r"```(?:python|py)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--originals", required=True, help="Originals JSON (list with filename/code)")
    ap.add_argument("--regen", required=True, help="Glob for regenerated JSON files")
    ap.add_argument("--outdir", required=True, help="Directory to write normalized JSONs")
    ap.add_argument("--code-field", default="program_specification", help="Field holding Python (e.g., program_specification)")
    ap.add_argument("--extract-python", action="store_true", help="Extract fenced ```python blocks")
    ap.add_argument("--verified", nargs="*", help="(Optional) Globs for verified-only JSONs to filter indices")
    args = ap.parse_args()

    idx2name = load_original_index_map(args.originals)
    keep_idxs = load_verified_indices(args.verified) if args.verified else None

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    total_files, total_rows = 0, 0
    for fp in glob.glob(args.regen):
        obj = json.loads(Path(fp).read_text(encoding="utf-8"))
        rows = (obj.get("specifications") or
                obj.get("results") or
                (obj if isinstance(obj, list) else []))

        normalized = []
        for i, r in enumerate(rows, start=1):
            if not isinstance(r, dict):
                continue
            if keep_idxs and i not in keep_idxs:
                continue
            src = idx2name.get(i)
            if not src:
                # no filename for this index in originals → skip
                continue

            raw = r.get(args.code_field) or r.get("regenerated_code") or r.get("code") or ""
            code = extract_python_block(raw) if args.extract_python else (raw or "").strip()

            row = dict(r)  # preserve your metadata
            row["specification_index"] = i
            row["source_file"] = src
            row["regenerated_code"] = code  # normalized field the evaluator expects
            normalized.append(row)

        out_path = outdir / os.path.basename(fp)
        out_path.write_text(json.dumps({"results": normalized}, indent=2, ensure_ascii=False), encoding="utf-8")
        total_files += 1
        total_rows += len(normalized)

    print(f"✅ Normalized {total_files} file(s), {total_rows} row(s) → {outdir}")

if __name__ == "__main__":
    main()
