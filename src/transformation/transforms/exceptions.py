"""
Transformer that removes exception handling blocks.
"""

import ast
from ..base import BaseTransformer

class RemoveExceptionsTransformer(BaseTransformer):
    """Transformer that removes exception handling code."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "remove_exceptions"
    
    def visit_Try(self, node):
        """Remove try/except blocks, keeping only the try body."""
        # Process children
        self.generic_visit(node)
        
        # Keep only the body of the try block, discard except, else, and finally
        return node.body
    
    def visit_Raise(self, node):
        """Remove raise statements."""
        # Simply delete the raise statement
        return None
    
    def describe(self):
        return "Removes exception handling code (try/except blocks and raise statements)"
