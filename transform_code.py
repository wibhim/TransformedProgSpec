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
try:
    # Optional set of string-only transformers to apply after AST unparse
    from src.transformation.transforms import STRING_TRANSFORMERS
except Exception:
    STRING_TRANSFORMERS = set()
try:
    # Optional set of string-only transformers to apply after AST unparse
    from src.transformation.transforms import STRING_TRANSFORMERS
except Exception:
    STRING_TRANSFORMERS = set()
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
        # Keep a structural snapshot to detect true AST changes
        orig_dump = ast.dump(tree, include_attributes=False)
        
        # Build the list of transformers to apply
        ast_transformers: List[BaseTransformer] = []
        string_transformers: List[str] = []
        
        # Add requested transformers or use all if none specified
        transformer_names_to_use = transformation_names or list(TRANSFORMERS.keys())
        
        for name in transformer_names_to_use:
            if name in TRANSFORMERS:
                # Get the transformer class directly from the imported dictionary
                try:
                    if name in STRING_TRANSFORMERS:
                        string_transformers.append(name)
                        if verbose:
                            print(f"Queued string transformer: {name}")
                    else:
                        transformer_class = TRANSFORMERS[name]
                        transformer = create_transformer_instance(transformer_class, verbose)
                        ast_transformers.append(transformer)
                        if verbose:
                            print(f"Added AST transformer: {name}")
                except Exception as e:
                    if verbose:
                        print(f"Error creating transformer '{name}': {e}")
            else:
                if verbose:
                    print(f"Warning: Transformer '{name}' not found")
        
        # Apply AST transformers in sequence
        for transformer in ast_transformers:
            if verbose:
                print(f"Applying transformer: {transformer.__class__.__name__}")
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
        
        # Generate the transformed code only if the AST actually changed.
        # This avoids formatting-only diffs from ast.unparse when no transform applied.
        new_dump = ast.dump(tree, include_attributes=False)
        if new_dump == orig_dump:
            transformed = code  # no structural change; preserve original formatting
        else:
            transformed = ast.unparse(tree)

        # Apply string-only transformers after unparse (no reparse)
        for name in string_transformers:
            try:
                if verbose:
                    print(f"Applying string transformer: {name}")
                transformer_class = TRANSFORMERS[name]
                transformer = create_transformer_instance(transformer_class, verbose)
                transformed = transformer.transform(transformed)
            except Exception as e:
                if verbose:
                    print(f"Error in string transformer '{name}': {e}")
        
        return transformed, None
        
    except Exception as e:
        error_message = f"Error during transformation: {str(e)}"
        if verbose:
            print(error_message)
            import traceback
            print(traceback.format_exc())
        return code, error_message

def transform_file(input_path: str, output_path: str, transformation_names: Optional[List[str]] = None,
                  verbose: bool = False, changed_only: bool = False) -> bool:
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

        # If only storing changed outputs is requested and nothing changed, skip writing
        if changed_only and transformed.strip() == code.strip():
            if verbose:
                print("No changes detected; skipping write due to --changed-only.")
            return True
        
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
                     output_path: Optional[str] = None,
                     changed_only: bool = False) -> bool:
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
            raw_data = json.load(f)
        
        # Handle both direct arrays and wrapped data structures
        if isinstance(raw_data, dict) and 'data' in raw_data:
            dataset = raw_data['data']
        elif isinstance(raw_data, dict) and 'programs' in raw_data:
            dataset = raw_data['programs']
        elif isinstance(raw_data, list):
            dataset = raw_data
        else:
            raise ValueError("Input file must contain either a list of items or a dict with 'data' or 'programs' field")
        
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

            # Fallback: if replace_parentheses was requested but parentheses remain,
            # remove them directly here to ensure the dataset reflects the request.
            if transformation_names and 'replace_parentheses' in transformation_names:
                if '(' in transformed_code or ')' in transformed_code:
                    if verbose:
                        print("Fallback: removing parentheses at dataset stage")
                    transformed_code = transformed_code.replace('(', '').replace(')', '')
            
            # Decide if the sample actually changed
            changed = transformed_code.strip() != code.strip()

            # Create a new sample with transformed code
            new_sample = sample.copy()
            new_sample['code'] = transformed_code
            
            # Set the transformation type based on the transformations applied
            if transformation_names:
                # Use the first/primary transformation as the type
                new_sample['transformation_type'] = transformation_names[0]
                # Also record all requested transforms for clarity
                new_sample['applied_transformers'] = transformation_names
                # Optional: flag if parentheses still present when requested removal
                if 'replace_parentheses' in transformation_names:
                    if '(' in transformed_code or ')' in transformed_code:
                        new_sample['note'] = "Warning: parentheses still present after replace_parentheses even after fallback."
            else:
                new_sample['transformation_type'] = 'all_transformations'
                new_sample['applied_transformers'] = list(TRANSFORMERS.keys())

            # If original filename exists, compute an output name that appends the transformation type
            # e.g., foo.py -> foo__control_flow.py
            orig_fname = sample.get('filename') or sample.get('file')
            if orig_fname:
                base, ext = os.path.splitext(orig_fname)
                suffix = new_sample.get('transformation_type', 'transformed')
                new_sample['output_filename'] = f"{base}__{suffix}{ext or '.py'}"
            
            if error:
                new_sample['transformation_error'] = error
                error_count += 1
                if verbose:
                    print(f"Error transforming sample: {error}")
            else:
                new_sample['transformation_error'] = None
            
            # If only-changed mode is enabled, keep only changed samples
            if (not changed_only) or changed:
                transformed_dataset.append(new_sample)
            else:
                if verbose:
                    sid = sample.get('id') or sample.get('filename') or 'unknown'
                    print(f"Skipping unchanged sample due to --changed-only: {sid}")
        
        # Save the transformed dataset
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Only create directory if there is one
            os.makedirs(output_dir, exist_ok=True)
        
        # Prepare output in the same format as input
        if isinstance(raw_data, dict) and 'data' in raw_data:
            # Maintain wrapper structure
            output_data = {
                "metadata": raw_data.get("metadata", {}),
                "data": transformed_dataset
            }
        elif isinstance(raw_data, dict) and 'programs' in raw_data:
            # Maintain wrapper structure for consolidated datasets
            output_data = {
                "metadata": raw_data.get("metadata", {}),
                "programs": transformed_dataset
            }
            # Update metadata if it exists
            if "metadata" in output_data:
                output_data["metadata"]["total_items"] = len(transformed_dataset)
                output_data["metadata"]["transformation_applied"] = True
                if changed_only:
                    output_data["metadata"]["filtered_to_changed_only"] = True
        else:
            # Direct array output
            output_data = transformed_dataset
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
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
    parser.add_argument('--name-with-transform', action='store_true',
                       help='In single-file mode, derive output filename as <name>__<transform>.py when --output-file is not provided')
    
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
    parser.add_argument('--changed-only', action='store_true',
                       help='Only store outputs where the code actually changed after transformation')
    
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
            if args.name_with_transform and (args.all or args.core_only or args.transformers):
                # Build output path from input file name and primary transformation
                in_dir = os.path.dirname(input_path)
                in_base = os.path.basename(input_path)
                base, ext = os.path.splitext(in_base)
                # Determine primary transform label
                if args.all:
                    label = 'all_transformations'
                elif args.core_only:
                    label = 'core_transformations'
                else:
                    # transformers string already split below; recompute here safely
                    primary = None
                    if args.transformers:
                        for t in [t.strip() for t in args.transformers.split(',') if t.strip()]:
                            primary = t
                            break
                    label = primary or 'transformed'
                output_path = os.path.join(in_dir, f"{base}__{label}{ext or '.py'}")
                if args.verbose:
                    print(f"Derived output path: {output_path}")
            else:
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
        # Split by comma, trim whitespace, and drop empty entries
        transformers = [t.strip() for t in args.transformers.split(',') if t.strip()]
    
    # Execute the appropriate transformation
    if is_single_file:
        success = transform_file(
            input_path=input_path,
            output_path=output_path,
            transformation_names=transformers,
            verbose=args.verbose,
            changed_only=args.changed_only
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
            output_path=args.output,
            changed_only=args.changed_only
        )
        
        if success:
            print("Dataset transformation completed successfully.")
        else:
            print("Dataset transformation completed with errors.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
