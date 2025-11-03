#!/usr/bin/env python3
"""
filter_if_else_loop.py (revised with switch/case support)

Detect presence (not counts) of:
  - any IF (only-if or if-else, including elif),
  - any loop (for/while),
  - any switch/case (Python 3.10+ match/case),
and write filtered subsets + a summary.

Usage:
    python filter_if_else_loop.py --input combined.json --out-dir output_folder
"""

import ast
import json
import argparse
from pathlib import Path


def parse_tree(code: str):
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def has_any_if(code: str) -> bool:
    """True if the code has at least one ast.If (includes only-if, elif, and if-else)."""
    tree = parse_tree(code)
    if not tree:
        return False
    return any(isinstance(node, ast.If) for node in ast.walk(tree))


def has_any_loop(code: str) -> bool:
    """True if the code contains at least one for/while loop."""
    tree = parse_tree(code)
    if not tree:
        return False
    return any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))


def has_any_switch_case(code: str) -> bool:
    """
    True if the code contains at least one Python 3.10+ match/case.
    Uses ast.Match when available (Python >= 3.10). On older Python,
    ast.Match may not exist—then this returns False.
    """
    if not hasattr(ast, "Match"):
        return False  # Running on Python < 3.10; cannot have match/case in valid code
    tree = parse_tree(code)
    if not tree:
        return False
    return any(isinstance(node, ast.Match) for node in ast.walk(tree))


def main():
    parser = argparse.ArgumentParser(description="Filter programs by presence of IF, loops, and switch/case.")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Path to combined dataset JSON.")
    parser.add_argument("--out-dir", "-o", type=Path, required=True, help="Output directory path.")
    args = parser.parse_args()

    input_path: Path = args.input
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return

    filtered_if_any = []
    filtered_loops = []
    filtered_both_if_loops = []
    filtered_switch = []
    filtered_switch_loops = []

    for entry in data:
        code = entry.get("code", "") or ""

        any_if = has_any_if(code)
        any_loop = has_any_loop(code)
        any_switch = has_any_switch_case(code)

        if any_if:
            filtered_if_any.append(entry)
        if any_loop:
            filtered_loops.append(entry)
        if any_if and any_loop:
            filtered_both_if_loops.append(entry)

        if any_switch:
            filtered_switch.append(entry)
        if any_switch and any_loop:
            filtered_switch_loops.append(entry)

    # File paths
    out_if = out_dir / "filtered_if_else.json"  # now means ANY if (only-if or if-else)
    out_loops = out_dir / "filtered_loops.json"
    out_both_if_loops = out_dir / "filtered_if_else_and_loops.json"
    out_switch = out_dir / "filtered_switch_case.json"
    out_switch_loops = out_dir / "filtered_switch_case_and_loops.json"

    # Write outputs
    out_if.write_text(json.dumps(filtered_if_any, ensure_ascii=False, indent=2), encoding="utf-8")
    out_loops.write_text(json.dumps(filtered_loops, ensure_ascii=False, indent=2), encoding="utf-8")
    out_both_if_loops.write_text(json.dumps(filtered_both_if_loops, ensure_ascii=False, indent=2), encoding="utf-8")
    out_switch.write_text(json.dumps(filtered_switch, ensure_ascii=False, indent=2), encoding="utf-8")
    out_switch_loops.write_text(json.dumps(filtered_switch_loops, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "total_programs": len(data),
        "programs_with_any_if": len(filtered_if_any),
        "programs_with_loops": len(filtered_loops),
        "programs_with_both_if_and_loops": len(filtered_both_if_loops),
        "programs_with_switch_case": len(filtered_switch),
        "programs_with_switch_case_and_loops": len(filtered_switch_loops),
        "notes": {
            "if_definition": "Any ast.If counts (including only-if, elif, and if-else).",
            "loops_definition": "Any ast.For or ast.While counts.",
            "switch_case_definition": "Any ast.Match (Python 3.10+) counts.",
            "compat": {
                "filtered_if_else.json": "Now contains ANY if (not just if-else).",
                "new_files": [
                    "filtered_switch_case.json",
                    "filtered_switch_case_and_loops.json"
                ],
            },
            "python_version": "If running on Python < 3.10, 'switch/case' detection always returns False.",
        },
        "output_dir": str(out_dir.resolve()),
        "output_files": {
            "if_else": str(out_if),
            "loops": str(out_loops),
            "both_if_and_loops": str(out_both_if_loops),
            "switch_case": str(out_switch),
            "switch_case_and_loops": str(out_switch_loops),
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
