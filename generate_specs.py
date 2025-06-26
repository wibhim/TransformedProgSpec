#!/usr/bin/env python
"""
Entry point for specification generation functionality.
Generates formal specifications from transformed Python code using LLMs.

Usage:
    python generate_specs.py [--input FILE] [--output FILE] [--model MODEL]
"""
import sys
import os
import argparse
import json

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import settings
try:
    from config.settings import CONFIG
    OUTPUT_DIR = CONFIG.get("OUTPUT_DIR", "output")
except (ImportError, KeyError):
    OUTPUT_DIR = "output"

# Import specification generator
from src.specification.generator import generate_specifications

def main():
    """Main entry point for specification generation"""
    parser = argparse.ArgumentParser(
        description="Generate formal specifications from transformed Python code"
    )
    
    parser.add_argument("--input", "-i", 
                        default=os.path.join(OUTPUT_DIR, "transformed_code_dataset.json"),
                        help="Input JSON file containing transformed code")
    
    parser.add_argument("--output", "-o", 
                        default=os.path.join(OUTPUT_DIR, "transformed_specifications.json"),
                        help="Output JSON file for specifications")
    
    parser.add_argument("--model", "-m", default="gpt-4",
                        help="Model to use for specification generation")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Load the transformed code dataset
    if args.verbose:
        print(f"Loading transformed code from: {args.input}")
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            transformed_dataset = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading input file: {e}")
        return 1
    
    # Generate specifications
    if args.verbose:
        print(f"Generating specifications using {args.model}...")
    
    specifications = generate_specifications(
        transformed_dataset, 
        model=args.model,
        verbose=args.verbose
    )
    
    # Save specifications
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    if args.verbose:
        print(f"Saving specifications to: {args.output}")
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(specifications, f, indent=2)
    
    if args.verbose:
        print(f"Specification generation complete. Results saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
