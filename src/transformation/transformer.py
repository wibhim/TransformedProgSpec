"""
Transformer module for code transformation.
"""

import os
import json
import ast
from typing import Dict, Any, List, Tuple

from config.settings import CONFIG
import ast
import astor
# Direct implementation to avoid circular imports
def pipeline_transform(code, transformation_names=None, include_core=True, verbose=False):
    """Transform code using direct implementation to avoid circular imports."""
    import ast
    import astor
    from .transforms import TRANSFORMERS
    from .transforms.control_flow import ControlFlowSimplifier
    from .transforms.variable_naming import VariableRenamer
    from .transforms.expression import ExpressionDecomposer
    from .transforms.loop_standard import LoopStandardizer
    from .transforms.function_extract import FunctionExtractor
    
    try:
        # Clean up the code
        code = code.strip()
        
        # Parse the code
        tree = ast.parse(code)
        
        # Build the list of transformers
        transformers = []
        
        # Add core transformers if requested
        if include_core:
            core_transformers = [
                FunctionExtractor(verbose=verbose),     # Extract functions first
                ControlFlowSimplifier(verbose=verbose), # Simplify control flow
                LoopStandardizer(verbose=verbose),      # Standardize loops
                ExpressionDecomposer(verbose=verbose),  # Decompose expressions
                VariableRenamer(verbose=verbose)        # Rename variables last
            ]
            transformers.extend(core_transformers)
            
        # Add requested transformers from the TRANSFORMERS dictionary
        if transformation_names:
            for name in transformation_names:
                if name in TRANSFORMERS:
                    transformer_class = TRANSFORMERS[name]
                    transformers.append(transformer_class(verbose=verbose))
                    if verbose:
                        print(f"Added transformer: {name}")
                else:
                    if verbose:
                        print(f"Warning: Transformer '{name}' not found")
        
        # If no transformers are specified and include_core is False, use all transformers
        if not transformers:
            if verbose:
                print("No specific transformers provided. Using all available transformers.")
            transformers.extend([cls(verbose=verbose) for name, cls in TRANSFORMERS.items()])
        
        # Apply each transformation
        for transformer in transformers:
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
            if verbose:
                print(transformer.report())
        
        # Convert back to code
        try:
            # Python 3.9+ has ast.unparse
            transformed_code = ast.unparse(tree)
        except AttributeError:
            # Fallback for older Python versions
            transformed_code = astor.to_source(tree)
        
        # Final cleanup
        transformed_code = transformed_code.strip()
        return transformed_code, None
        
    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def transform_code(code: str, transformation_names=None, include_core=True, verbose: bool = False) -> str:
    """
    Transform Python code into a cleaner, more standardized format.
    
    Args:
        code: String containing Python code to transform
        transformation_names: List of transformer names to apply
        include_core: Whether to include core transformers
        verbose: Whether to print verbose output
    
    Returns:
        Transformed code string
    """
    # Get transformation configuration
    from config.settings import CONFIG
    if transformation_names is None:
        transformation_names = CONFIG["transform"].get("transformations", [])
    if include_core is None:
        include_core = CONFIG["transform"].get("include_core", True)
        
    transformed, error = pipeline_transform(
        code, 
        transformation_names=transformation_names,
        include_core=include_core,
        verbose=verbose
    )
    
    if error:
        if verbose:
            print(f"Error transforming code: {error}")
        return code  # Return original code in case of error
    return transformed

def process_file(file_data: Dict[str, Any], transformation_names=None, include_core=True, verbose: bool = False) -> Dict[str, Any]:
    """
    Process a single file's data and transform its code.
    
    Args:
        file_data: Dictionary containing file data
        transformation_names: List of transformer names to apply
        include_core: Whether to include core transformers
        verbose: Whether to print verbose output
    
    Returns:
        Transformed file data
    """
    if 'cleaned_code' in file_data:
        code = file_data.get('cleaned_code', '')
        transformed_code = transform_code(
            code, 
            transformation_names=transformation_names,
            include_core=include_core,
            verbose=verbose
        )
        file_data['transformed_code'] = transformed_code
        
    return file_data

def run_transformation(transformation_names=None, include_core=None, verbose=False):
    """
    Run the transformation process on the cleaned code dataset.
    
    Args:
        transformation_names: List of transformer names to apply, None to use config
        include_core: Whether to include core transformers, None to use config
        verbose: Whether to print verbose output
    """
    print("Starting code transformation...")
    
    # Load configuration
    input_file = CONFIG["transform"]["input_json"]
    output_file = CONFIG["transform"]["output_json"]
    error_file = CONFIG["transform"]["error_file"]
    
    # Use config values if not provided
    if transformation_names is None:
        transformation_names = CONFIG["transform"].get("transformations", [])
    if include_core is None:
        include_core = CONFIG["transform"].get("include_core", True)
    
    if verbose:
        print(f"Using transformations: {transformation_names if transformation_names else 'All'}")
        print(f"Including core transformers: {include_core}")
    
    # Read input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each file
    transformed_data = []
    errors = []
    
    for file_data in data:
        try:
            transformed_file = process_file(
                file_data,
                transformation_names=transformation_names,
                include_core=include_core,
                verbose=verbose
            )
            transformed_data.append(transformed_file)
        except Exception as e:
            file_name = file_data.get('name', 'unknown')
            error_msg = f"Error transforming {file_name}: {str(e)}"
            errors.append(error_msg)
            if verbose:
                print(error_msg)
    
    # Write output JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=2)
    
    # Write errors
    if errors:
        with open(error_file, 'w', encoding='utf-8') as f:
            for error in errors:
                f.write(error + "\n")
    
    print(f"Transformation completed. Processed {len(transformed_data)} files with {len(errors)} errors.")

if __name__ == "__main__":
    run_transformation()
