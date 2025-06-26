"""
Common utilities for transformers.
"""
import ast
import textwrap

# Import BaseTransformer from parent module
from ..base import BaseTransformer

def clean_code(code):
    """Clean the code by fixing whitespace and indentation."""
    return textwrap.dedent(code).strip()

def extract_function_name(node):
    """Extract function name from a call node."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
    return None
    
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