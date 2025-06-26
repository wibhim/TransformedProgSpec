"""
Script to apply all transformations sequentially to a Python program.
This helps assess the combined effect of multiple transformations.
"""

import os
import sys
import argparse
import json
from transformation.transforms import TRANSFORMERS

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Apply all transformations to a Python file")
    parser.add_argument("--input", type=str, required=True,
                       help="Input Python file or JSON file from collected programs")
    parser.add_argument("--output-dir", type=str, default="output/transformed_programs",
                       help="Output directory for transformed files")
    parser.add_argument("--skip", type=str, nargs="+", default=[],
                       help="Transformations to skip")
    return parser.parse_args()

def read_input_file(input_path):
    """Read input file, handling both .py and .json files."""
    try:
        if input_path.endswith(".py"):
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read(), os.path.basename(input_path)
        elif input_path.endswith(".json"):
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                filename = data.get("file_name", os.path.basename(input_path).replace(".json", ".py"))
                return data.get("code", ""), filename
        else:
            raise ValueError(f"Unsupported file format: {input_path}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

def apply_transformations(code, filename, output_dir, skip=None):
    """Apply all transformations sequentially."""
    skip = skip or []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the original code
    original_path = os.path.join(output_dir, f"{filename}")
    with open(original_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"✅ Original code saved to {original_path}")
    
    # Track transformations
    current_code = code
    
    # Apply each transformation in sequence
    for name, transformer_class in TRANSFORMERS.items():
        if name in skip:
            print(f"⏭️ Skipping transformation: {name}")
            continue
            
        transformer = transformer_class()
        print(f"🔄 Applying transformation: {transformer.describe()}")
        
        # Apply transformation
        transformed = transformer.transform(current_code)
        
        # Save the result of this transformation
        output_path = os.path.join(output_dir, f"{filename.replace('.py', '')}_{name}.py")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transformed)
        
        print(f"  - Size change: {len(current_code)} → {len(transformed)} chars")
        print(f"  - Output: {output_path}")
        
        # Update current code for next transformation
        current_code = transformed
    
    # Save the final result with all transformations applied
    final_path = os.path.join(output_dir, f"{filename.replace('.py', '')}_all_transforms.py")
    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(current_code)
    
    print(f"\n✅ All transformations applied:")
    print(f"  - Original size: {len(code)} chars")
    print(f"  - Final size: {len(current_code)} chars")
    print(f"  - Final output: {final_path}")
    
    return final_path

def main():
    """Main function."""
    args = parse_arguments()
    
    # Read input code
    code, filename = read_input_file(args.input)
    if not code:
        print("❌ No code found in input file")
        sys.exit(1)
    
    # Apply transformations
    apply_transformations(code, filename, args.output_dir, args.skip)

if __name__ == "__main__":
    main()
