import json
import csv
import sys
from pathlib import Path

def json_to_csv(input_path, output_path):
    # Load JSON (handles both dict with "programs" and raw list)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Detect program list
    if isinstance(data, dict):
        programs = data.get("programs") or data.get("items") or []
        if not programs:
            # try first list in dict
            for v in data.values():
                if isinstance(v, list):
                    programs = v
                    break
    else:
        programs = data

    if not programs:
        print("No program entries found in JSON.")
        return

    # Collect all keys
    all_keys = set()
    for p in programs:
        if isinstance(p, dict):
            all_keys.update(p.keys())
    all_keys = sorted(all_keys)

    # Compute summary counts
    verified = 0
    parse_errors = 0
    compile_errors = 0
    verification_errors = 0
    for p in programs:
        et = p.get("error_type") or p.get("status") or ""
        if p.get("verified") is True or et in ("verified", "success", "ok", "passed"):
            verified += 1
        elif "parse" in str(et).lower():
            parse_errors += 1
        elif "compile" in str(et).lower():
            compile_errors += 1
        elif "verification" in str(et).lower():
            verification_errors += 1

    summary = {
        "id": "SUMMARY",
        "total_programs": len(programs),
        "verified_count": verified,
        "parse_error_count": parse_errors,
        "compile_error_count": compile_errors,
        "verification_error_count": verification_errors,
        "failed_count": len(programs) - verified,
        "verification_rate": round(verified / len(programs), 3) if programs else 0.0,
    }
    all_keys = sorted(set(all_keys).union(summary.keys()))

    # Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        for p in programs:
            if isinstance(p, dict):
                writer.writerow({k: p.get(k, "") for k in all_keys})
        writer.writerow(summary)

    print(f"Converted {len(programs)} records + summary into {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python json_to_csv_with_summary.py input.json output.csv")
        sys.exit(1)

    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2])
    json_to_csv(inp, outp)
