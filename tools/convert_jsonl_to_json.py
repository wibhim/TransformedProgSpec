# convert_jsonl_to_json.py
import json

IN  = "dataset_filtered.jsonl"
OUT = "datasets/dataset_filtered.json"

data = []
with open(IN, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Converted {len(data)} entries to {OUT}")
