"""
Transformer that removes print statements.
"""

import ast
from ..base import BaseTransformer

class RemovePrintTransformer(BaseTransformer):
    """Transformer that removes all print statements."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "remove_print"
        self.print_count = 0
    
    def visit_Expr(self, node):
        """Check if the expression is a print call."""
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
            self.print_count += 1
            # Replace print statement with pass statement
            return ast.Pass()
        return self.generic_visit(node)
    
    def report(self):
        """Report transformation results."""
        if self.print_count > 0:
            return f"Removed {self.print_count} print statements"
        return None
    
    def describe(self):
        return "Removes all print statements from the code"
