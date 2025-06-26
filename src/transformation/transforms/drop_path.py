"""
Transformer that removes import paths and simplifies imports.
"""

import ast
from transformation.base import BaseTransformer

class DropPathTransformer(BaseTransformer):
    """Transformer that removes import paths and simplifies imports."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "drop_path"
    
    def visit_Import(self, node):
        """Simplify import statements."""
        # Process children
        self.generic_visit(node)
        
        # Keep imports but simplify them if they have paths
        for alias in node.names:
            # For imports like "import path.to.module"
            # Change to "import module"
            if '.' in alias.name:
                alias.name = alias.name.split('.')[-1]
        
        return node
    
    def visit_ImportFrom(self, node):
        """Simplify import from statements."""
        # Process children
        self.generic_visit(node)
        
        # Change "from path.to.module import X" to "from module import X"
        if node.module and '.' in node.module:
            node.module = node.module.split('.')[-1]
            node.level = 0
        
        return node
    
    def describe(self):
        return "Removes import paths and simplifies imports"
