"""
Boolean Exchange: Flip the value of a boolean variable and propagate simple references.

Heuristic:
- Find a simple assignment x = True/False in a function, record mapping x -> not value
- Replace Name loads of x with UnaryOp(Not, Name(x)) or constants accordingly
"""

import ast
from ..base import BaseTransformer


class BooleanExchangeTransformer(BaseTransformer):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "boolean_exchange"
        self.verbose = verbose
        self._flip_vars = set()
        self._const_map = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # scan for x = True/False
        self._flip_vars = set()
        self._const_map = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0].id
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, bool):
                    val = stmt.value.value
                    self._const_map[target] = not val
                    self._flip_vars.add(target)
                    break
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id in self._flip_vars:
            # Replace with not x when not a known constant, else constant
            if node.id in self._const_map:
                return ast.copy_location(ast.Constant(value=self._const_map[node.id]), node)
            return ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=node.id, ctx=ast.Load())), node)
        return node
