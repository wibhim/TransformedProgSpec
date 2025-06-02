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
from config import CONFIG

def setup_argparser() -> argparse.ArgumentParser:
    """Set up command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Code Transformation and Formal Verification Pipeline"
    )
    parser.add_argument(
        "--steps", type=str, default="all",
        help="Comma-separated list of steps to run ('github', 'cleanup', 'transform', 'spec', 'verify', 'report')"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show verbose output"
    )
    return parser

def run_github_collection(verbose: bool = False) -> bool:
    """Run the step to collect code from GitHub."""
    try:
        print("\n📥 Running GitHub code collection...")
        # This will execute the script as it runs when imported
        import process.data_collect as data_collect
        print("✅ Successfully collected data from GitHub")
        return True
    except Exception as e:
        print(f"❌ Error in GitHub collection: {str(e)}")
        return False

def run_cleanup(verbose: bool = False) -> bool:
    """Run code cleanup step."""
    try:
        print("\n🧹 Running code cleanup...")
        # This will execute the script when imported
        import process.cleanup as cleanup
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
        import process.transform_final as transform_final
        # Call the main function if the module doesn't run automatically
        if hasattr(transform_final, 'run_transformation'):
            transform_final.run_transformation()
        print("✅ Successfully transformed code")
        return True
    except Exception as e:
        print(f"❌ Error in transformation: {str(e)}")
        return False

def run_specification_generation(verbose: bool = False) -> bool:
    """Run formal specification generation step."""
    try:
        print("\n📝 Running specification generation...")
        # Execute the ChatGPT module
        import process.chatgpt as chatgpt
        print("✅ Successfully generated specifications")
        return True
    except Exception as e:
        print(f"❌ Error in specification generation: {str(e)}")
        return False

def run_dafny_verification(verbose: bool = False) -> bool:
    """Run Dafny verification step."""
    try:
        print("\n✅ Running Dafny verification...")
        # Execute the Dafny verification module
        import process.dafny_check as dafny_check
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
        import process.format_dafny_results as format_dafny_results
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
        results["github"] = run_github_collection(args.verbose)
        
    if run_all or "cleanup" in steps:
        results["cleanup"] = run_cleanup(args.verbose)
        
    if run_all or "transform" in steps:
        results["transform"] = run_transformation(args.verbose)
        
    if run_all or "spec" in steps:
        results["spec"] = run_specification_generation(args.verbose)
        
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
