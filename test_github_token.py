import ast
import json
from github import Github

# --- CONFIG ---
GITHUB_TOKEN = "Token Github"  # 🔐 Replace with your real token
TARGET_REPO = "Any repo name"     # 🧠 Change to any repo you like
OUTPUT_JSON = "python_code_dataset_with_metadata.json"
MAX_FILES = 5

# --- Connect to GitHub ---
g = Github(GITHUB_TOKEN)
repo = g.get_repo(TARGET_REPO)

# --- Find Python files ---
def get_python_files(repo, max_files=MAX_FILES):
    files = []
    contents = repo.get_contents("")
    while contents and len(files) < max_files:
        item = contents.pop(0)
        if item.type == "dir":
            contents.extend(repo.get_contents(item.path))
        elif item.path.endswith(".py"):
            files.append(item)
    return files

# --- Collect Code and Metadata ---
dataset = []
py_files = get_python_files(repo)

for file in py_files:
    try:
        content = file.decoded_content.decode()

        # Collect metadata
        file_data = {
            "repo": repo.full_name,
            "file_path": file.path,
            "file_name": file.name,
            "download_url": file.download_url,
            "size_bytes": file.size,
            "code": content
        }

        dataset.append(file_data)
        print(f"✅ Collected: {file.path}")

    except Exception as e:
        print(f"❌ Failed to download {file.path}: {e}")

# --- Save to JSON ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(dataset)} Python files to '{OUTPUT_JSON}'")