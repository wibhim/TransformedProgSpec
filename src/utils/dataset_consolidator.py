#!/usr/bin/env python
"""
Dataset Consolidation Utility

This script consolidates individual program files into structured datasets
for experimental use, maintaining both individual access and batch processing capabilities.
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from config.settings import CONFIG

class DatasetConsolidator:
    """Consolidates individual program files into structured datasets."""
    
    def __init__(self, individual_dir: str, output_dir: str):
        self.individual_dir = Path(individual_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def consolidate_by_repository(self) -> Dict[str, str]:
        """Consolidate programs by repository."""
        repo_files = {}
        programs_by_repo = {}
        
        # Group individual files by repository
        for file_path in self.individual_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                program_data = json.load(f)
            
            repo_name = program_data.get("source_repo", "unknown")
            if repo_name not in programs_by_repo:
                programs_by_repo[repo_name] = []
            programs_by_repo[repo_name].append(program_data)
        
        # Create consolidated files per repository
        for repo_name, programs in programs_by_repo.items():
            consolidated_data = {
                "repository": repo_name,
                "collection_date": datetime.now().isoformat(),
                "program_count": len(programs),
                "programs": programs
            }
            
            output_file = self.output_dir / f"{repo_name.replace('/', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
            
            repo_files[repo_name] = str(output_file)
            print(f"✅ Consolidated {len(programs)} programs from {repo_name}")
        
        return repo_files
    
    def create_master_dataset(self, repo_files: Dict[str, str]) -> str:
        """Create master dataset from all repositories."""
        all_programs = []
        repo_info = {}
        
        for repo_name, file_path in repo_files.items():
            with open(file_path, 'r', encoding='utf-8') as f:
                repo_data = json.load(f)
            
            repo_info[repo_name] = {
                "program_count": len(repo_data["programs"]),
                "collection_date": repo_data["collection_date"]
            }
            
            # Add repository context to each program
            for program in repo_data["programs"]:
                program["source_repo"] = repo_name
                all_programs.append(program)
        
        master_dataset = {
            "dataset_info": {
                "version": "1.0",
                "creation_date": datetime.now().isoformat(),
                "total_programs": len(all_programs),
                "repositories": repo_info,                "collection_criteria": {
                    "min_lines": 10,
                    "max_lines": 50,
                    "total_target": 5000,
                    "estimated_repos": 50,
                    "avg_per_repo": 100,
                    "language": "python",                    "diversity_focus": True
                }
            },
            "programs": all_programs
        }
        
        output_file = self.output_dir / "complete_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(master_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created master dataset with {len(all_programs)} programs")
        return str(output_file)
    
    def create_experimental_splits(self, master_file: str, 
                                 train_ratio: float = 0.6,
                                 val_ratio: float = 0.2,
                                 test_ratio: float = 0.2) -> Dict[str, str]:
        """Create stratified train/validation/test splits for experiments."""
        import random
        
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        
        programs = master_data["programs"].copy()
        
        # Stratify by complexity and repository for balanced splits
        stratified_programs = self._stratify_programs(programs)
        
        all_splits = {"training": [], "validation": [], "test": []}
        
        # Create balanced splits within each stratum
        for stratum_programs in stratified_programs.values():
            random.shuffle(stratum_programs)
            total = len(stratum_programs)
            train_end = int(total * train_ratio)
            val_end = train_end + int(total * val_ratio)
            
            all_splits["training"].extend(stratum_programs[:train_end])
            all_splits["validation"].extend(stratum_programs[train_end:val_end])
            all_splits["test"].extend(stratum_programs[val_end:])
        
        # Shuffle final splits
        for split_data in all_splits.values():
            random.shuffle(split_data)
        
        split_files = {}
        for split_name, split_data in all_splits.items():
            split_dataset = {
                **master_data["dataset_info"],
                "split": split_name,
                "split_size": len(split_data),
                "stratification_info": self._get_split_statistics(split_data),
                "programs": split_data
            }
            
            output_file = self.output_dir / f"{split_name}_set.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(split_dataset, f, indent=2, ensure_ascii=False)
            
            split_files[split_name] = str(output_file)
            print(f"✅ Created {split_name} set with {len(split_data)} programs")
        
        return split_files
    
    def create_analysis_subsets(self, master_file: str) -> Dict[str, str]:
        """
        Create analysis subsets for comparative evaluation without permanent splits.
        Better for LLM comparison studies where no training is involved.
        """
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        
        programs = master_data["programs"].copy()
        
        # Create subsets for different analysis dimensions
        subsets = {}
        
        # 1. Complexity-based subsets
        complexity_groups = {"simple": [], "medium": [], "complex": []}
        for program in programs:
            complexity = self._estimate_complexity(program)
            complexity_groups[complexity].append(program)
        
        for complexity, group_programs in complexity_groups.items():
            if group_programs:  # Only create subset if there are programs
                subset_data = {
                    **master_data["dataset_info"],
                    "subset_type": "complexity",
                    "subset_name": complexity,
                    "subset_size": len(group_programs),
                    "subset_description": f"Programs with {complexity} complexity",
                    "programs": group_programs
                }
                
                output_file = self.output_dir / f"complexity_{complexity}_subset.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(subset_data, f, indent=2, ensure_ascii=False)
                
                subsets[f"complexity_{complexity}"] = str(output_file)
                print(f"✅ Created {complexity} complexity subset with {len(group_programs)} programs")
        
        # 2. Repository-type based subsets
        repo_groups = self._group_by_repository_type(programs)
        for repo_type, group_programs in repo_groups.items():
            if len(group_programs) >= 10:  # Only create subset if sufficient programs
                subset_data = {
                    **master_data["dataset_info"],
                    "subset_type": "repository_type", 
                    "subset_name": repo_type,
                    "subset_size": len(group_programs),
                    "subset_description": f"Programs from {repo_type} repositories",
                    "programs": group_programs
                }
                
                output_file = self.output_dir / f"repo_type_{repo_type}_subset.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(subset_data, f, indent=2, ensure_ascii=False)
                
                subsets[f"repo_type_{repo_type}"] = str(output_file)
                print(f"✅ Created {repo_type} repository subset with {len(group_programs)} programs")
        
        # 3. Size-based subsets for different evaluation scenarios
        size_groups = {
            "small_eval": programs[:100],  # Quick evaluation subset
            "medium_eval": programs[:500],  # Medium-scale evaluation
            "full_eval": programs  # Full dataset
        }
        
        for size_name, group_programs in size_groups.items():
            subset_data = {
                **master_data["dataset_info"],
                "subset_type": "evaluation_size",
                "subset_name": size_name,
                "subset_size": len(group_programs),
                "subset_description": f"Evaluation subset with {len(group_programs)} programs",
                "programs": group_programs
            }
            
            output_file = self.output_dir / f"eval_{size_name}_subset.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(subset_data, f, indent=2, ensure_ascii=False)
            
            subsets[f"eval_{size_name}"] = str(output_file)
            print(f"✅ Created {size_name} evaluation subset with {len(group_programs)} programs")
        
        return subsets
    
    def _stratify_programs(self, programs: List[Dict]) -> Dict[str, List[Dict]]:
        """Stratify programs by complexity and source repository."""
        strata = {}
        
        for program in programs:
            # Create stratification key based on complexity and repo
            complexity = self._estimate_complexity(program)
            repo = program.get("source_repo", "unknown")
            
            stratum_key = f"{complexity}_{repo}"
            if stratum_key not in strata:
                strata[stratum_key] = []
            strata[stratum_key].append(program)
        
        return strata
    
    def _estimate_complexity(self, program: Dict) -> str:
        """Estimate program complexity based on available metrics."""
        code = program.get("original_code", "")
        lines = len(code.split('\n'))
        
        # Simple complexity estimation
        if lines <= 15:
            return "simple"
        elif lines <= 30:
            return "medium"
        else:
            return "complex"
    
    def _get_split_statistics(self, programs: List[Dict]) -> Dict:
        """Get statistics about a split."""
        repos = {}
        complexities = {"simple": 0, "medium": 0, "complex": 0}
        
        for program in programs:
            repo = program.get("source_repo", "unknown")
            repos[repo] = repos.get(repo, 0) + 1
            
            complexity = self._estimate_complexity(program)
            complexities[complexity] += 1
        
        return {
            "repository_distribution": repos,
            "complexity_distribution": complexities,
            "total_repositories": len(repos)
        }
    
    def _group_by_repository_type(self, programs: List[Dict]) -> Dict[str, List[Dict]]:
        """Group programs by repository type/domain."""
        # Define repository categories based on your collection
        repo_categories = {
            "web_frameworks": ["django", "flask", "fastapi", "tornado", "bottle", "falcon"],
            "data_science": ["pandas", "numpy", "scipy", "matplotlib", "plotly", "sklearn"],
            "algorithms": ["Garvit244", "TheAlgorithms", "kamyu104", "leetcode", "algorithms"],
            "devops_tools": ["ansible", "fabric", "celery", "docker", "paramiko"],
            "testing_quality": ["pytest", "pylint", "mypy", "black", "flake8"],
            "utilities": ["click", "fire", "playwright", "requests", "pillow"]
        }
        
        groups = {category: [] for category in repo_categories.keys()}
        groups["other"] = []
        
        for program in programs:
            repo_name = program.get("source_repo", "").lower()
            categorized = False
            
            for category, keywords in repo_categories.items():
                if any(keyword.lower() in repo_name for keyword in keywords):
                    groups[category].append(program)
                    categorized = True
                    break
            
            if not categorized:
                groups["other"].append(program)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

def main():
    """Main consolidation process."""
    parser = argparse.ArgumentParser(description="Consolidate individual program files into datasets")
    parser.add_argument("--individual-dir", type=str, 
                       default=os.path.join(CONFIG["BASE_DIR"], "data", "repositories", "individual"),
                       help="Directory containing individual program JSON files")
    parser.add_argument("--output-dir", type=str,
                       default=os.path.join(CONFIG["BASE_DIR"], "data", "repositories", "consolidated"),
                       help="Output directory for consolidated datasets")
    
    # Choose consolidation approach
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--create-splits", action="store_true",
                       help="Create train/validation/test splits (for model training/benchmarking)")
    group.add_argument("--create-subsets", action="store_true",
                       help="Create analysis subsets (for LLM comparison studies - RECOMMENDED)")
    
    args = parser.parse_args()
    
    print("🔄 Starting dataset consolidation...")
    
    consolidator = DatasetConsolidator(args.individual_dir, args.output_dir)
    
    # Step 1: Consolidate by repository
    repo_files = consolidator.consolidate_by_repository()
    
    # Step 2: Create master dataset
    master_file = consolidator.create_master_dataset(repo_files)
    
    # Step 3: Create analysis datasets based on approach
    if args.create_splits:
        print("\n📊 Creating train/validation/test splits...")
        split_files = consolidator.create_experimental_splits(master_file)
        print(f"\n📊 Dataset splits created:")
        for split_name, file_path in split_files.items():
            print(f"  - {split_name}: {file_path}")
            
    elif args.create_subsets:
        print("\n📊 Creating analysis subsets...")
        subset_files = consolidator.create_analysis_subsets(master_file)
        print(f"\n📊 Analysis subsets created:")
        for subset_name, file_path in subset_files.items():
            print(f"  - {subset_name}: {file_path}")
    
    else:
        print("\n💡 Use --create-subsets (recommended for LLM comparison) or --create-splits (for model training)")
    
    print(f"\n✅ Consolidation complete!")
    print(f"📁 Master dataset: {master_file}")
    print(f"📁 Repository files: {len(repo_files)} files created")
    
    if not args.create_splits and not args.create_subsets:
        print(f"\n🚀 Next steps:")
        print(f"  For LLM comparison: python consolidate_dataset.py --create-subsets")
        print(f"  For model training: python consolidate_dataset.py --create-splits")

if __name__ == "__main__":
    main()
