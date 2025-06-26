"""
Base transformer module for Python code transformation testing.
This provides common functionality for all transformation classes.
"""

import ast
import astor

class BaseTransformer(ast.NodeTransformer):
    """Base class for all transformers."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "base"  # Override in subclasses
    
    def transform(self, code_string):
        """Transform Python code string and return the modified code.
        
        Args:
            code_string: Original Python code as a string
            
        Returns:
            Transformed Python code as a string
        """
        try:
            # Parse the Python code into an AST
            tree = ast.parse(code_string)
            
            # Apply the transformation (using visit method from NodeTransformer)
            transformed_tree = self.visit(tree)
            
            # Convert back to source code
            transformed_code = astor.to_source(transformed_tree)
            
            return transformed_code
        except Exception as e:
            # Return original code if transformation fails
            print(f"Error in {self.transformation_name} transformation: {str(e)}")
            return code_string
            
    def describe(self):
        """Return a description of the transformation."""
        return f"Base transformer that doesn't modify code"
