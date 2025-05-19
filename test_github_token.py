import ast
import json
from github import Github
"""
PyGithub is a Python library that provides a convenient interface to work with GitHub. It allows you to:
  • Authenticate with GitHub using tokens.
  • Access user profiles, repositories, issues, pull requests, and gists.
  • Create, update, or delete GitHub content programmatically.
  • Automate GitHub workflows (e.g., managing issues, adding labels, commenting).
"""


# --- CONFIG ---
GITHUB_TOKEN = "Token Github"  # Replace with your real token
TARGET_REPO = "Any repo name"     # Change to any repo you like
OUTPUT_JSON = "python_code_dataset_with_metadata.json"
# Currently limiting the dataset to 5 Python files for testing or small-scale extraction.
# Consider increasing this value or turning it into a command-line/config parameter
# (e.g., via argparse or environment variable) when scaling to larger repositories.
MAX_FILES = 5

# --- Connect to GitHub ---
g = Github(GITHUB_TOKEN)
repo = g.get_repo(TARGET_REPO)

# --- Find Python files ---
# This function looks good for now. It recursively traverses the repository contents
# to find .py files, up to a maximum specified by max_files.
#
# Example output of `files` after running get_python_files():
# files = [
#     ContentFile(path='main.py', name='main.py', type='file', ...),
#     ContentFile(path='utils/helpers.py', name='helpers.py', type='file', ...),
#     ContentFile(path='scripts/setup.py', name='setup.py', type='file', ...)
# ]
# Each item is a GitHub ContentFile object with metadata like path, name, type, size, etc.
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
# dataset is a list of dictionaries, where each dictionary represents metadata
# and content for one .py file
# You are collecting structured records of similar type (here: .py file metadata).
# You plan to export it to JSON (which naturally supports lists and dicts).
# You want to perform transformations, filtering, or indexing later.
dataset = []
# list of GitHub ContentFile objects
py_files = get_python_files(repo)

# This block fetches and decodes each `.py` file’s content,
# collects metadata (file name, path, size, etc.),
# and appends it to a list. If any error occurs, it prints a warning.
for file in py_files:
    try:
        # Attempts to process each file.
        # If anything goes wrong (e.g., file not readable),
        # it will jump to the `except` block.
        #
        # file.decoded_content gives you the raw content of the file (as bytes).
        # .decode() converts it into a human-readable UTF-8 string (i.e., the actual Python source code).
        # So this line extracts the source code of the Python file.
        content = file.decoded_content.decode()

        # Collect metadata
        # It builds a dictionary `file_data`
        file_data = {
            "repo": repo.full_name,
            "file_path": file.path,
            "file_name": file.name,
            "download_url": file.download_url,
            "size_bytes": file.size,
            "code": content
        }

        # Adds the metadata dictionary for this file to the
        # overall `dataset` list.
        dataset.append(file_data)
        print(f"✅ Collected: {file.path}")

    except Exception as e:
        print(f"❌ Failed to download {file.path}: {e}")

# --- Save to JSON ---
# script is responsible for saving the collected dataset to a JSON file
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(dataset)} Python files to '{OUTPUT_JSON}'")