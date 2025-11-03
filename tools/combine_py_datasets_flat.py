#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
import hashlib
import random
from pathlib import Path
from typing import List, Tuple, Set

SKIP_DIR_NAMES = {"__pycache__", ".git", ".venv", "venv", ".mypy_cache", ".pytest_cache"}

def is_python_file(p: Path) -> bool:
    return p.is_file() and p.suffix == ".py"

def iter_py_files(root: Path) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune noisy dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py") and not fn.startswith("."):
                files.append(Path(dirpath) / fn)
    return files

def read_text(p: Path) -> str:
    with p.open("r", encoding="utf-8", errors="replace") as f:
        return f.read()

def normalize_code(code: str) -> str:
    """Light normalization for stable hashing: strip trailing spaces, collapse long blank runs."""
    lines = [ln.rstrip() for ln in code.splitlines()]
    text = "\n".join(lines).strip() + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def zero(n: int, width: int) -> str:
    return str(n).zfill(width)

def main():
    ap = argparse.ArgumentParser(
        description="Combine two directories of .py files into a randomized flat dataset: program_001.py, program_002.py, ..."
    )
    ap.add_argument("--in1", required=True, help="First input directory (e.g., your collected programs)")
    ap.add_argument("--in2", required=True, help="Second input directory (e.g., MBPP converted to .py)")
    ap.add_argument("--label1", default="GitHub", help="Source label for --in1 (default: GitHub)")
    ap.add_argument("--label2", default="MBPP", help="Source label for --in2 (default: MBPP)")
    ap.add_argument("--out", required=True, help="Output directory (flat files)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for shuffling (default: 42)")
    ap.add_argument("--limit", type=int, default=None, help="Optional cap on number of items")
    ap.add_argument("--start-index", type=int, default=1, help="Starting index for program IDs (default: 1)")
    ap.add_argument("--dedup", action="store_true", help="If set, skip duplicates by normalized code hash")
    args = ap.parse_args()

    in1 = Path(args.in1).resolve()
    in2 = Path(args.in2).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # 1) Collect files
    src1 = iter_py_files(in1)
    src2 = iter_py_files(in2)

    items: List[Tuple[str, Path]] = []
    items += [(args.label1, p) for p in src1]
    items += [(args.label2, p) for p in src2]

    if not items:
        print("No .py files found in either directory.", file=sys.stderr)
        sys.exit(1)

    # 2) Shuffle deterministically
    rnd = random.Random(args.seed)
    rnd.shuffle(items)

    # 3) Optionally limit later (after dedup) to keep count accurate
    seen_hashes: Set[str] = set()
    staged: List[Tuple[str, Path, str, str]] = []  # (source_label, path, normalized_code, code_hash)

    for source_label, path in items:
        raw = read_text(path)
        norm = normalize_code(raw)
        code_hash = sha256(norm)
        if args.dedup and code_hash in seen_hashes:
            continue
        if args.dedup:
            seen_hashes.add(code_hash)
        staged.append((source_label, path, norm, code_hash))

    if args.limit is not None and args.limit > 0:
        staged = staged[:args.limit]

    total = len(staged)
    if total == 0:
        print("No items to write after filtering/dedup/limit.", file=sys.stderr)
        sys.exit(1)

    width = max(3, len(str(args.start_index + total - 1)))

    # 4) Write flat files + manifest
    manifest_path = out / "manifest.jsonl"
    written = 0
    with manifest_path.open("w", encoding="utf-8") as mf:
        for i, (source_label, path, norm, code_hash) in enumerate(staged, start=args.start_index):
            program_id = f"program_{zero(i, width)}"
            dst = out / f"{program_id}.py"
            # Write normalized code
            dst.write_text(norm if norm.endswith("\n") else norm + "\n", encoding="utf-8")

            # Relative original path (from the appropriate root)
            if source_label == args.label1:
                rel = str(path.relative_to(in1))
            else:
                rel = str(path.relative_to(in2))

            rec = {
                "program_id": program_id,
                "source": source_label,
                "original_path": rel,
                "original_abs_path": str(path),
                "code_sha256": code_hash,
                "seed": args.seed
            }
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"Combined {written} files into: {out}")
    print(f"- Flat files named program_XXX.py")
    print(f"- Manifest written to: {manifest_path}")
    if args.dedup:
        print(f"- De-duplication by code hash enabled (unique items written: {written})")

if __name__ == "__main__":
    main()
