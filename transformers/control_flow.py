"""
Control flow transformations to simplify code structure.
Includes flattening nested conditionals, guard clauses, etc.
"""
import ast
from .common import BaseTransformer

class ControlFlowSimplifier(BaseTransformer):
    """Simplifies complex control flow structures."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose
    
    def visit_FunctionDef(self, node):
        """Mark all If nodes with their parent function."""
        self.generic_visit(node)
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                child.parent_function = node
        return node
    
    def visit_If(self, node):
        """Convert nested if-else structures to guard clauses where possible."""
        self.generic_visit(node)  # Transform any nested nodes first
        
        # Check if this is not a return-based guard already
        if hasattr(node, 'parent_function') and not (
            len(node.body) == 1 and isinstance(node.body[0], ast.Return)
        ):
            # Simplify "if X: return Y" patterns - convert to early returns
            if node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.Return):
                # Move the else's return to an if with negated condition
                new_if = ast.If(
                    test=ast.UnaryOp(op=ast.Not(), operand=node.test),
                    body=node.orelse,
                    orelse=[],
                    lineno=node.lineno
                )
                
                # Create a new node list with the new if followed by the original if's body
                result = [new_if] + node.body
                self.log_change("Converted else-return to guard clause")
                return result
                
            # Check if it's a nested if structure that can be flattened
            if node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                inner_if = node.orelse[0]
                
                # Create a new condition that combines the negation of the outer condition
                # with the inner condition
                new_cond = ast.BoolOp(
                    op=ast.And(),
                    values=[
                        ast.UnaryOp(op=ast.Not(), operand=node.test),
                        inner_if.test
                    ]
                )
                
                # Create a new if statement with the combined condition and the inner body
                new_if = ast.If(
                    test=new_cond,
                    body=inner_if.body,
                    orelse=inner_if.orelse,
                    lineno=node.lineno
                )
                
                # Return both the original if and the new flattened if
                node.orelse = []
                self.log_change("Flattened nested if-else structure")
                return [node, new_if]
                
        return node