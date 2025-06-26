import ast
import json
import argparse
from github import Github
from config.settings import CONFIG

# --- CONFIG ---
GITHUB_CONFIG = CONFIG["github"]
TOKEN_FILE = GITHUB_CONFIG["token_file"]
OUTPUT_JSON = GITHUB_CONFIG["output_json"]
TARGET_REPO = GITHUB_CONFIG["target_repo"]
MAX_FILES = GITHUB_CONFIG["max_files"]

# Load GitHub token
try:
    with open(TOKEN_FILE, "r") as f:
        GITHUB_TOKEN = f.read().strip()
except FileNotFoundError:
    print(f"⚠️ GitHub token file not found at: {TOKEN_FILE}")
    GITHUB_TOKEN = input("Enter your GitHub API token: ")

# --- Parse command-line arguments to override config ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="Collect Python code from GitHub repositories")
    parser.add_argument("--repo", type=str, default=TARGET_REPO,
                        help=f"GitHub repository in the format 'owner/repo' (default: {TARGET_REPO})")
    parser.add_argument("--max-files", type=int, default=MAX_FILES,
                        help=f"Maximum number of files to collect (default: {MAX_FILES})")
    parser.add_argument("--output", type=str, default=OUTPUT_JSON,
                        help=f"Output JSON file path (default: {OUTPUT_JSON})")
    return parser.parse_args()

# Parse arguments
args = parse_arguments()
target_repo = args.repo
max_files = args.max_files
output_json = args.output

print(f"🔍 Collecting Python files from: {target_repo}")
print(f"📊 Max files to collect: {max_files}")

# --- Connect to GitHub ---
g = Github(GITHUB_TOKEN)
repo = g.get_repo(target_repo)

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
py_files = get_python_files(repo, max_files=max_files)

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
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(dataset)} Python files to '{output_json}'")