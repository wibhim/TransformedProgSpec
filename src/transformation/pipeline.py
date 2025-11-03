"""
Transformation pipeline for chaining multiple transformations.
"""
import ast
import json
import os
import textwrap
import astor

# Import common utilities
def clean_code(code):
    """Clean the code by fixing whitespace and indentation."""
    return textwrap.dedent(code).strip()

# Import transformation classes
from .transforms.control_flow import ControlFlowSimplifier
from .transforms.variable_naming import VariableRenamer
from .transforms.expression import ExpressionDecomposer
from .transforms.loop_standard import LoopStandardizer
from .transforms.function_extract import FunctionExtractor

# Optional registry of available transformers and string-only markers
try:
    from .transforms import TRANSFORMERS, STRING_TRANSFORMERS
except Exception:
    TRANSFORMERS = {}
    STRING_TRANSFORMERS = set()

def transform_code(code, transformers=None, transformation_names=None, include_core=True, verbose=False):
    """Apply selected transformations to a code snippet.
    
    Args:
        code (str): Python code string to transform
        transformers (list): List of transformer instances to apply, or None to use defaults
        transformation_names (list): List of transformer names to use from TRANSFORMERS dictionary
        include_core (bool): Whether to include core transformers (control flow etc.)
        verbose (bool): Whether to print detailed progress messages
    
    Returns:
        tuple: (transformed_code, error_message)
    """
    if transformers is None:
        # Build AST and string transformer queues
        ast_transformers = []
        string_transformers = []  # store names; instantiate later

        # Add core AST transformers if requested
        if include_core:
            core_transformers = [
                FunctionExtractor(verbose=verbose),     # Extract functions first
                ControlFlowSimplifier(verbose=verbose), # Simplify control flow
                LoopStandardizer(verbose=verbose),      # Standardize loops
                ExpressionDecomposer(verbose=verbose),  # Decompose expressions
                VariableRenamer(verbose=verbose)        # Rename variables last
            ]
            ast_transformers.extend(core_transformers)

        # Add requested transformers from the TRANSFORMERS dictionary
        if transformation_names:
            for name in transformation_names:
                if name in TRANSFORMERS:
                    if name in STRING_TRANSFORMERS:
                        string_transformers.append(name)
                        if verbose:
                            print(f"Queued string transformer: {name}")
                    else:
                        transformer_class = TRANSFORMERS[name]
                        ast_transformers.append(transformer_class(verbose=verbose))
                        if verbose:
                            print(f"Added AST transformer: {name}")
                else:
                    if verbose:
                        print(f"Warning: Transformer '{name}' not found")

        # If no transformers were specified at all, include all available ones
        if not transformation_names:
            if verbose:
                print("No specific transformers provided. Using all available transformers.")
            for name, cls in TRANSFORMERS.items():
                if name in STRING_TRANSFORMERS:
                    string_transformers.append(name)
                else:
                    ast_transformers.append(cls(verbose=verbose))
        
        transformers = (ast_transformers, string_transformers)
    
    try:
        # Clean up the code
        code = clean_code(code)
        
        # Parse the code
        tree = ast.parse(code)

        # Unpack queues
        if isinstance(transformers, tuple):
            ast_transformers, string_transformers = transformers
        else:
            # Backward compatibility: previous callers may pass a flat list
            ast_transformers = transformers
            string_transformers = []

        # Apply AST transformations
        for transformer in ast_transformers:
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
            if verbose and hasattr(transformer, 'report'):
                print(transformer.report())

        # Convert AST back to code
        try:
            # Python 3.9+ has ast.unparse
            transformed_code = ast.unparse(tree)
        except AttributeError:
            # Fallback for older Python versions
            import astor
            transformed_code = astor.to_source(tree)

        # Apply string-only transformers at the end (no reparse)
        for name in string_transformers:
            try:
                transformer_class = TRANSFORMERS[name]
                transformer = transformer_class(verbose=verbose)
                transformed_code = transformer.transform(transformed_code)
                if verbose and hasattr(transformer, 'report'):
                    print(transformer.report())
            except Exception as e:
                if verbose:
                    print(f"Error in string transformer '{name}': {e}")

        # Final cleanup
        transformed_code = clean_code(transformed_code)
        return transformed_code, None
        
    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def process_dataset(input_file, output_file, transformation_names=None, include_core=True, verbose=False):
    """Process an entire dataset of code snippets.
    
    Args:
        input_file (str): Path to input JSON file with code snippets
        output_file (str): Path to output JSON file for transformed code
        transformation_names (list): List of transformer names to apply, None for all
        include_core (bool): Whether to include core transformers
        verbose (bool): Whether to print detailed progress messages
    """
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        # Load the dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        if verbose:
            print(f"Loaded {len(dataset)} items from {input_file}")
        
        # Process each item
        transformed_dataset = []
        errors = []
        
        for i, item in enumerate(dataset):
            if verbose and i % 10 == 0:
                print(f"Processing item {i+1}/{len(dataset)}...")
                
            if 'cleaned_code' in item:
                code = item.get('cleaned_code', '')
                file_path = item.get('file_path', f"item_{i}")
                
                transformed, error = transform_code(
                    code, 
                    transformation_names=transformation_names,
                    include_core=include_core,
                    verbose=verbose
                )
                
                if transformed:
                    item['transformed_code'] = transformed
                    transformed_dataset.append(item)
                else:
                    errors.append((file_path, error))
                    if verbose:
                        print(f"Error transforming {file_path}: {error}")
        
        # Save the results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_dataset, f, indent=2)
            
        if verbose:
            print(f"Processed {len(dataset)} items with {len(errors)} errors")
            print(f"Results saved to {output_file}")
            
        # Optionally save errors to a file
        if errors:
            error_file = os.path.join(os.path.dirname(output_file), "transformation_errors.txt")
            with open(error_file, 'w', encoding='utf-8') as f:
                for file_path, error in errors:
                    f.write(f"{file_path}: {error}\n")
            if verbose:
                print(f"Errors saved to {error_file}")
                
    except Exception as e:
        print(f"Error processing dataset: {e}")