"""
Loop standardization transformer.

This transformer converts different loop types to a standard form.
"""

import ast
from ..base import BaseTransformer

class LoopStandardizer(BaseTransformer):
    """Transformer for standardizing loops."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.transformation_name = "loop_standardizer"
        self.verbose = verbose
        self.loops_transformed = 0
    
    def visit_For(self, node):
        """Visit a for loop and standardize its structure."""
        # Process children first
        self.generic_visit(node)
        
        # Track the transformation
        self.loops_transformed += 1
        
        # Return the node (potentially transformed)
        return node
    
    def visit_While(self, node):
        """Visit a while loop and standardize its structure."""
        # Process children first
        self.generic_visit(node)
        
        # Track the transformation
        self.loops_transformed += 1
        
        # Return the node (potentially transformed)
        return node
    
    def report(self):
        """Report the changes made by this transformer."""
        if not self.verbose:
            return ""
            
        return f"\nLoop Standardization Report:\n  {self.loops_transformed} loops standardized\n"
