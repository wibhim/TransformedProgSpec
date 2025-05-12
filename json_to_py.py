import json
import os

# --- CONFIG ---
INPUT_JSON = "transformed_code_dataset.json"
OUTPUT_DIR = "transformed_programs"

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load JSON
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# Save each transformed snippet into a .py file
for i, entry in enumerate(data):
    file_name = entry.get("file_path", f"program_{i}.py").replace("/", "_").replace("\\", "_")
    transformed_code = entry.get("transformed_code", "")
    
    # fallback if file_path isn't usable
    if not file_name.endswith(".py"):
        file_name = f"program_{i}.py"

    out_path = os.path.join(OUTPUT_DIR, file_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(transformed_code)

print(f"\n✅ Exported {len(data)} Python files to folder: {OUTPUT_DIR}")
