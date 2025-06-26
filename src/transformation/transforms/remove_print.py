"""
Transformer that removes print statements.
"""

import ast
from transformation.base import BaseTransformer

class RemovePrintTransformer(BaseTransformer):
    """Transformer that removes all print statements."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "remove_print"
    
    def visit_Call(self, node):
        """Remove print function calls."""
        # Process children
        self.generic_visit(node)
        
        # Check if this is a print function call
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            # Return None to remove the node
            return None
        
        return node
    
    def describe(self):
        return "Removes all print statements from the code"
