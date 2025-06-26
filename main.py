#!/usr/bin/env python
"""
Research Pipeline Entry Point

This script orchestrates the entire pipeline for code transformation,
specification generation, and Dafny verification.
"""
import os
import json
import time
import argparse
from typing import Dict, Any, Optional

# Import configuration
from config.settings import CONFIG

def setup_argparser() -> argparse.ArgumentParser:
    """Set up command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Code Transformation and Formal Verification Pipeline"
    )
    parser.add_argument(
        "--steps", type=str, default="all",
        help="Comma-separated list of steps to run ('github', 'cleanup', 'transform', 'spec', 'extract', 'verify', 'report')"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show verbose output"
    )
    
    # GitHub data collection parameters
    parser.add_argument(
        "--repo", type=str,
        help="GitHub repository to collect from (format: 'owner/repo')"
    )
    parser.add_argument(
        "--max-files", type=int,
        help="Maximum number of files to collect from GitHub"
    )
    
    # Specification generation parameters
    parser.add_argument(
        "--spec-type", type=str, default="transformed",
        choices=["original", "transformed", "prompt_engineered"],
        help="Type of specification to generate ('original', 'transformed', 'prompt_engineered')"
    )
    parser.add_argument(
        "--prompt-template", type=str,
        help="Path to prompt template file for prompt-engineered specifications"
    )
    
    return parser

def run_github_collection(verbose: bool = False, repo: str = None, max_files: int = None) -> bool:
    """Run the step to collect code from GitHub."""
    try:
        print("\n📥 Running GitHub code collection...")
        
        # Build command line arguments for data collection
        import sys
        original_args = sys.argv.copy()
        sys.argv = [sys.argv[0]]  # Reset argv to just the script name
        
        # Add optional parameters if provided
        if repo:
            sys.argv.extend(["--repo", repo])
        if max_files:
            sys.argv.extend(["--max-files", str(max_files)])
        if verbose:
            print(f"Running data collection with args: {sys.argv}")
            
        # Import and run data collection
        import src.collection.repository as repository
        
        # Restore original arguments
        sys.argv = original_args
        
        print("✅ Successfully collected data from GitHub")
        return True
    except Exception as e:
        print(f"❌ Error in GitHub collection: {str(e)}")
        return False

def run_cleanup(verbose: bool = False) -> bool:
    """Run code cleanup step."""
    try:
        print("\n🧹 Running code cleanup...")
        # Import the cleanup module from the new location
        import src.utils.cleanup as cleanup
        print("✅ Successfully cleaned up code")
        return True
    except Exception as e:
        print(f"❌ Error in cleanup: {str(e)}")
        return False

def run_transformation(verbose: bool = False) -> bool:
    """Run code transformation step."""
    try:
        print("\n🔄 Running code transformation...")
        # Execute the transformation module
        import src.transformation.transformer as transformer
        # Call the main function if the module doesn't run automatically
        if hasattr(transformer, 'run_transformation'):
            transformer.run_transformation()
        print("✅ Successfully transformed code")
        return True
    except Exception as e:
        print(f"❌ Error in transformation: {str(e)}")
        return False

def run_specification_generation(verbose: bool = False, spec_type: str = "transformed", prompt_template: str = None) -> bool:
    """Run formal specification generation step.
    
    Args:
        verbose: Whether to show verbose output
        spec_type: Type of specification to generate ('original', 'transformed', 'prompt_engineered')
        prompt_template: Path to prompt template file for prompt-engineered specifications
    """
    try:
        print(f"\n📝 Running specification generation (type: {spec_type})...")
        
        # Set environment variables for the ChatGPT module
        import os
        os.environ["SPEC_TYPE"] = spec_type
        if prompt_template:
            os.environ["PROMPT_TEMPLATE"] = prompt_template
            
        # Execute the ChatGPT module
        import src.specification.generator as generator
        
        print(f"✅ Successfully generated {spec_type} specifications")
        return True
    except Exception as e:
        print(f"❌ Error in specification generation: {str(e)}")
        return False

def run_dafny_extraction(verbose: bool = False) -> bool:
    """Extract Dafny code from specifications and save as .dfy files."""
    try:
        print("\n📄 Extracting Dafny code from specifications...")
        # Execute the extraction module
        import src.verification.extractor as extractor
        extractor.main()
        print("✅ Successfully extracted Dafny programs")
        return True
    except Exception as e:
        print(f"❌ Error extracting Dafny code: {str(e)}")
        return False

def run_dafny_verification(verbose: bool = False) -> bool:
    """Run Dafny verification step."""
    try:
        print("\n✅ Running Dafny verification...")
        # Execute the Dafny verification module
        import src.verification.verifier as verifier
        print("✅ Successfully verified with Dafny")
        return True
    except Exception as e:
        print(f"❌ Error in Dafny verification: {str(e)}")
        return False

def run_report_generation(verbose: bool = False) -> bool:
    """Generate the final report."""
    try:
        print("\n📊 Generating report...")
        # Execute the report generation module
        import src.verification.reporter as reporter
        print("✅ Successfully generated reports")
        return True
    except Exception as e:
        print(f"❌ Error in report generation: {str(e)}")
        return False

def main() -> None:
    """Main execution function."""
    start_time = time.time()
    
    # Parse command-line arguments
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Determine which steps to run
    steps = args.steps.lower().split(",")
    run_all = "all" in steps
    
    # Run the pipeline steps
    results = {}
    
    if run_all or "github" in steps:
        results["github"] = run_github_collection(
            verbose=args.verbose,
            repo=args.repo,
            max_files=args.max_files
        )
        
    if run_all or "cleanup" in steps:
        results["cleanup"] = run_cleanup(args.verbose)
        
    if run_all or "transform" in steps:
        results["transform"] = run_transformation(args.verbose)
        
    if run_all or "spec" in steps:
        results["spec"] = run_specification_generation(
            verbose=args.verbose,
            spec_type=args.spec_type,
            prompt_template=args.prompt_template
        )
        
    if run_all or "extract" in steps:
        results["extract"] = run_dafny_extraction(args.verbose)
        
    # Always run extraction before verification when running all steps
    if run_all and "verify" in steps and "extract" not in steps:
        print("\n⚠️ Running extraction step automatically before verification...")
        results["extract"] = run_dafny_extraction(args.verbose)
        
    if run_all or "verify" in steps:
        results["verify"] = run_dafny_verification(args.verbose)
        
    if run_all or "report" in steps:
        results["report"] = run_report_generation(args.verbose)
    
    # Report results
    print("\n" + "="*50)
    print("Pipeline Execution Summary:")
    print("="*50)
    
    for step, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{step.capitalize()}: {status}")
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    print("="*50)

if __name__ == "__main__":
    main()