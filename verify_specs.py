#!/usr/bin/env python
"""
Entry point for verification functionality.
Extracts and verifies Dafny code from specifications.

Usage:
    python verify_specs.py [--input FILE] [--output FILE] [--dafny PATH]
"""
import os
import sys
import argparse
import json
from typing import Dict, List, Any

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import settings
try:
    from config.settings import CONFIG
    OUTPUT_DIR = CONFIG.get("OUTPUT_DIR", "output")
    DAFNY_PATH = CONFIG.get("DAFNY_PATH", "dafny")
except (ImportError, KeyError):
    OUTPUT_DIR = "output"
    DAFNY_PATH = "dafny"  # Assuming dafny is in PATH

# Import verification modules
from src.verification.extractor import extract_dafny_code
from src.verification.verifier import verify_dafny_file
from src.verification.reporter import generate_html_report as generate_verification_report

def main():
    """Main entry point for verification functionality"""
    parser = argparse.ArgumentParser(
        description="Extract and verify Dafny code from specifications"
    )
    
    parser.add_argument("--input", "-i", 
                        default=os.path.join(OUTPUT_DIR, "transformed_specifications.json"),
                        help="Input JSON file containing specifications")
    
    parser.add_argument("--output", "-o", 
                        default=os.path.join(OUTPUT_DIR, "dafny_verification_results.json"),
                        help="Output JSON file for verification results")
    
    parser.add_argument("--dafny-dir", "-d", 
                        default=os.path.join(OUTPUT_DIR, "dafny_programs"),
                        help="Directory to save extracted Dafny files")
    
    parser.add_argument("--dafny-path", 
                        default=DAFNY_PATH,
                        help="Path to Dafny executable")
    
    parser.add_argument("--timeout", "-t", type=int, default=60,
                        help="Timeout in seconds for each verification")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Load the specifications
    if args.verbose:
        print(f"Loading specifications from: {args.input}")
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            specifications = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading input file: {e}")
        return 1
    
    # Create output directory for Dafny files
    os.makedirs(args.dafny_dir, exist_ok=True)
    
    # Extract Dafny code
    if args.verbose:
        print("Extracting Dafny code from specifications...")
    
    dafny_files = extract_dafny_code(
        specifications, 
        output_dir=args.dafny_dir,
        verbose=args.verbose
    )
      # Verify Dafny code
    if args.verbose:
        print(f"Verifying Dafny code using {args.dafny_path}...")
    
    verification_results = []
    for dafny_file in dafny_files:
        result = verify_dafny_file(
            dafny_file,
            timeout=args.timeout
        )
        verification_results.append(result)
    
    # Generate verification report
    if args.verbose:
        print("Generating verification report...")
    
    report = generate_verification_report(
        verification_results,
        specifications
    )
    
    # Save verification results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    if args.verbose:
        print(f"Saving verification results to: {args.output}")
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nVerification Summary:")
    print(f"- Total specifications: {len(specifications)}")
    print(f"- Successful verifications: {report['summary']['successful']}")
    print(f"- Failed verifications: {report['summary']['failed']}")
    print(f"- Timeout verifications: {report['summary']['timeout']}")
    print(f"- Success rate: {report['summary']['success_rate']:.2f}%")
    
    if args.verbose:
        print(f"Verification complete. Results saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
