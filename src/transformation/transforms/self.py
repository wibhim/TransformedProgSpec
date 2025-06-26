"""
Transformer that removes 'self' parameters and references from methods.
"""

import ast
from ..base import BaseTransformer

class DropSelfTransformer(BaseTransformer):
    """Transformer that removes all 'self' parameters and references."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "drop_self"
    
    def visit_FunctionDef(self, node):
        """Remove 'self' from function parameters."""
        # Process the function recursively
        self.generic_visit(node)
        
        # Remove 'self' from arguments if it exists
        if node.args.args and len(node.args.args) > 0:
            # Check if first argument is self (typical for methods)
            if node.args.args[0].arg == 'self':
                node.args.args = node.args.args[1:]
        
        return node
    
    def visit_Attribute(self, node):
        """Remove 'self.' prefixes from attribute references."""
        # Process children
        self.generic_visit(node)
        
        # Check if this is a self.something attribute
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            # Replace self.attr with just attr
            return ast.Name(id=node.attr, ctx=node.ctx)
        
        return node
    
    def describe(self):
        return "Removes 'self' parameters and references from methods"
