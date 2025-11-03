"""
Transformer that removes docstrings from Python code.
"""

import ast
from ..base import BaseTransformer

class RemoveDocstringsTransformer(BaseTransformer):
    """Transformer that removes all docstrings from the code."""
    
    def __init__(self):
        super().__init__()
        self.transformation_name = "remove_docstrings"
        self.docstrings_removed = 0
    
    def visit_Module(self, node):
        """Remove module-level docstrings."""
        # Process children first
        self.generic_visit(node)
        
        # Check if the first statement is a docstring
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            # Remove the module docstring
            node.body = node.body[1:]
            self.docstrings_removed += 1
            
        return node
    
    def visit_FunctionDef(self, node):
        """Remove function docstrings."""
        # Process children first
        self.generic_visit(node)
        
        # Check if the first statement in the function body is a docstring
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            # Remove the function docstring
            node.body = node.body[1:]
            self.docstrings_removed += 1
            
        return node
    
    def visit_AsyncFunctionDef(self, node):
        """Remove async function docstrings."""
        # Process children first
        self.generic_visit(node)
        
        # Check if the first statement in the function body is a docstring
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            # Remove the async function docstring
            node.body = node.body[1:]
            self.docstrings_removed += 1
            
        return node
    
    def visit_ClassDef(self, node):
        """Remove class docstrings."""
        # Process children first
        self.generic_visit(node)
        
        # Check if the first statement in the class body is a docstring
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            # Remove the class docstring
            node.body = node.body[1:]
            self.docstrings_removed += 1
            
        return node
    
    def report(self):
        """Report transformation results."""
        if self.docstrings_removed > 0:
            return f"Removed {self.docstrings_removed} docstrings"
        return None
    
    def describe(self):
        return "Removes all docstrings from modules, classes, and functions"
