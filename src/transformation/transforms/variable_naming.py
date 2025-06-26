"""
Variable renaming transformer.

This transformer renames variables to standardized names.
"""

import ast
from ..base import BaseTransformer

class VariableRenamer(BaseTransformer):
    """Transformer for renaming variables to standardized names."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.transformation_name = "variable_renamer"
        self.verbose = verbose
        self.counter = 0
        self.var_mapping = {}
    
    def visit_Name(self, node):
        """Visit a variable name and rename it if it's a target."""
        if isinstance(node.ctx, ast.Store):
            # This is an assignment, so we may want to rename
            if node.id not in self.var_mapping:
                new_name = f'var_{self.counter}'
                self.var_mapping[node.id] = new_name
                self.counter += 1
            
            node.id = self.var_mapping.get(node.id, node.id)
        elif isinstance(node.ctx, ast.Load):
            # This is a variable use, so we rename if we've seen it before
            node.id = self.var_mapping.get(node.id, node.id)
        
        return node
    
    def report(self):
        """Report the changes made by this transformer."""
        if not self.verbose:
            return ""
            
        report = f"\nVariable Renaming Report:\n"
        report += f"  {len(self.var_mapping)} variables renamed\n"
        
        if self.var_mapping:
            report += "  Mappings:\n"
            for old_name, new_name in self.var_mapping.items():
                report += f"    {old_name} -> {new_name}\n"
        
        return report
