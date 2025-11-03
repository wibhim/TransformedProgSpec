# save as py_to_json.py
import os
import json
import argparse

def py_to_json(input_dir, output_file, jsonl=True):
    records = []
    for root, _, files in os.walk(input_dir):   # recursive scan
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                code = f.read().strip()

            # Task id from relative path (unique and traceable)
            rel_path = os.path.relpath(fpath, input_dir)
            base = os.path.splitext(rel_path)[0]
            task_id = "".join(ch for ch in base if ch.isdigit()) or base.replace(os.sep, "_")

            rec = {
                "task_id": task_id,
                "filename": rel_path,   # keep relative path
                "code": code
            }
            records.append(rec)

    if jsonl:
        with open(output_file, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Saved {len(records)} records to {output_file} (JSONL)")
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(records)} records to {output_file} (JSON array)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively convert .py files to JSON/JSONL dataset")
    parser.add_argument("--in", dest="input_dir", required=True, help="Root directory containing .py files")
    parser.add_argument("--out", dest="output_file", required=True, help="Output JSON or JSONL file")
    parser.add_argument("--mode", choices=["json", "jsonl"], default="jsonl", help="json = array, jsonl = one JSON per line")
    args = parser.parse_args()

    py_to_json(args.input_dir, args.output_file, jsonl=(args.mode == "jsonl"))
