"""
Reorder Condition: Swap left and right parts of a binary condition.

We handle:
- Compare nodes with a single operator (e.g., a < b -> b > a)
- BoolOp with And/Or: reverse the operands order
"""

import ast
from ..base import BaseTransformer


def invert_op(op):
    # Invert comparison direction
    mapping = {
        ast.Lt: ast.Gt,
        ast.Gt: ast.Lt,
        ast.LtE: ast.GtE,
        ast.GtE: ast.LtE,
        ast.Eq: ast.Eq,
        ast.NotEq: ast.NotEq,
        ast.Is: ast.Is,
        ast.IsNot: ast.IsNot,
        ast.In: ast.In,      # cannot invert symmetrically without swapping contains
        ast.NotIn: ast.NotIn,
    }
    return mapping.get(type(op), type(op))()


class ReorderConditionTransformer(BaseTransformer):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "reorder_condition"
        self.verbose = verbose

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        test = node.test
        node.test = self._reorder(test)
        return node

    def visit_While(self, node: ast.While):
        self.generic_visit(node)
        node.test = self._reorder(node.test)
        return node

    def _reorder(self, expr: ast.AST) -> ast.AST:
        # Compare with single operator
        if isinstance(expr, ast.Compare) and len(expr.ops) == 1 and len(expr.comparators) == 1:
            left = expr.left
            op = expr.ops[0]
            right = expr.comparators[0]
            new_op = invert_op(op)
            return ast.Compare(left=right, ops=[new_op], comparators=[left])
        # BoolOp: just reverse order of values
        if isinstance(expr, ast.BoolOp) and isinstance(expr.op, (ast.And, ast.Or)):
            return ast.BoolOp(op=expr.op, values=list(reversed(expr.values)))
        return expr
