#!/usr/bin/env python
"""
Enhanced data collection script for the Python to Dafny Formal Verification Pipeline.
This script collects Python programs from multiple GitHub repositories to build a comprehensive
dataset for formal specification generation and verification.

Features:
- Collects from multiple repositories in a single run
- Tracks progress and supports resuming interrupted collections
- Filters programs by criteria such as size and complexity
- Maintains a count of collected programs toward the target goal
- Automatically handles GitHub API rate limits
"""

import os
import re
import ast
import json
import time
import argparse
from datetime import datetime
from github import Github
from github.GithubException import RateLimitExceededException
from config.settings import CONFIG

# --- CONFIG ---
GITHUB_CONFIG = CONFIG["github"]
TOKEN_FILE = GITHUB_CONFIG["token_file"]
OUTPUT_DIR = os.path.join(CONFIG["BASE_DIR"], "output", "collected_programs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "collection_progress.json")
TARGET_COUNT = 200  # Target number of programs to collect (20 from each of 10 repos)
MAX_FILES_PER_REPO = 20  # Maximum files to collect from a single repository

# Repository recommendations - complex Python projects
RECOMMENDED_REPOS = [
    "django/django",           # Web framework
    "pallets/flask",           # Web framework
    "scikit-learn/scikit-learn", # Machine learning
    "pandas-dev/pandas",       # Data analysis
    "pytorch/pytorch",         # Deep learning
    "ansible/ansible",         # Automation
    "TheAlgorithms/Python",    # Various algorithms implementations
    "tiangolo/fastapi",        # API framework
    "Garvit244/Leetcode",      # LeetCode solutions
    "psf/requests"             # HTTP library
]

# Load GitHub token
try:
    with open(TOKEN_FILE, "r") as f:
        GITHUB_TOKEN = f.read().strip()
except FileNotFoundError:
    print(f"⚠️ GitHub token file not found at: {TOKEN_FILE}")
    GITHUB_TOKEN = input("Enter your GitHub API token: ")

# --- Parse command-line arguments ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="Collect Python programs from multiple GitHub repositories")
    parser.add_argument("--repos", type=str, nargs='+', 
                        help="GitHub repositories in the format 'owner/repo' (default: use recommended repos)")
    parser.add_argument("--target", type=int, default=TARGET_COUNT,
                        help=f"Target number of programs to collect (default: {TARGET_COUNT})")
    parser.add_argument("--max-per-repo", type=int, default=MAX_FILES_PER_REPO,
                        help=f"Maximum files to collect from each repository (default: {MAX_FILES_PER_REPO})")
    parser.add_argument("--min-lines", type=int, default=10,
                        help="Minimum number of lines for a program to be included (default: 10)")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help=f"Directory to save collected programs (default: {OUTPUT_DIR})")
    parser.add_argument("--continue", action="store_true", dest="continue_collection",
                        help="Continue from previous collection progress")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: collect only a few files from each repository")
    return parser.parse_args()

# --- Helper functions ---
def ensure_dir_exists(directory):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)
    return directory

def load_progress():
    """Load progress from previous collection."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Progress file is corrupted. Starting fresh.")
            return {"collected_count": 0, "processed_repos": {}, "last_updated": datetime.now().isoformat()}
    return {"collected_count": 0, "processed_repos": {}, "last_updated": datetime.now().isoformat()}

def save_progress(progress):
    """Save collection progress."""
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    return True

def is_complex_enough(content, min_lines=10):
    """Check if the Python code is complex enough to be worth including."""
    lines = content.split('\n')
    non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    
    # Check minimum line count (excluding comments and empty lines)
    if len(non_empty_lines) < min_lines:
        return False
    
    try:
        # Parse the AST to analyze the code structure
        tree = ast.parse(content)
        
        # Count function definitions and class definitions
        func_count = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        class_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        # Check if there's at least one function or class
        if func_count + class_count == 0:
            return False
        
        # Count control structures (if/for/while statements)
        if_count = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
        loop_count = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
          # More complex programs tend to have more control structures
        complexity_score = func_count * 2 + class_count * 3 + if_count + loop_count
        
        # Higher threshold for more representative programs
        return complexity_score >= 5  # We want more complex, representative programs
    
    except SyntaxError:
        # Skip files with syntax errors
        return False

def handle_rate_limit(g, reset_buffer=60):
    """Handle GitHub API rate limit by waiting if needed."""
    rate_limit = g.get_rate_limit()
    core_limit = rate_limit.core
    
    if core_limit.remaining == 0:
        reset_time = core_limit.reset.timestamp()
        sleep_time = reset_time - time.time() + reset_buffer  # Add buffer to be safe
        
        if sleep_time > 0:
            print(f"⏱️ GitHub API rate limit reached. Sleeping for {sleep_time:.0f} seconds until {core_limit.reset}")
            time.sleep(sleep_time)
    
    # Still have some requests left, but let's print out the status
    else:
        print(f"📊 GitHub API requests remaining: {core_limit.remaining}/{core_limit.limit}")

def extract_function_name(code):
    """Extract function or class name from Python code."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
            elif isinstance(node, ast.ClassDef):
                return node.name
        return None
    except SyntaxError:
        return None

# --- Main function to collect Python files ---
def collect_from_repo(repo_name, g, output_dir, max_files=MAX_FILES_PER_REPO, min_lines=10, progress=None, test_mode=False):
    """Collect Python files from a specific repository."""
    try:
        print(f"\n🔍 Collecting Python files from: {repo_name}")
        
        # Check if we have already processed this repo
        if progress and repo_name in progress["processed_repos"]:
            processed_files = progress["processed_repos"][repo_name]
            print(f"↩️ Resuming collection for {repo_name}, already processed {len(processed_files)} files")
        else:
            processed_files = []
            if progress:
                progress["processed_repos"][repo_name] = processed_files
        
        # Connect to repo
        repo = g.get_repo(repo_name)
        
        # Create a directory for this repo
        repo_output_dir = os.path.join(output_dir, repo_name.replace("/", "_"))
        os.makedirs(repo_output_dir, exist_ok=True)
          # Track collection
        collected_count = 0
        collected_function_types = set()  # Track function types to ensure diversity
        contents = repo.get_contents("")
        print(f"📂 Found {len(contents)} items in the root directory")
        
        # Limit early for testing
        if test_mode:
            max_files = min(10, max_files)
        
        # Get all Python files in the repo
        while contents and collected_count < max_files:
            try:
                file_content = contents.pop(0)
                
                # Skip this file if already processed
                if file_content.path in processed_files:
                    continue
                
                # Add to processed list immediately to avoid repeats if an error occurs
                processed_files.append(file_content.path)
                if progress:
                    save_progress(progress)
                
                # Process directories recursively
                if file_content.type == "dir":
                    if not any(exclude in file_content.path for exclude in ['test', 'docs', 'example', 'vendor']):
                        try:
                            dir_contents = repo.get_contents(file_content.path)
                            contents.extend(dir_contents)
                        except Exception as e:
                            print(f"  ⚠️ Error accessing directory {file_content.path}: {e}")
                
                # Process Python files
                elif file_content.path.endswith(".py"):
                    try:
                        # Get file content
                        code_content = file_content.decoded_content.decode('utf-8', errors='replace')
                          # Skip if not complex enough
                        if not is_complex_enough(code_content, min_lines):
                            continue
                        
                        # Create a descriptive filename
                        function_name = extract_function_name(code_content) or "unknown"
                        
                        # For representative collection, try to ensure diversity by file path pattern
                        file_type = file_content.path.split("/")[-2] if "/" in file_content.path else "root"
                        
                        # Skip if we already have enough of this file type (ensures diversity)
                        if collected_count >= 10 and file_type in collected_function_types and len(collected_function_types) >= 5:
                            continue
                        
                        # Add this file type to our collected types
                        collected_function_types.add(file_type)
                        
                        safe_path = re.sub(r'[\\/*?:"<>|]', "_", file_content.path)
                        file_id = f"{repo_name.replace('/', '_')}_{safe_path}"
                        
                        # Prepare metadata and save
                        file_data = {
                            "repo": repo_name,
                            "file_path": file_content.path,
                            "file_name": file_content.name,
                            "download_url": file_content.download_url,
                            "size_bytes": file_content.size,
                            "function_name": function_name,
                            "code": code_content
                        }
                        
                        # Save to JSON file
                        output_filename = os.path.join(repo_output_dir, f"{file_id}.json")
                        with open(output_filename, "w", encoding="utf-8") as f:
                            json.dump(file_data, f, indent=2, ensure_ascii=False)
                        
                        collected_count += 1
                        print(f"✅ [{collected_count}/{max_files}] Collected: {file_content.path}")
                        
                        # Update progress
                        if progress:
                            progress["collected_count"] += 1
                            save_progress(progress)
                        
                        # Check if we've hit GitHub's rate limit
                        if collected_count % 10 == 0:
                            handle_rate_limit(g)
                    
                    except Exception as e:
                        print(f"  ❌ Error processing file {file_content.path}: {e}")
            
            except RateLimitExceededException:
                print(f"⏱️ Rate limit exceeded while processing {repo_name}")
                handle_rate_limit(g)
            except Exception as e:
                print(f"  ⚠️ Error with item {file_content.path if 'file_content' in locals() else 'unknown'}: {e}")
        
        return collected_count
    
    except Exception as e:
        print(f"❌ Failed to process repository {repo_name}: {e}")
        return 0

# --- Main execution ---
def main():
    """Main function to coordinate collection from multiple repositories."""
    start_time = time.time()
    args = parse_arguments()
    
    # Set up directories
    output_dir = args.output_dir
    ensure_dir_exists(output_dir)
    
    # Load or create progress tracking
    progress = None
    if args.continue_collection:
        progress = load_progress()
        print(f"📊 Continuing collection. Already collected: {progress['collected_count']} programs")
    else:
        progress = {"collected_count": 0, "processed_repos": {}, "last_updated": datetime.now().isoformat()}
        save_progress(progress)
    
    # Initialize GitHub API client
    g = Github(GITHUB_TOKEN)
    
    # Get repositories to process
    repos_to_process = args.repos if args.repos else RECOMMENDED_REPOS
      # Calculate how many files per repo to reach target
    remaining_target = args.target - progress["collected_count"]
    if remaining_target <= 0:
        print(f"🎉 Target of {args.target} programs has already been reached!")
        return
    files_per_repo = min(args.max_per_repo, remaining_target // len(repos_to_process) + 1)
    print(f"🎯 Target: {args.target} programs (collecting {files_per_repo} representative programs per repository)")
    print(f"📊 Strategy: Selecting diverse, complex programs from different modules in each repository")
    
    # Process each repository
    total_collected = progress["collected_count"]
    for repo_name in repos_to_process:
        # Skip if we've already reached the target
        if total_collected >= args.target:
            break
            
        # Check rate limit before starting a new repo
        handle_rate_limit(g)
        
        # Collect from this repo
        print(f"\n=== Processing repository: {repo_name} ===")
        
        files_needed = min(files_per_repo, args.target - total_collected)
        collected = collect_from_repo(
            repo_name, g, output_dir, 
            max_files=files_needed,
            min_lines=args.min_lines,
            progress=progress,
            test_mode=args.test
        )
        
        total_collected += collected
        print(f"📊 Progress: {total_collected}/{args.target} programs collected")
    
    # Final report
    elapsed_time = time.time() - start_time
    print(f"\n✅ Collection complete! {total_collected}/{args.target} programs collected")
    print(f"⏱️ Total execution time: {elapsed_time:.2f} seconds")
    print(f"💾 Programs saved to {output_dir}")

if __name__ == "__main__":
    main()
