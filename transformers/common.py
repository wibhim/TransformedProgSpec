"""
Common utilities and base classes for transformers.
"""
import ast
import textwrap

class BaseTransformer(ast.NodeTransformer):
    """Base class for all transformers with common functionality."""
    
    def __init__(self):
        super().__init__()
        self.changes_made = 0
    
    def log_change(self, message=None):
        """Track changes made by this transformer."""
        self.changes_made += 1
        if message and hasattr(self, 'verbose') and self.verbose:
            print(f"[{self.__class__.__name__}] {message}")
    
    def report(self):
        """Report the number of changes made."""
        return f"{self.__class__.__name__}: {self.changes_made} changes"

def clean_code(code):
    """Pre-process code before transformation."""
    # Replace tabs with spaces
    code = code.replace('\t', '    ')
    # Dedent the code to remove common leading whitespace
    code = textwrap.dedent(code)
    return code

def get_all_variable_names(node):
    """Extract all variable names from an AST node."""
    names = set()
    for sub_node in ast.walk(node):
        if isinstance(sub_node, ast.Name):
            names.add(sub_node.id)
    return names

def parent_child_map(tree):
    """Create a mapping from child nodes to parent nodes."""
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents