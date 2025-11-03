#!/usr/bin/env python
"""
Filter verification JSON files to only keep verified entries, optionally merging or splitting per input.

Key features
------------
- Default: merge all inputs into one JSON (no dedup unless requested).
- Split mode: --split-dir writes ONE output per input file (same count).
- Preserve filename: --preserve-name keeps the same basename (no "_verified" suffix).
- Keep only selected fields in JSON: --json-keep (always preserves 'transformation' and identity fields if present).

Identity fields we attempt to preserve (if present):
- source_file, file_path, filename, task_id, program_id, specification_index

Heuristic for "verified":
- Boolean fields: verified, is_verified, verification_passed, verifies == True
- String status fields: status, verification, verify_status, verifier_status, verification_status in {verified, success, passed, ok, true}
- Nested common path: verification.status
- Dafny-ish counters: verified_count > 0
Override with --verified-key / --verified-value

Examples
--------
# Merge: keep every verified row from many files (no dedup)
python filter_verified.py -i output/*.json -o output/all_verified.json --csv output/all_verified.csv

# Split: one verified file per input, same basename, plus per-file CSV
python filter_verified.py -i output/*.json --split-dir output/verified --preserve-name --split-csv-dir output/verified_csv --keep file_path task_id transformation program_specification

# Split + JSON field selection (keep just a few fields in each JSON result)
python filter_verified.py -i output/*.json --split-dir out/verified --preserve-name --json-keep source_file specification_index transformation program_specification
"""

import argparse, csv, glob, json, os, re, sys
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple, Union

Truthy = {"true", "1", "yes", "y", "ok", "passed", "pass", "success", "succeeded", "verified", "verifies"}
HeuristicFieldsBool = {"verified", "is_verified", "verification_passed", "verifies"}
HeuristicFieldsStr = {"status", "verification", "verify_status", "verifier_status", "verification_status"}
HeuristicValuesStr = {"verified", "success", "passed", "ok", "true"}

def read_json_anyshape(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return raw, {"_container": "list"}
    if isinstance(raw, dict):
        for key in ("results", "data", "programs", "items"):
            if key in raw and isinstance(raw[key], list):
                return raw[key], {"_container": key, "_root": raw}
        if all(isinstance(v, dict) for v in raw.values()):
            return list(raw.values()), {"_container": "dict_values", "_root": raw}
    raise ValueError(f"Unsupported JSON structure in {path}: {type(raw)}")

def get_nested(d: Dict[str, Any], dotted: str, default=None):
    cur = d
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur

def to_boolish(x: Any) -> Union[bool, None]:
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in Truthy:
            return True
        if s in {"false", "0", "no", "n", "fail", "failed", "error"}:
            return False
    return None

def record_verified(record: Dict[str, Any], forced_key: str = None, forced_value: str = None) -> bool:
    if forced_key:
        val = get_nested(record, forced_key, None)
        if forced_value is None:
            tb = to_boolish(val)
            if tb is not None:
                return tb
            return bool(val)
        else:
            want = forced_value.strip().lower()
            got = str(val).strip().lower() if val is not None else ""
            return got == want
    for k in HeuristicFieldsBool:
        if k in record:
            tb = to_boolish(record[k])
            if tb is True:
                return True
    v = get_nested(record, "verification.status", None)
    if isinstance(v, str) and v.strip().lower() in HeuristicValuesStr:
        return True
    for k in HeuristicFieldsStr:
        if k in record and isinstance(record[k], str):
            if record[k].strip().lower() in HeuristicValuesStr:
                return True
    if record.get("verified_count", 0):
        try:
            return int(record.get("verified_count", 0)) > 0
        except Exception:
            pass
    if "verifies" in record:
        tb = to_boolish(record["verifies"])
        if tb is True:
            return True
    return False

def infer_transformation_name(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    name = re.sub(r"(verification|results|output|verified|specs?)", "", name, flags=re.I)
    name = re.sub(r"[_\-\.]+", "_", name).strip("_")
    return name or base

IDENTITY_KEYS = ("source_file", "file_path", "filename", "task_id", "program_id", "specification_index")

def normalize_record(rec: Dict[str, Any], transform: str, src_path: str) -> Dict[str, Any]:
    out = dict(rec)
    out.setdefault("transformation", transform)
    out.setdefault("source_json", src_path)
    for k in IDENTITY_KEYS:
        if k not in out:
            for cand in ("meta."+k, "metadata."+k, "program."+k):
                val = get_nested(rec, cand, None)
                if val is not None:
                    out[k] = val
                    break
    return out

def collect_verified(inputs: List[str], forced_key: str = None, forced_value: str = None, invert: bool = False):
    verified, rejected = [], []
    for path in inputs:
        try:
            records, _ = read_json_anyshape(path)
        except Exception as e:
            rejected.append({"source_json": path, "error": str(e)})
            continue
        tname = infer_transformation_name(path)
        for rec in records:
            ok = record_verified(rec, forced_key, forced_value)
            if invert:
                ok = not ok
            if ok:
                verified.append(normalize_record(rec, tname, path))
            else:
                rej = normalize_record(rec, tname, path)
                rejected.append(rej)
    return verified, rejected

def build_key(record: Dict[str, Any], keys: List[str]) -> str:
    parts = []
    for k in keys:
        k = k.strip()
        if not k:
            continue
        parts.append(str(get_nested(record, k, record.get(k, ""))))
    return "§".join(parts)

def dedup_rows(rows: List[Dict[str, Any]], keys: List[str], prefer: str = "first", prefer_field: str = None) -> List[Dict[str, Any]]:
    if not keys:
        return rows
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        k = build_key(r, keys)
        if k not in out:
            out[k] = r
        else:
            if prefer == "last":
                out[k] = r
            elif prefer == "longer" and prefer_field:
                a = out[k].get(prefer_field, "") or ""
                b = r.get(prefer_field, "") or ""
                if len(str(b)) > len(str(a)):
                    out[k] = r
            # default "first": keep existing
    return list(out.values())

def write_json(path: str, payload: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

def write_csv(path: str, rows: List[Dict[str, Any]], keep: List[str] = None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if keep:
                writer.writerow(keep)
        return
    if keep:
        fieldnames = keep
    else:
        keys = set()
        for r in rows:
            keys.update(r.keys())
        fieldnames = sorted(keys)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def select_fields(row: Dict[str, Any], json_keep: List[str] = None) -> Dict[str, Any]:
    if not json_keep:
        return row
    base = {}
    # Always try to preserve identity and transformation if present
    for k in set(json_keep) | set(IDENTITY_KEYS) | {"transformation"}:
        if k in row:
            base[k] = row[k]
    return base

def write_per_input(input_path: str,
                    rows: List[Dict[str, Any]],
                    rejected_rows: List[Dict[str, Any]],
                    out_dir: str,
                    csv_dir: str = None,
                    keep_cols: List[str] = None,
                    predicate_meta: Dict[str, Any] = None,
                    preserve_name: bool = False,
                    json_keep: List[str] = None):
    base = os.path.basename(input_path)
    stem, ext = os.path.splitext(base)
    os.makedirs(out_dir, exist_ok=True)
    if preserve_name:
        out_json = os.path.join(out_dir, base)  # same basename
    else:
        out_json = os.path.join(out_dir, f"{stem}_verified{ext or '.json'}")

    rows_this = [r for r in rows if r.get("source_json") == input_path]
    rej_this = [r for r in rejected_rows if r.get("source_json") == input_path]

    processed = [select_fields(r, json_keep) for r in rows_this]

    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "input": input_path,
            "count_verified": len(processed),
            "count_rejected": len(rej_this),
            "predicate": predicate_meta or {},
        },
        "results": processed
    }
    write_json(out_json, payload)

    if csv_dir:
        os.makedirs(csv_dir, exist_ok=True)
        out_csv = os.path.join(csv_dir, f"{stem}_verified.csv")
        write_csv(out_csv, processed, keep=keep_cols)
    return out_json

def main(argv=None):
    p = argparse.ArgumentParser(description="Filter verification JSONs to only verified (or only rejected with --invert)")
    p.add_argument("-i", "--inputs", nargs="+", required=True, help="Input JSON files or globs (e.g., out/*.json)")
    p.add_argument("-o", "--output", help="Output JSON for merged verified records (omit when using --split-dir)")
    p.add_argument("--csv", help="Optional CSV summary output (merged mode). If --split-dir is used and you also want per-file CSVs, use --split-csv-dir")
    p.add_argument("--verified-key", help="Force a specific field to check (dot-notation for nested)")
    p.add_argument("--verified-value", help="Value to match for --verified-key (case-insensitive). For booleans use true/false")
    p.add_argument("--invert", action="store_true", help="Keep non-verified instead (i.e., filter out verified)")
    p.add_argument("--keep", nargs="*", help="Columns to keep (for CSV only). Example: --keep source_file specification_index transformation program_specification")
    # Optional dedup (merged mode)
    p.add_argument("--dedup-keys", nargs="*", help="Optional list of keys (dot-notation) to deduplicate on. Default: no dedup")
    p.add_argument("--dedup-prefer", choices=["first","last","longer"], default="first", help="When duplicates occur, which to keep")
    p.add_argument("--dedup-prefer-field", help="When using --dedup-prefer longer, compare this field length (e.g., program_specification)")
    # Split mode
    p.add_argument("--split-dir", help="Write one output JSON per input into this directory (filename[_verified].json).")
    p.add_argument("--split-csv-dir", help="(Optional) If set with --split-dir, also write one CSV per input into this directory.")
    p.add_argument("--preserve-name", action="store_true", help="With --split-dir, keep the same basename as the input (no _verified suffix).")
    p.add_argument("--json-keep", nargs="*", help="For JSON outputs, keep only these fields (always preserves identity fields and 'transformation' if present).")
    args = p.parse_args(argv)

    # Expand globs
    expanded: List[str] = []
    for pat in args.inputs:
        hits = glob.glob(pat)
        if not hits:
            print(f"⚠️ No matches for input: {pat}")
        expanded.extend(hits)
    if not expanded:
        print("No input files found.", file=sys.stderr)
        return 2

    verified, rejected = collect_verified(expanded, args.verified_key, args.verified_value, args.invert)

    # Split-per-input branch
    if args.split_dir:
        predicate_meta = {
            "forced_key": args.verified_key,
            "forced_value": args.verified_value,
            "invert": args.invert
        }
        for ip in expanded:
            outp = write_per_input(
                input_path=ip,
                rows=verified,
                rejected_rows=rejected,
                out_dir=args.split_dir,
                csv_dir=args.split_csv_dir,
                keep_cols=args.keep,
                predicate_meta=predicate_meta,
                preserve_name=args.preserve_name,
                json_keep=args.json_keep
            )
            print(f"✅ {ip} → {outp}")
        return 0

    # Merged mode
    if not args.output:
        print("When not using --split-dir, you must provide --output for merged JSON.", file=sys.stderr)
        return 2

    # Optional dedup
    if args.dedup_keys:
        verified = dedup_rows(verified, args.dedup_keys, prefer=args.dedup_prefer, prefer_field=args.dedup_prefer_field)

    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "inputs": expanded,
            "count_verified": len(verified),
            "count_rejected": len(rejected),
            "predicate": {
                "forced_key": args.verified_key,
                "forced_value": args.verified_value,
                "invert": args.invert
            },
            "dedup": {
                "keys": args.dedup_keys,
                "prefer": args.dedup_prefer,
                "prefer_field": args.dedup_prefer_field,
            }
        },
        "results": [select_fields(r, args.json_keep) for r in verified]
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    write_json(args.output, payload)
    print(f"✅ Saved {len(verified)} records → {args.output}")
    if args.csv:
        write_csv(args.csv, verified, keep=args.keep)
        print(f"📄 CSV written → {args.csv}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
