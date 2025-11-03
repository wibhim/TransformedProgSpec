# add_index_and_mapping.py
import json, csv, sys
from pathlib import Path

INPUT_JSON  = "datasets/sliced_single_eval.json"          # change if needed
OUTPUT_JSON = "datasets/sliced_single_eval_indexed.json"  # new JSON with `index`
MAP_CSV     = "datasets/sliced_single_eval_index_map.csv" # handy mapping table

def load_programs(data):
    if isinstance(data, list):
        return data
    # common containers like {"programs":[...]} or similar
    for k in ("programs", "items", "results", "entries", "cases"):
        if k in data and isinstance(data[k], list):
            return data[k]
    # fallback: first list value in dict
    for v in data.values():
        if isinstance(v, list):
            return v
    raise ValueError("Could not find a list of program entries in the JSON.")

def main():
    in_path = Path(INPUT_JSON)
    data = json.loads(in_path.read_text(encoding="utf-8"))

    programs = load_programs(data)

    # add a 1-based index to each item
    for i, obj in enumerate(programs, start=1):
        obj["index"] = i

    # Save updated JSON
    Path(OUTPUT_JSON).write_text(
        json.dumps(programs if isinstance(data, list) else {**data, "programs": programs}, 
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Build and save a mapping CSV for quick lookup in your thesis
    fields = ["index", "id", "file_name", "file_path", "function", "source_path"]
    with open(MAP_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for obj in programs:
            w.writerow({
                "index": obj.get("index"),
                "id": obj.get("id", ""),
                "file_name": obj.get("file_name", ""),
                "file_path": obj.get("file_path", ""),
                "function": obj.get("function", ""),
                "source_path": obj.get("source_path", ""),
            })

    print(f"Added index to {len(programs)} items.")
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {MAP_CSV}")

if __name__ == "__main__":
    # optional CLI: python add_index_and_mapping.py [in.json] [out.json] [map.csv]
    if len(sys.argv) >= 2:
        INPUT_JSON = sys.argv[1]
    if len(sys.argv) >= 3:
        OUTPUT_JSON = sys.argv[2]
    if len(sys.argv) >= 4:
        MAP_CSV = sys.argv[3]
    main()
