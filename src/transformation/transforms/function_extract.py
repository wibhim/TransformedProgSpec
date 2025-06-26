"""
Function extraction transformer.

This transformer extracts inline logic into separate functions.
"""

import ast
from ..base import BaseTransformer

class FunctionExtractor(BaseTransformer):
    """Transformer for extracting logic into separate functions."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.transformation_name = "function_extractor"
        self.verbose = verbose
        self.functions_extracted = 0
    
    def visit_Module(self, node):
        """Visit module and extract functions."""
        # Process children first
        self.generic_visit(node)
        
        # Return the node (potentially transformed)
        return node
    
    def report(self):
        """Report the changes made by this transformer."""
        if not self.verbose:
            return ""
            
        return f"\nFunction Extraction Report:\n  {self.functions_extracted} functions extracted\n"
