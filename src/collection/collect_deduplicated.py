#!/usr/bin/env python
"""
Enhanced data collection script with deduplication support.
Supports incremental collection in batches while preventing duplicates.

Features:
- Content-based deduplication across collection runs
- Batch management and tracking
- Smart repository selection and balancing
- Resume capability for interrupted collections
- Progress tracking and reporting
"""

import os
import re
import ast
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from github import Github
from github.GithubException import RateLimitExceededException

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import CONFIG
from config.repositories import get_all_repos, get_repos_for_strategy, COLLECTION_STRATEGIES
from src.utils.deduplication import ProgramIndex, BatchManager, print_collection_summary

# --- CONFIG ---
GITHUB_CONFIG = CONFIG["github"]
TOKEN_FILE = GITHUB_CONFIG["token_file"]
OUTPUT_DIR = os.path.join(CONFIG["BASE_DIR"], "output", "collected_programs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get repositories from configuration
RECOMMENDED_REPOS = get_all_repos()

# Load GitHub token
try:
    with open(TOKEN_FILE, "r") as f:
        GITHUB_TOKEN = f.read().strip()
except FileNotFoundError:
    print(f"⚠️ GitHub token file not found at: {TOKEN_FILE}")
    GITHUB_TOKEN = input("Enter your GitHub API token: ")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Collect Python programs with deduplication support")
    
    # Basic collection parameters
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Number of programs to collect in this batch (default: 500)")
    parser.add_argument("--target-total", type=int, default=5000,
                        help="Total target number of programs across all batches (default: 5000)")
    parser.add_argument("--min-lines", type=int, default=15,
                        help="Minimum number of lines for a program (default: 15)")
    parser.add_argument("--min-complexity", type=int, default=5,
                        help="Minimum complexity score for a program (default: 5)")
    
    # Repository selection
    parser.add_argument("--repos", type=str, nargs='+',
                        help="Specific repositories to target (default: use strategy-based selection)")
    parser.add_argument("--exclude-repos", type=str, nargs='+', default=[],
                        help="Repositories to exclude from collection")
    parser.add_argument("--strategy", type=str, choices=list(COLLECTION_STRATEGIES.keys()) + ['all'],
                        default='balanced',
                        help="Collection strategy: balanced, algorithms_focused, web_focused, data_science_focused, or all")
    
    # Collection modes
    parser.add_argument("--plan-only", action="store_true",
                        help="Only show the collection plan without executing")
    parser.add_argument("--stats", action="store_true",
                        help="Show collection statistics and exit")
    parser.add_argument("--reset-index", action="store_true",
                        help="Reset the program index (use with caution)")
    
    # Output and debugging
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help=f"Directory to save collected programs (default: {OUTPUT_DIR})")
    parser.add_argument("--test-mode", action="store_true",
                        help="Test mode: collect only a few files for testing")
    
    return parser.parse_args()


def calculate_complexity_score(code_content: str) -> int:
    """
    Calculate a complexity score for the code.
    Returns -1 if the code is invalid.
    """
    try:
        tree = ast.parse(code_content)
        
        # Count different types of nodes
        func_count = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        class_count = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        if_count = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
        loop_count = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
        try_count = len([n for n in ast.walk(tree) if isinstance(n, ast.Try)])
        
        # Weight different constructs
        complexity_score = (
            func_count * 2 + 
            class_count * 3 + 
            if_count + 
            loop_count * 2 +
            try_count * 2
        )
        
        return complexity_score
    except (SyntaxError, ValueError):
        return -1


def is_program_suitable(code_content: str, min_lines: int = 15, min_complexity: int = 5) -> bool:
    """Check if a program meets our collection criteria."""
    # Count non-empty, non-comment lines
    lines = [line.strip() for line in code_content.split('\n')]
    non_empty_lines = [line for line in lines if line and not line.startswith('#')]
    
    if len(non_empty_lines) < min_lines:
        return False
    
    # Check complexity
    complexity = calculate_complexity_score(code_content)
    if complexity < min_complexity:
        return False
    
    return True


def extract_function_name(code: str) -> str:
    """Extract the primary function or class name from code."""
    try:
        tree = ast.parse(code)
        # Look for the first function or class definition
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                return node.name
        return "unknown"
    except (SyntaxError, ValueError):
        return "invalid"


def handle_rate_limit(g, reset_buffer=60):
    """Handle GitHub API rate limit."""
    rate_limit = g.get_rate_limit()
    core_limit = rate_limit.core
    
    if core_limit.remaining < 10:  # Conservative threshold
        if core_limit.remaining == 0:
            reset_time = core_limit.reset.timestamp()
            sleep_time = reset_time - time.time() + reset_buffer
            
            if sleep_time > 0:
                print(f"⏱️ Rate limit reached. Sleeping for {sleep_time:.0f} seconds...")
                time.sleep(sleep_time)
        else:
            print(f"📊 API requests remaining: {core_limit.remaining}/{core_limit.limit}")


def collect_from_repo_deduplicated(repo_name: str, g: Github, output_dir: str, 
                                 index: ProgramIndex, max_files: int = 50, 
                                 min_lines: int = 15, min_complexity: int = 5,
                                 batch_id: int = None, test_mode: bool = False) -> int:
    """
    Collect Python files from a repository with deduplication.
    
    Returns:
        Number of new (non-duplicate) programs collected
    """
    try:
        print(f"\n🔍 Collecting from: {repo_name}")
        
        # Create repository output directory
        repo_output_dir = Path(output_dir) / repo_name.replace("/", "_")
        repo_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Connect to repository
        repo = g.get_repo(repo_name)
        
        # Collection tracking
        collected_count = 0
        processed_count = 0
        duplicate_count = 0
        
        # Get repository contents
        contents = repo.get_contents("")
        
        # Limit for test mode
        if test_mode:
            max_files = min(5, max_files)
        
        print(f"📂 Scanning repository contents...")
        
        while contents and collected_count < max_files:
            try:
                file_content = contents.pop(0)
                
                # Handle directories recursively
                if file_content.type == "dir":
                    # Skip common non-code directories
                    skip_dirs = ['test', 'tests', 'docs', 'doc', 'examples', 'example', 
                               'vendor', 'node_modules', '__pycache__', '.git']
                    if not any(skip in file_content.path.lower() for skip in skip_dirs):
                        try:
                            dir_contents = repo.get_contents(file_content.path)
                            contents.extend(dir_contents)
                        except Exception as e:
                            print(f"  ⚠️ Error accessing directory {file_content.path}: {e}")
                    continue
                
                # Process Python files
                if not file_content.path.endswith(".py"):
                    continue
                
                processed_count += 1
                
                try:
                    # Get file content
                    code_content = file_content.decoded_content.decode('utf-8', errors='replace')
                    
                    # Check if suitable
                    if not is_program_suitable(code_content, min_lines, min_complexity):
                        continue
                    
                    # Check for duplicates
                    if index.is_duplicate(code_content):
                        duplicate_count += 1
                        print(f"  🔄 Duplicate found: {file_content.path}")
                        continue
                    
                    # Extract metadata
                    function_name = extract_function_name(code_content)
                    complexity = calculate_complexity_score(code_content)
                    lines_count = len([line for line in code_content.split('\n') 
                                     if line.strip() and not line.strip().startswith('#')])
                    
                    # Generate unique filename
                    safe_path = re.sub(r'[\\/*?:"<>|]', "_", file_content.path)
                    file_id = f"{repo_name.replace('/', '_')}_{safe_path}"
                    output_file = repo_output_dir / f"{file_id}.json"
                    
                    # Prepare program data
                    program_data = {
                        "repo": repo_name,
                        "file_path": file_content.path,
                        "file_name": file_content.name,
                        "download_url": file_content.download_url,
                        "size_bytes": file_content.size,
                        "function_name": function_name,
                        "complexity_score": complexity,
                        "lines_of_code": lines_count,
                        "collection_batch": batch_id,
                        "collected_at": datetime.now().isoformat(),
                        "code": code_content
                    }
                    
                    # Save to file
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(program_data, f, indent=2, ensure_ascii=False)
                    
                    # Add to index
                    success = index.add_program(
                        code=code_content,
                        repo_name=repo_name,
                        file_path=file_content.path,
                        file_name=file_content.name,
                        function_name=function_name,
                        complexity_score=complexity,
                        lines_of_code=lines_count,
                        batch_id=batch_id,
                        output_file_path=str(output_file)
                    )
                    
                    if success:
                        collected_count += 1
                        print(f"✅ [{collected_count}/{max_files}] {file_content.path} (complexity: {complexity})")
                    else:
                        duplicate_count += 1
                        print(f"  🔄 Duplicate detected after processing: {file_content.path}")
                    
                    # Check rate limit periodically
                    if (collected_count + duplicate_count) % 10 == 0:
                        handle_rate_limit(g)
                
                except Exception as e:
                    print(f"  ❌ Error processing {file_content.path}: {e}")
            
            except Exception as e:
                print(f"  ⚠️ Error with repository item: {e}")
        
        print(f"📊 Repository {repo_name} summary:")
        print(f"  • Processed: {processed_count} files")
        print(f"  • Collected: {collected_count} new programs")
        print(f"  • Duplicates: {duplicate_count}")
        
        return collected_count
    
    except Exception as e:
        print(f"❌ Failed to process repository {repo_name}: {e}")
        return 0


def main():
    """Main function with batch management and deduplication."""
    args = parse_arguments()
    
    # Initialize deduplication system
    index = ProgramIndex()
    batch_manager = BatchManager(index)
    
    # Handle special modes
    if args.reset_index:
        if input("⚠️ This will delete all collection history. Continue? (y/N): ").lower() == 'y':
            os.remove(index.index_path)
            print("✅ Index reset")
            index = ProgramIndex()  # Reinitialize
        else:
            print("❌ Index reset cancelled")
            return
    
    if args.stats:
        print_collection_summary(index)
        return
      # Prepare repository list based on strategy or direct specification
    if args.repos:
        available_repos = args.repos
        print(f"📋 Using specified repositories: {len(available_repos)} repos")
    else:
        if args.strategy == 'all':
            available_repos = get_all_repos()
            print(f"📋 Using all available repositories: {len(available_repos)} repos")
        else:
            available_repos = get_repos_for_strategy(args.strategy)
            print(f"📋 Using '{args.strategy}' strategy: {len(available_repos)} repos")
    
    # Apply exclusions
    if args.exclude_repos:
        available_repos = [repo for repo in available_repos if repo not in args.exclude_repos]
        print(f"📋 After exclusions: {len(available_repos)} repos")
    
    # Plan the batch
    print("🎯 Planning collection batch...")
    batch_plan = batch_manager.plan_next_batch(
        target_total=args.target_total,
        batch_size=args.batch_size,
        available_repos=available_repos
    )
    
    # Display plan
    print("\n" + "="*60)
    print("📋 BATCH COLLECTION PLAN")
    print("="*60)
    
    if batch_plan['status'] == 'target_reached':
        print(batch_plan['message'])
        print_collection_summary(index)
        return
    
    print(f"Current Progress: {batch_plan['current_total']}/{batch_plan['target_total']} programs")
    print(f"Batch Target: {batch_plan['batch_target']} new programs")
    print(f"Remaining Needed: {batch_plan['remaining_needed']} programs")
    print(f"\nRepositories for this batch:")
    
    for repo_info in batch_plan['repositories']:
        print(f"  • {repo_info['name']}: {repo_info['target_for_batch']} programs "
              f"(current: {repo_info['current_count']})")
    
    if args.plan_only:
        print("\n📋 Plan displayed. Use --execute to run the collection.")
        return
    
    # Confirm execution
    if not args.test_mode:
        confirm = input(f"\n🚀 Execute batch collection? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Collection cancelled")
            return
    
    # Execute collection
    print("\n🚀 Starting batch collection...")
    start_time = time.time()
    
    # Initialize GitHub client
    g = Github(GITHUB_TOKEN)
    
    # Create collection function for batch manager
    def collection_func(repo_name: str, max_files: int, batch_id: int, **kwargs):
        return collect_from_repo_deduplicated(
            repo_name=repo_name,
            g=g,
            output_dir=args.output_dir,
            index=index,
            max_files=max_files,
            min_lines=args.min_lines,
            min_complexity=args.min_complexity,
            batch_id=batch_id,
            test_mode=args.test_mode
        )
    
    # Execute the batch
    result = batch_manager.execute_batch_plan(batch_plan, collection_func)
    
    # Report results
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("📊 BATCH COLLECTION RESULTS")
    print("="*60)
    
    if result['status'] == 'completed':
        print(f"✅ Batch completed successfully!")
        print(f"📈 Collected: {result['total_collected']}/{result['target']} programs")
        print(f"⏱️ Execution time: {elapsed_time:.2f} seconds")
        print(f"💾 Programs saved to: {args.output_dir}")
        
        print(f"\nResults by repository:")
        for repo_result in result['repo_results']:
            print(f"  • {repo_result['repo_name']}: {repo_result['collected']}/{repo_result['target']}")
    
    elif result['status'] == 'failed':
        print(f"❌ Batch failed: {result['error']}")
    
    # Show overall progress
    print_collection_summary(index)


if __name__ == "__main__":
    main()
