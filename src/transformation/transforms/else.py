"""
Transformer that removes else blocks from if statements and try statements.
"""

import ast
from transformation.base import BaseTransformer

class RemoveElseTransformer(BaseTransformer):
    """Transformer that removes else blocks."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "remove_else"
    
    def visit_If(self, node):
        """Remove the else part of if statements."""
        # Process children
        self.generic_visit(node)
        
        # Remove the else part
        node.orelse = []
        
        return node
    
    def visit_Try(self, node):
        """Remove the else part of try statements."""
        # Process children
        self.generic_visit(node)
        
        # Remove the else part, but keep the handlers (except blocks)
        node.orelse = []
        
        return node
    
    def describe(self):
        return "Removes else blocks from if statements and try statements"
