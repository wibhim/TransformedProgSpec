import json
import os
import argparse

def json_to_code_only(json_file, output_dir="output_py"):
    os.makedirs(output_dir, exist_ok=True)

    with open(json_file, "r", encoding="utf-8") as f:
        try:
            # If the file is a JSON array
            data = json.load(f)
        except json.JSONDecodeError:
            # If it's JSONL (one JSON object per line)
            f.seek(0)
            data = [json.loads(line) for line in f if line.strip()]

    # If single object, wrap into list
    if isinstance(data, dict):
        data = [data]

    for task in data:
        task_id = task.get("task_id", "unknown")
        code = task.get("code", "").strip()

        if not code:
            continue

        # Save only the code
        filename = f"program_{str(task_id).zfill(3)}.py"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as out_f:
            out_f.write(code + "\n")

        print(f"Saved {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON/JSONL dataset to .py files (code only)")
    parser.add_argument("--in", dest="json_file", required=True, help="Path to JSON/JSONL dataset file")
    parser.add_argument("--out", dest="output_dir", default="output_py", help="Directory to save Python files")
    args = parser.parse_args()

    json_to_code_only(args.json_file, args.output_dir)
