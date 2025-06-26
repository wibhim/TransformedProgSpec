#!/usr/bin/env python
"""
Entry point for code transformation functionality.
Transforms Python code by applying various transformations for simplification.

Usage:
    # Transform a single file
    python transform_code.py --single-file input.py --output-file output.py --transformers control_flow,variable_naming
    
    # Transform a dataset
    python transform_code.py --transformers control_flow,variable_naming
    
    # Apply all transformations
    python transform_code.py --all
    
    # List available transformers
    python transform_code.py --list
"""
import sys
import os
import argparse
import json
import ast
from typing import List, Dict, Any, Optional, Tuple

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the transformation functionality
from src.transformation.transforms import TRANSFORMERS
from src.transformation.base import BaseTransformer

# Import settings
try:
    from config.settings import CONFIG
    DATASETS_DIR = os.path.join(CONFIG["REPOSITORIES_DIR"], "datasets")
    OUTPUT_DIR = CONFIG["OUTPUT_DIR"]
except (ImportError, KeyError):
    # Default values
    DATASETS_DIR = os.path.join("data", "repositories", "datasets")
    OUTPUT_DIR = "output"

def create_transformer_instance(transformer_class, verbose=False):
    """Create a transformer instance, handling different constructor signatures"""
    try:
        # Try with verbose parameter
        return transformer_class(verbose=verbose)
    except TypeError:
        # Fall back to no parameters
        return transformer_class()

def transform_code(code: str, transformation_names: Optional[List[str]] = None, 
                  verbose: bool = False) -> Tuple[str, Optional[str]]:
    """
    Transform Python code by applying selected transformations.
    
    Args:
        code: String containing Python code to transform
        transformation_names: Names of transformers to apply (from TRANSFORMERS dictionary)
        verbose: Whether to print detailed progress information
    
    Returns:
        tuple: (transformed_code, error_message)
    """
    try:
        # Clean the code
        code = code.strip()
        
        # Parse the code
        tree = ast.parse(code)
        
        # Build the list of transformers to apply
        transformers = []
        # Add requested transformers or use all if none specified
        transformer_names_to_use = transformation_names or list(TRANSFORMERS.keys())
        
        for name in transformer_names_to_use:
            if name in TRANSFORMERS:
                # Get the transformer class directly from the imported dictionary
                try:
                    transformer_class = TRANSFORMERS[name]
                    transformer = create_transformer_instance(transformer_class, verbose)
                    transformers.append(transformer)
                    if verbose:
                        print(f"Added transformer: {name}")
                except Exception as e:
                    if verbose:
                        print(f"Error creating transformer '{name}': {e}")
            else:
                if verbose:
                    print(f"Warning: Transformer '{name}' not found")
        
        # Apply each transformer in sequence
        for transformer in transformers:
            if verbose:
                print(f"Applying transformer: {transformer.__class__.__name__}")
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
        
        # Generate the transformed code
        transformed = ast.unparse(tree)
        
        return transformed, None
        
    except Exception as e:
        error_message = f"Error during transformation: {str(e)}"
        if verbose:
            print(error_message)
            import traceback
            print(traceback.format_exc())
        return code, error_message

def transform_file(input_path: str, output_path: str, transformation_names: Optional[List[str]] = None,
                  verbose: bool = False) -> bool:
    """Transform a Python file using selected transformations."""
    try:
        if verbose:
            print(f"Transforming file: {input_path}")
            print(f"Transformations: {transformation_names}")
        
        # Read the input file
        with open(input_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Transform the code
        transformed, error = transform_code(
            code=code,
            transformation_names=transformation_names,
            verbose=verbose
        )
        
        if error:
            print(f"Error transforming file: {error}")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write transformed code to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transformed)
        
        if verbose:
            print(f"Transformed code saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error transforming file: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def transform_dataset(transformation_names: Optional[List[str]] = None, 
                     verbose: bool = False,
                     input_path: Optional[str] = None,
                     output_path: Optional[str] = None) -> bool:
    """Transform the entire dataset of Python code samples."""
    try:
        # Get input and output paths
        input_path = input_path or os.path.join(DATASETS_DIR, 'python_code_dataset.json')
        output_path = output_path or os.path.join(OUTPUT_DIR, 'transformed_code_dataset.json')
        
        if verbose:
            print(f"Transforming dataset: {input_path}")
            print(f"Output path: {output_path}")
            print(f"Using transformations: {transformation_names or 'All'}")
        
        # Load the input dataset
        with open(input_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Transform each code sample
        transformed_dataset = []
        error_count = 0
        
        total_samples = len(dataset)
        for i, sample in enumerate(dataset):
            if verbose:
                print(f"\nProcessing sample {i+1}/{total_samples}: {sample.get('id', 'unknown')}")
            
            # Get the code
            code = sample.get('code', '')
            
            # Skip empty samples
            if not code.strip():
                if verbose:
                    print("Skipping empty code sample")
                continue
            
            # Transform the code
            transformed_code, error = transform_code(
                code=code,
                transformation_names=transformation_names,
                verbose=verbose
            )
            
            # Create a new sample with transformed code
            new_sample = sample.copy()
            new_sample['code'] = transformed_code
            
            if error:
                new_sample['transformation_error'] = error
                error_count += 1
                if verbose:
                    print(f"Error transforming sample: {error}")
            else:
                new_sample['transformation_error'] = None
            
            transformed_dataset.append(new_sample)
        
        # Save the transformed dataset
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transformed_dataset, f, indent=2)
        
        if verbose:
            print(f"\nTransformation complete. {len(transformed_dataset)} samples processed.")
            print(f"Errors encountered: {error_count}")
            print(f"Results saved to: {output_path}")
        
        return error_count == 0
        
    except Exception as e:
        print(f"Error transforming dataset: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def list_available_transformers():
    """Print available transformers"""
    print("\nAvailable transformers:")
    
    # Group transformers into categories for better organization
    core_transformers = ["control_flow", "variable_naming", "expression", "loop_standard", "function_extract"]
    
    print("\nStructural transformers (recommended for code structure changes):")
    for name in sorted(name for name in TRANSFORMERS.keys() if name in core_transformers):
        print(f"  - {name}")
        
    print("\nAdditional transformers (specialized transformations):")
    for name in sorted(name for name in TRANSFORMERS.keys() if name not in core_transformers):
        print(f"  - {name}")
        
    print("\nNote: All transformers can be selected individually or in combination.")

def main():
    """Main entry point for transformation functionality"""
    parser = argparse.ArgumentParser(
        description="Transform Python code using selected transformations"
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--single-file', metavar='INPUT_FILE',
                          help='Transform a single file instead of the dataset')
    mode_group.add_argument('--list', '-l', action='store_true',
                          help='List available transformers')
    
    # File options
    parser.add_argument('--output-file', metavar='OUTPUT_FILE',
                       help='Output path for single file transformation')
    parser.add_argument('--input', metavar='INPUT_DATASET',
                       help='Input dataset file (for dataset transformation)')
    parser.add_argument('--output', metavar='OUTPUT_DATASET',
                       help='Output dataset file (for dataset transformation)')
    
    # Transformer selection options
    transform_group = parser.add_mutually_exclusive_group()
    transform_group.add_argument('--all', action='store_true',
                               help='Apply all available transformations')
    transform_group.add_argument('--transformers', type=str,
                               help='Comma-separated list of transformers to apply')
    transform_group.add_argument('--core-only', action='store_true',
                               help='Apply only core transformations (control_flow, variable_naming, expression, loop_standard, function_extract)')
    
    # Other options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed progress information')
    
    # Legacy positional arguments support
    parser.add_argument('input_pos', nargs='?', help=argparse.SUPPRESS)
    parser.add_argument('output_pos', nargs='?', help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Handle list mode
    if args.list:
        list_available_transformers()
        return 0
    
    # Determine operation mode: single file or dataset
    is_single_file = args.single_file is not None or (args.input_pos is not None and args.output_pos is not None)
    
    # Handle single file mode
    if is_single_file:
        # Determine input and output paths
        input_path = args.single_file or args.input_pos
        output_path = args.output_file or args.output_pos
        
        if not input_path:
            print("Error: Input file path is required.")
            return 1
        
        if not output_path:
            print("Error: Output file path is required.")
            return 1
    
    # Determine which transformers to use
    transformers = None
    
    if args.all:
        transformers = list(TRANSFORMERS.keys())
    elif args.core_only:
        # Use only core transformers
        core_transformers = ["control_flow", "variable_naming", "expression", "loop_standard", "function_extract"]
        transformers = [t for t in core_transformers]
    elif args.transformers:
        transformers = [t.strip() for t in args.transformers.split(',')]
    
    # Execute the appropriate transformation
    if is_single_file:
        success = transform_file(
            input_path=input_path,
            output_path=output_path,
            transformation_names=transformers,
            verbose=args.verbose
        )
        
        if success:
            print("Transformation completed successfully.")
        else:
            print("Transformation failed. See errors above.")
            return 1
    else:
        # Dataset transformation
        success = transform_dataset(
            transformation_names=transformers,
            verbose=args.verbose,
            input_path=args.input,
            output_path=args.output
        )
        
        if success:
            print("Dataset transformation completed successfully.")
        else:
            print("Dataset transformation completed with errors.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
