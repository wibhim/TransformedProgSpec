"""
Transformer that removes variable declarations or just their initializations.
"""

import ast
from ..base import BaseTransformer

class DropVarsTransformer(BaseTransformer):
    """Transformer that removes variable declarations or initializations."""
    
    def __init__(self, drop_type='initialization'):
        """Initialize with the type of drop to perform.
        
        Args:
            drop_type: Either 'declaration' to remove the entire variable 
                     declaration or 'initialization' to just remove the value.
        """
        super().__init__()
        self.transformation_name = "drop_vars"
        self.drop_type = drop_type
    
    def visit_Assign(self, node):
        """Handle assignment statements."""
        # Process children
        self.generic_visit(node)
        
        if self.drop_type == 'declaration':
            # Remove the whole variable assignment
            return None
        elif self.drop_type == 'initialization':
            # Replace the value with a placeholder (None)
            node.value = ast.Constant(value=None)
        
        return node
    
    def visit_AnnAssign(self, node):
        """Handle annotated assignments (with type hints)."""
        # Process children
        self.generic_visit(node)
        
        if self.drop_type == 'declaration':
            # Remove the whole variable assignment
            return None
        elif self.drop_type == 'initialization' and node.value:
            # Replace the value with None but keep the type annotation
            node.value = ast.Constant(value=None)
        
        return node
    
    def describe(self):
        if self.drop_type == 'declaration':
            return "Removes variable declarations completely"
        else:
            return "Removes variable initializations, leaving them uninitialized"
