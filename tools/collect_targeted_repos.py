#!/usr/bin/env python3
"""
Targeted Repository Collector
Collects programs from specific high-priority repositories for formal specification research
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set
import tempfile
import shutil

class TargetedRepositoryCollector:
    """Collects programs from targeted repositories to fill dataset gaps"""
    
    def __init__(self, output_dir: str = "data/programs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Priority repositories for formal specification research
        self.priority_repositories = {
            'cryptography': {
                'url': 'https://github.com/pyca/cryptography.git',
                'focus_dirs': ['src/cryptography/hazmat/primitives', 'src/cryptography/utils'],
                'domain': 'cryptographic',
                'priority': 1,
                'description': 'Cryptographic primitives and security functions',
                'details': 'PyCA Cryptography provides cryptographic recipes and primitives to Python developers. Excellent for formal specification because cryptographic functions have well-defined security properties, clear input/output contracts, and mathematical foundations. Contains hash functions, symmetric/asymmetric encryption, digital signatures, and key derivation functions.',
                'why_good_for_specs': 'Security properties are formally definable, functions are pure with clear contracts, mathematical foundations enable rigorous specification'
            },
            'sympy': {
                'url': 'https://github.com/sympy/sympy.git',
                'focus_dirs': ['sympy/core', 'sympy/functions', 'sympy/utilities'],
                'domain': 'mathematical',
                'priority': 1,
                'description': 'Symbolic mathematics library with computer algebra system',
                'details': 'SymPy is a Python library for symbolic mathematics. It provides capabilities for symbolic computation including calculus, algebra, discrete math, and geometry. Functions have clear mathematical definitions and properties that translate directly to formal specifications.',
                'why_good_for_specs': 'Mathematical operations have precise definitions, symbolic computation enables property verification, pure functional style'
            },
            'networkx': {
                'url': 'https://github.com/networkx/networkx.git',
                'focus_dirs': ['networkx/algorithms', 'networkx/utils'],
                'domain': 'mathematical',
                'priority': 1,
                'description': 'Graph theory and network analysis algorithms',
                'details': 'NetworkX provides tools for creation, manipulation, and study of complex networks and graphs. Contains classic graph algorithms (shortest path, centrality, clustering) with well-established mathematical properties and invariants.',
                'why_good_for_specs': 'Graph algorithms have well-known mathematical properties, clear pre/post-conditions, established correctness criteria'
            },
            'lark': {
                'url': 'https://github.com/lark-parser/lark.git',
                'focus_dirs': ['lark', 'lark/parsers'],
                'domain': 'parser_language',
                'priority': 1,
                'description': 'Modern parsing toolkit for Python with grammar-based approach',
                'details': 'Lark is a parsing toolkit that can parse any context-free grammar. Uses Earley, LALR(1), or SLR parsers. Parser combinators and grammar rules have formal semantics based on language theory.',
                'why_good_for_specs': 'Parsing has formal language theory foundation, grammar rules are mathematically precise, deterministic behavior'
            },
            'more-itertools': {
                'url': 'https://github.com/more-itertools/more-itertools.git',
                'focus_dirs': ['more_itertools'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Additional iterator tools beyond Python standard library',
                'details': 'More-itertools provides iterator functions with functional programming patterns. Functions are typically pure, have clear input/output relationships, and follow mathematical principles of iteration and transformation.',
                'why_good_for_specs': 'Functional programming style, iterator combinators have mathematical properties, minimal side effects'
            },
            'pydantic': {
                'url': 'https://github.com/pydantic/pydantic.git',
                'focus_dirs': ['pydantic'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Data validation and type enforcement using Python type hints',
                'details': 'Pydantic provides data validation and settings management using Python type hints. Validation functions have clear contracts and error conditions that map well to formal specifications.',
                'why_good_for_specs': 'Type-based validation has formal semantics, clear error conditions, contract-based design'
            },
            'sortedcontainers': {
                'url': 'https://github.com/grantjenks/python-sortedcontainers.git',
                'focus_dirs': ['sortedcontainers'],
                'domain': 'data_processing',
                'priority': 2,
                'description': 'Pure Python sorted container types (lists, dicts, sets)',
                'details': 'SortedContainers provides sorted list, dict, and set implementations with guaranteed performance characteristics. Data structure operations maintain invariants that are perfect for formal specification.',
                'why_good_for_specs': 'Data structure invariants are formally definable, clear complexity guarantees, mathematical properties'
            },
            'toolz': {
                'url': 'https://github.com/pytoolz/toolz.git',
                'focus_dirs': ['toolz'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Functional programming utilities and higher-order functions',
                'details': 'Toolz provides functional programming utilities inspired by libraries like Underscore.js. Functions follow functional programming principles with immutability and composability.',
                'why_good_for_specs': 'Functional programming paradigm, composable functions, mathematical function properties'
            },
            'marshmallow': {
                'url': 'https://github.com/marshmallow-code/marshmallow.git',
                'focus_dirs': ['src/marshmallow'],
                'domain': 'data_processing',
                'priority': 2,
                'description': 'Object serialization/deserialization library with validation',
                'details': 'Marshmallow converts complex datatypes to/from native Python datatypes. Serialization and validation schemas have clear rules and error conditions suitable for specification.',
                'why_good_for_specs': 'Schema-based validation, clear transformation rules, well-defined error conditions'
            },
            'schema': {
                'url': 'https://github.com/keleshev/schema.git',
                'focus_dirs': ['schema'],
                'domain': 'data_processing',
                'priority': 2,
                'description': 'Simple data validation library with declarative schemas',
                'details': 'Schema provides a simple way to validate data structures. Uses declarative schemas that clearly specify data requirements and validation rules.',
                'why_good_for_specs': 'Declarative validation rules, clear boolean logic, simple contract specification'
            },
            'pyparsing': {
                'url': 'https://github.com/pyparsing/pyparsing.git',
                'focus_dirs': ['pyparsing'],
                'domain': 'parser_language',
                'priority': 2,
                'description': 'Parser generator library with recursive descent parsing',
                'details': 'PyParsing creates parsers using Python expressions. Parser combinators have compositional semantics that align well with formal specification approaches.',
                'why_good_for_specs': 'Parser combinators are mathematically compositional, recursive descent has clear semantics'
            },
            'jsonschema': {
                'url': 'https://github.com/python-jsonschema/jsonschema.git',
                'focus_dirs': ['jsonschema'],
                'domain': 'data_processing',
                'priority': 2,
                'description': 'JSON Schema validation implementation',
                'details': 'JSON Schema validation according to specifications. Validation functions implement formal JSON Schema semantics with precise error reporting.',
                'why_good_for_specs': 'JSON Schema has formal specification, validation logic is precisely defined, clear boolean results'
            },
            'click': {
                'url': 'https://github.com/pallets/click.git',
                'focus_dirs': ['src/click'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Command-line interface creation toolkit',
                'details': 'Click creates command-line interfaces with decorators and parameter validation. Option parsing and validation functions have clear contracts.',
                'why_good_for_specs': 'Parameter validation has clear rules, command-line parsing is deterministic, well-defined error cases'
            },
            'hypothesis': {
                'url': 'https://github.com/HypothesisWorks/hypothesis.git',
                'focus_dirs': ['hypothesis-python/src/hypothesis'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Property-based testing library with data generation',
                'details': 'Hypothesis generates test data and performs property-based testing. Data generation strategies and property checking have mathematical foundations.',
                'why_good_for_specs': 'Property-based testing aligns with formal specification, data generators have formal properties'
            },
            'attrs': {
                'url': 'https://github.com/python-attrs/attrs.git',
                'focus_dirs': ['src/attr'],
                'domain': 'system_utilities',
                'priority': 2,
                'description': 'Classes without boilerplate with validation and conversion',
                'details': 'Attrs helps create classes with automatic method generation, validation, and conversion. Attribute validation and conversion functions have clear contracts.',
                'why_good_for_specs': 'Validation functions have clear contracts, conversion rules are deterministic, type-based design'
            }
        }
    
    def clone_repository(self, repo_name: str, temp_dir: Path) -> Path:
        """Clone repository to temporary directory"""
        repo_config = self.priority_repositories[repo_name]
        repo_url = repo_config['url']
        clone_path = temp_dir / repo_name
        
        print(f"Cloning {repo_name} from {repo_url}...")
        
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(clone_path)],
                check=True,
                capture_output=True,
                text=True
            )
            return clone_path
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {repo_name}: {e}")
            print(f"stderr: {e.stderr}")
            raise
    
    def find_python_files(self, repo_path: Path, focus_dirs: List[str]) -> List[Path]:
        """Find Python files in focus directories"""
        python_files = []
        
        for focus_dir in focus_dirs:
            focus_path = repo_path / focus_dir
            if focus_path.exists():
                # Find all .py files recursively
                for py_file in focus_path.rglob("*.py"):
                    # Skip test files and __init__.py files for now
                    if (not py_file.name.startswith('test_') and 
                        not py_file.name.startswith('_test') and
                        py_file.name != '__init__.py' and
                        not 'test' in str(py_file).lower()):
                        python_files.append(py_file)
        
        return python_files
    
    def extract_functions_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract individual functions from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            import ast
            tree = ast.parse(content)
            
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function code
                    function_lines = content.split('\n')[node.lineno-1:node.end_lineno]
                    function_code = '\n'.join(function_lines)
                    
                    # Basic quality checks
                    if (len(function_code) >= 50 and  # Minimum size
                        len(function_code) <= 3000 and  # Maximum size
                        'def ' in function_code and
                        'return' in function_code):
                        
                        function_info = {
                            'name': node.name,
                            'code': function_code,
                            'file_path': str(file_path),
                            'line_start': node.lineno,
                            'line_end': node.end_lineno,
                            'docstring': ast.get_docstring(node) or ""
                        }
                        functions.append(function_info)
            
            return functions
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []
    
    def collect_from_repository(self, repo_name: str, max_programs: int = 50) -> List[Dict[str, Any]]:
        """Collect programs from a specific repository"""
        if repo_name not in self.priority_repositories:
            print(f"Unknown repository: {repo_name}")
            return []
        
        repo_config = self.priority_repositories[repo_name]
        
        print(f"\n{'='*60}")
        print(f"Repository: {repo_name}")
        print(f"{'='*60}")
        print(f"Description: {repo_config['description']}")
        print(f"Domain: {repo_config['domain']}")
        print(f"Priority: {repo_config['priority']}")
        print(f"\nDetails: {repo_config['details']}")
        print(f"\nWhy good for specs: {repo_config['why_good_for_specs']}")
        print(f"{'='*60}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Clone repository
                repo_path = self.clone_repository(repo_name, temp_path)
                
                # Find Python files in focus directories
                python_files = self.find_python_files(repo_path, repo_config['focus_dirs'])
                print(f"Found {len(python_files)} Python files in {repo_name}")
                
                # Extract functions
                all_programs = []
                
                for py_file in python_files:
                    functions = self.extract_functions_from_file(py_file)
                    
                    for func in functions:
                        program = {
                            'id': f"{repo_name}_{func['name']}_{func['line_start']}",
                            'repository': f"{repo_name}/{repo_name}",
                            'file_path': func['file_path'].replace(str(repo_path), ''),
                            'function_name': func['name'],
                            'code': func['code'],
                            'docstring': func['docstring'],
                            'domain': repo_config['domain'],
                            'source': 'targeted_collection',
                            'line_range': f"{func['line_start']}-{func['line_end']}",
                            'repository_description': repo_config['description'],
                            'repository_details': repo_config['details']
                        }
                        all_programs.append(program)
                
                # Sort by quality and take best programs
                scored_programs = []
                for program in all_programs:
                    score = self.score_program_quality(program)
                    scored_programs.append((program, score))
                
                # Sort by score (descending) and take top programs
                scored_programs.sort(key=lambda x: x[1], reverse=True)
                selected_programs = [prog[0] for prog in scored_programs[:max_programs]]
                
                print(f"Selected {len(selected_programs)} high-quality programs from {repo_name}")
                return selected_programs
                
            except Exception as e:
                print(f"Error collecting from {repo_name}: {e}")
                return []
    
    def score_program_quality(self, program: Dict[str, Any]) -> int:
        """Score program quality for selection"""
        code = program['code']
        score = 0
        
        # Function length (optimal range: 50-200 lines)
        lines = len(code.split('\n'))
        if 50 <= lines <= 200:
            score += 20
        elif 20 <= lines <= 300:
            score += 10
        
        # Has docstring
        if program.get('docstring'):
            score += 15
        
        # Has type hints
        if ':' in code and '->' in code:
            score += 15
        
        # Mathematical/algorithmic content
        math_keywords = ['algorithm', 'calculate', 'compute', 'solve', 'optimize', 
                        'matrix', 'vector', 'graph', 'tree', 'sort', 'search']
        if any(keyword in code.lower() for keyword in math_keywords):
            score += 20
        
        # Clear input/output pattern
        if 'def ' in code and 'return ' in code:
            score += 10
        
        # Avoid complex dependencies
        avoid_keywords = ['import requests', 'import urllib', 'import os', 'import sys',
                         'subprocess', 'multiprocessing', 'threading']
        if not any(keyword in code for keyword in avoid_keywords):
            score += 10
        
        # Comments and documentation
        comment_count = code.count('#')
        if comment_count >= 3:
            score += 10
        
        return score
    
    def print_repository_information(self):
        """Print detailed information about all available repositories"""
        print("\n" + "="*80)
        print("AVAILABLE REPOSITORIES FOR TARGETED COLLECTION")
        print("="*80)
        
        # Group by priority
        priority_groups = {}
        for name, config in self.priority_repositories.items():
            priority = config['priority']
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append((name, config))
        
        # Print by priority
        for priority in sorted(priority_groups.keys()):
            print(f"\nPRIORITY {priority} REPOSITORIES:")
            print("-" * 40)
            
            for repo_name, config in priority_groups[priority]:
                print(f"\n📦 {repo_name.upper()}")
                print(f"   Description: {config['description']}")
                print(f"   Domain: {config['domain']}")
                print(f"   URL: {config['url']}")
                print(f"   Focus: {', '.join(config['focus_dirs'])}")
                print(f"   Details: {config['details']}")
                print(f"   Why good for specs: {config['why_good_for_specs']}")
        
        print(f"\n" + "="*80)
        print(f"TOTAL REPOSITORIES: {len(self.priority_repositories)}")
        
        # Domain summary
        domain_count = {}
        for config in self.priority_repositories.values():
            domain = config['domain']
            domain_count[domain] = domain_count.get(domain, 0) + 1
        
        print("\nDOMAIN DISTRIBUTION:")
        for domain, count in sorted(domain_count.items()):
            print(f"  {domain}: {count} repositories")
        print("="*80)

    def collect_priority_repositories(self, repo_names: List[str], max_per_repo: int = 50) -> List[Dict[str, Any]]:
        """Collect from multiple priority repositories"""
        all_programs = []
        
        for repo_name in repo_names:
            print(f"\n{'='*50}")
            print(f"Collecting from {repo_name}")
            print(f"{'='*50}")
            
            programs = self.collect_from_repository(repo_name, max_per_repo)
            all_programs.extend(programs)
            
            print(f"Total programs collected so far: {len(all_programs)}")
        
        return all_programs
    
    def save_collected_programs(self, programs: List[Dict[str, Any]], output_path: str):
        """Save collected programs to JSON file"""
        output_data = {
            'metadata': {
                'collection_type': 'targeted_repositories',
                'total_programs': len(programs),
                'collection_date': __import__('datetime').datetime.now().isoformat(),
                'repositories': list(set(prog['repository'] for prog in programs)),
                'domains': list(set(prog['domain'] for prog in programs))
            },
            'programs': programs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCollected programs saved to: {output_path}")
    
    def merge_with_existing_dataset(self, new_programs: List[Dict[str, Any]], 
                                   existing_dataset_path: str, output_path: str):
        """Merge new programs with existing dataset"""
        try:
            with open(existing_dataset_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_programs = existing_data
                elif isinstance(existing_data, dict) and 'programs' in existing_data:
                    existing_programs = existing_data['programs']
                else:
                    existing_programs = []
        except Exception as e:
            print(f"Error loading existing dataset: {e}")
            existing_programs = []
        
        # Check for duplicates (by ID or similar code)
        existing_ids = set(prog.get('id', '') for prog in existing_programs)
        
        unique_new_programs = []
        for program in new_programs:
            if program.get('id', '') not in existing_ids:
                unique_new_programs.append(program)
        
        # Merge
        merged_programs = existing_programs + unique_new_programs
        
        # Save merged dataset
        merged_data = {
            'metadata': {
                'total_programs': len(merged_programs),
                'original_programs': len(existing_programs),
                'new_programs': len(unique_new_programs),
                'merge_date': __import__('datetime').datetime.now().isoformat()
            },
            'programs': merged_programs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
        print(f"Merged dataset saved to: {output_path}")
        print(f"Total programs: {len(merged_programs)} (added {len(unique_new_programs)} new)")

def main():
    parser = argparse.ArgumentParser(description='Collect programs from targeted repositories')
    parser.add_argument('--repositories', '-r', nargs='+', 
                       choices=['cryptography', 'sympy', 'networkx', 'lark', 
                               'more-itertools', 'pydantic', 'sortedcontainers',
                               'toolz', 'marshmallow', 'schema', 'pyparsing',
                               'jsonschema', 'click', 'hypothesis', 'attrs'],
                       help='Repositories to collect from')
    parser.add_argument('--all-priority', action='store_true',
                       help='Collect from all priority 1 repositories')
    parser.add_argument('--list-repos', action='store_true',
                       help='List all available repositories with detailed information')
    parser.add_argument('--max-per-repo', type=int, default=35,
                       help='Maximum programs per repository (default: 35 for ~500 total)')
    parser.add_argument('--output', '-o', required=True,
                       help='Output JSON file for collected programs')
    parser.add_argument('--merge-with', 
                       help='Existing dataset to merge with')
    
    args = parser.parse_args()
    
    collector = TargetedRepositoryCollector()
    
    # List repositories if requested
    if args.list_repos:
        collector.print_repository_information()
        return 0
    
    # Determine which repositories to collect
    if args.all_priority:
        repo_names = [name for name, config in collector.priority_repositories.items() 
                     if config['priority'] == 1]
        print(f"Collecting from all Priority 1 repositories: {repo_names}")
    elif args.repositories:
        repo_names = args.repositories
    else:
        print("Error: Must specify --repositories, --all-priority, or --list-repos")
        return 1
    
    print(f"Target: ~{len(repo_names) * args.max_per_repo} programs total ({args.max_per_repo} per repository)")
    
    # Print repository information for selected repos
    print("\nSelected Repositories:")
    for repo_name in repo_names:
        if repo_name in collector.priority_repositories:
            config = collector.priority_repositories[repo_name]
            print(f"  • {repo_name}: {config['description']} ({config['domain']})")
    
    print(f"Collecting from repositories: {repo_names}")
    
    # Check git availability
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: git is not available. Please install git.")
        return 1
    
    # Collect programs
    collected_programs = collector.collect_priority_repositories(repo_names, args.max_per_repo)
    
    if not collected_programs:
        print("No programs collected.")
        return 1
    
    # Save or merge
    if args.merge_with:
        if not os.path.exists(args.merge_with):
            print(f"Error: Existing dataset '{args.merge_with}' not found")
            return 1
        collector.merge_with_existing_dataset(collected_programs, args.merge_with, args.output)
    else:
        collector.save_collected_programs(collected_programs, args.output)
    
    print(f"\nCollection completed successfully!")
    print(f"Total programs collected: {len(collected_programs)}")
    
    return 0

if __name__ == "__main__":
    exit(main())
