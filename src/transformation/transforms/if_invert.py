# transformers/if_invert_condition.py
import ast
from ..base import BaseTransformer

class IfInvertConditionTransformer(BaseTransformer):
    """
    if_invert_condition:
      Invert the condition of each if-statement and swap its branches.

    Examples:
        Before:
            if cond:
                work()
        After:
            if not cond:
                pass
            else:
                work()

        Before:
            if cond:
                a()
            else:
                b()
        After:
            if not cond:
                b()
            else:
                a()

    Motivation:
      • Produces a structural variant (inverted guard) while preserving semantics.
      • Increases dataset diversity for control-flow learning.
      • Useful for examining condition polarity and specification symmetry.
    """

    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "if_invert_condition"
        self.verbose = verbose
        self.changed = False

    def visit_If(self, node: ast.If):
        # Transform nested Ifs first
        self.generic_visit(node)

        # Build the negated condition
        negated = ast.UnaryOp(op=ast.Not(), operand=node.test)

        # Swap bodies
        orig_body = node.body
        orig_else = node.orelse if node.orelse else [ast.Pass()]

        node.test = negated
        node.body = orig_else
        node.orelse = orig_body
        self.changed = True

        if self.verbose:
            print(f"🔄 Inverted if-condition at line {getattr(node, 'lineno', '?')}")

        return node

    def transform_code(self, code: str) -> str:
        """Parse, apply transformation, and return new code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        self.changed = False
        tree = self.visit(tree)
        ast.fix_missing_locations(tree)
        new_code = self.unparse(tree)
        return new_code
