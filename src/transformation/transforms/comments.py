"""
Transformer that removes comments from Python code.
"""

import ast
from ..base import BaseTransformer

class DropCommentsTransformer(BaseTransformer):
    """Transformer that removes all comments from the code."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "drop_comments"
    
    def visit(self, node):
        """Remove comments by overriding the visit method.
        
        The AST doesn't store comments, so we need to handle this differently.
        This is actually handled by the astor library during code generation.
        """
        # Process this node with parent's visit method
        return super().visit(node)
        
    def describe(self):
        return "Removes all comments from the Python code"
