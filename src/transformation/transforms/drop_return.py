"""
Transformer that removes return statements from functions.
"""

import ast
from transformation.base import BaseTransformer

class DropReturnTransformer(BaseTransformer):
    """Transformer that removes return statements from functions."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "drop_return"
    
    def visit_Return(self, node):
        """Remove return statements or convert them to expressions."""
        # If the return has a value, keep the expression but drop the return
        if node.value:
            return ast.Expr(value=node.value)
        
        # If it's just a plain return, remove it entirely
        return None
    
    def describe(self):
        return "Removes return statements from functions"
