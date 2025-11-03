"""
Transformer that replaces parentheses with spaces.
Note: This transformation is tricky with AST as it's more about syntax than structure.
"""

import re
import ast
from src.transformation.base import BaseTransformer

class ReplaceParenthesesTransformer(BaseTransformer):
    """Transformer that replaces parentheses with spaces."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "replace_parentheses"
    
    def transform(self, code_string):
        """Override the transform method to remove all parentheses from the code string."""
        try:
            # Remove all '(' and ')' characters from the code string
            modified_code = code_string.replace('(', '').replace(')', '')
            return modified_code
        except Exception as e:
            print(f"Error in {self.transformation_name} transformation: {str(e)}")
            return code_string
    
    def visit(self, node):
        """Override the visit method to handle AST nodes."""
        # First use the standard visitor pattern to traverse the AST
        node = super().visit(node)
        
        # Then, after getting the AST back, convert it to source code,
        # apply our string-based transformation, and parse it back to AST
        try:
            # Convert the AST to source code
            code = ast.unparse(node)
            
            # Apply our string transformation to remove parentheses
            transformed_code = self.transform(code)
            
            # Parse the transformed code back to an AST
            return ast.parse(transformed_code)
        except Exception as e:
            print(f"Error in {self.transformation_name} AST transformation: {str(e)}")
            return node
    
    def describe(self):
        return "Replaces parentheses with spaces (warning: likely breaks syntax)"
