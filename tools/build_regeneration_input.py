#!/usr/bin/env python
"""
Build a regeneration input dataset from verified-only JSON files.

Goal: convert verification outputs that contain Dafny/spec text into the
generator's expected shape: a flat list where each item has a `code` field.

Usage (Windows cmd):
  python tools\build_regeneration_input.py \
    --input-dir output\verified_only \
    --output data\spec_regeneration_input.json \
    --field specification

Notes:
- --field selects which key in each record contains the spec text. Common
  options: specification, dafny, dafny_code, program, code.
- The script is resilient to different dataset wrappers: list, {data: [...]},
  {programs: [...]}. It skips empty/missing items and logs counts.
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List


def iter_json_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.json"):
        if p.is_file():
            yield p


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"! Skipping {path}: {e}")
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "programs", "items", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]
    print(f"! Unrecognized JSON structure in {path}; expected list or dict with data/programs.")
    return []


def choose_text(d: Dict[str, Any], field: str) -> str | None:
    # Try explicit field first
    v = d.get(field)
    if isinstance(v, str) and v.strip():
        return v
    # Try common alternates
    for alt in ("specification", "dafny", "dafny_code", "program", "code", "text"):
        v = d.get(alt)
        if isinstance(v, str) and v.strip():
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build regeneration input dataset from verified-only JSON files")
    ap.add_argument("--input-dir", default=str(Path("output")/"verified_only"), help="Directory containing verified-only JSON files")
    ap.add_argument("--output", default=str(Path("data")/"spec_regeneration_input.json"), help="Output JSON path for regeneration dataset")
    ap.add_argument("--field", default="specification", help="Record field name that contains the spec text (default: specification)")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_dir.exists():
        print(f"❌ Input directory not found: {in_dir}")
        return 1

    files = list(iter_json_files(in_dir))
    if not files:
        print(f"❌ No JSON files found under {in_dir}")
        return 1

    print(f"📂 Scanning {len(files)} file(s) in {in_dir}")
    out_items: List[Dict[str, Any]] = []
    total_in, total_kept = 0, 0

    for fp in files:
        items = load_dataset(fp)
        total_in += len(items)
        for idx, rec in enumerate(items):
            text = choose_text(rec, args.field)
            if not text:
                continue
            # Keep a minimal, generator-compatible shape
            tid = (
                rec.get("task_id")
                or rec.get("id")
                or rec.get("program_id")
                or f"{len(out_items)+1:03d}"
            )
            fname = (
                rec.get("filename")
                or rec.get("file")
                or f"program_{tid}.dfy"
            )
            out_items.append({
                "task_id": str(tid),
                "filename": str(fname),
                "code": text,
            })
            total_kept += 1

    if not out_items:
        print("❌ No usable records with spec text found. Try adjusting --field.")
        return 1

    out_path.write_text(json.dumps(out_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote {len(out_items)} items (from {total_in} scanned) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
