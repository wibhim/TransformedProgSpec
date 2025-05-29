"""
Variable naming transformations for code standardization.
"""
import ast
import re
import builtins
from .common import BaseTransformer

class VariableRenamer(BaseTransformer):
    """Converts all variable names to snake_case."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.var_map = {}  # Maps original names to new names
        self.builtin_names = set(dir(builtins))
        self.verbose = verbose
    
    def to_snake_case(self, name):
        """Convert camelCase or PascalCase to snake_case."""
        if (name in self.builtin_names or name.startswith("__") 
            or name == 'self' or name == 'cls'):
            return name
            
        # Handle camelCase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Handle PascalCase
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Convert to lowercase
        return s2.lower()
    
    def visit_Name(self, node):
        """Rename variables in both definitions and references."""
        if isinstance(node.ctx, (ast.Store, ast.Load)) and node.id not in self.builtin_names:
            # Don't rename if it's already snake_case
            if node.id == self.to_snake_case(node.id):
                return node
                
            if node.id not in self.var_map:
                old_name = node.id
                self.var_map[node.id] = self.to_snake_case(node.id)
                self.log_change(f"Renamed '{old_name}' to '{self.var_map[node.id]}'")
                
            node.id = self.var_map[node.id]
            
        return node
        
    def visit_ClassDef(self, node):
        """Don't rename classes for now."""
        self.generic_visit(node)
        return node
        
    def visit_FunctionDef(self, node):
        """Optionally rename function names."""
        # Process arguments first
        self.generic_visit(node)
        
        # Only rename the function itself if needed
        old_name = node.name
        new_name = self.to_snake_case(old_name)
        
        if old_name != new_name and old_name not in self.builtin_names:
            node.name = new_name
            self.var_map[old_name] = new_name
            self.log_change(f"Renamed function '{old_name}' to '{new_name}'")
            
        return node