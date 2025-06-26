"""
Transformer that replaces parentheses with spaces.
Note: This transformation is tricky with AST as it's more about syntax than structure.
"""

import re
from transformation.base import BaseTransformer

class ReplaceParenthesesTransformer(BaseTransformer):
    """Transformer that replaces parentheses with spaces."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "replace_parentheses"
    
    def transform(self, code_string):
        """Override the transform method for direct string manipulation.
        
        This can't be easily done with AST since parentheses are part of the syntax.
        
        Args:
            code_string: Original Python code as a string
            
        Returns:
            Transformed code with parentheses replaced by spaces
        """
        try:
            # Replace parentheses with spaces, but be careful with syntax
            # This is a simplified approach that will likely break valid Python syntax
            
            # Strategy: replace () with spaces but keep minimal function call syntax
            def replace_paren(match):
                # Count the number of characters and replace with same number of spaces
                return ' ' * len(match.group(0))
            
            # First, handle the easy cases - empty parentheses
            modified_code = re.sub(r'\(\s*\)', '  ', code_string)
            
            # Now handle the more complex cases
            # This is extremely simplified and will likely break syntax
            modified_code = re.sub(r'\(([^()]*)\)', r' \1 ', modified_code)
            
            return modified_code
        except Exception as e:
            print(f"Error in {self.transformation_name} transformation: {str(e)}")
            return code_string
    
    def describe(self):
        return "Replaces parentheses with spaces (warning: likely breaks syntax)"
