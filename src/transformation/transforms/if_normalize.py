# transformers/if_normalize.py
import ast
from ..base import BaseTransformer

class IfNormalizeTransformer(BaseTransformer):
    """
    if_normalize: A conservative, single-pass normalizer for if/elif/else.

    Rewrites:
      - De Morgan (push single 'not' inward):  if not (A and B) -> if (not A) or (not B)
      - Positivity swap:                      if not A: X else: Y -> if A: Y else: X
      - Nested->AND (clean shape only):       if A: if B: BODY -> if A and B: BODY
      - Remove redundant else w/ hoist:       if-branch always terminates -> drop 'else' and hoist body

    Notes:
      * Safe, structure-preserving; skips complex shapes it can't guarantee.
      * Hoisting requires touching the parent block; handled in *_rewrite_block methods.
    """
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "if_normalize"
        self.verbose = verbose

    # ------------ small helpers ------------
    @staticmethod
    def _is_terminating(stmt: ast.stmt) -> bool:
        return isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue))

    @classmethod
    def _body_always_terminates(cls, body) -> bool:
        if not body:
            return False
        last = body[-1]
        if cls._is_terminating(last):
            return True
        if isinstance(last, ast.If):
            return cls._body_always_terminates(last.body) and cls._body_always_terminates(last.orelse)
        return False

    @staticmethod
    def _is_not(expr: ast.expr) -> bool:
        return isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not)

    @staticmethod
    def _is_and(expr: ast.expr) -> bool:
        return isinstance(expr, ast.BoolOp) and isinstance(expr.op, ast.And) and len(expr.values) >= 2

    @staticmethod
    def _demorgan_once(expr: ast.expr) -> ast.expr:
        # Only one level to avoid aggressive changes
        if not (isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not)):
            return expr
        inner = expr.operand
        if isinstance(inner, ast.BoolOp) and isinstance(inner.op, (ast.And, ast.Or)):
            new_op = ast.Or() if isinstance(inner.op, ast.And) else ast.And()
            new_vals = []
            for v in inner.values:
                if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not):
                    new_vals.append(v.operand)
                else:
                    new_vals.append(ast.UnaryOp(op=ast.Not(), operand=v))
            return ast.BoolOp(op=new_op, values=new_vals)
        return expr

    # ------------ core node visitors ------------
    def visit_If(self, node: ast.If):
        # First recurse so children are normalized before this level
        self.generic_visit(node)

        # (1) De Morgan (push single 'not' inward)
        node.test = self._demorgan_once(node.test)

        # (2) Positivity swap (only when else exists)
        if node.orelse and self._is_not(node.test):
            node.test = node.test.operand
            node.body, node.orelse = node.orelse, node.body

        # (3) Collapse clean nested-if to A and B (outer: no else, inner: single If, no else)
        if not node.orelse and len(node.body) == 1 and isinstance(node.body[0], ast.If):
            inner = node.body[0]
            if not inner.orelse:
                node.test = ast.BoolOp(op=ast.And(), values=[node.test, inner.test])
                node.body = inner.body

        # (4) Remove redundant else when if-branch always terminates -> mark for hoist
        if node.orelse and self._body_always_terminates(node.body):
            setattr(node, "__hoist_else__", True)  # parent block will hoist and clear orelse later

        return node

    # ------------ block rewriters for hoisting ------------
    def _rewrite_block(self, body):
        """Hoist 'else' bodies for If nodes marked with __hoist_else__."""
        new_body = []
        for stmt in body:
            if isinstance(stmt, ast.If) and getattr(stmt, "__hoist_else__", False):
                setattr(stmt, "__hoist_else__", False)
                # keep the If as-is but drop its else; append else-body after it
                new_body.append(stmt)
                for extra in stmt.orelse:
                    new_body.append(extra)
                stmt.orelse = []
            else:
                new_body.append(stmt)
        return new_body

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    def visit_Module(self, node: ast.Module):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    # Also handle blocks inside loops/with/try so hoists work there too
    def visit_For(self, node: ast.For):
        node.body = self._rewrite_block(node.body)
        node.orelse = self._rewrite_block(node.orelse)
        return self.generic_visit(node)

    def visit_While(self, node: ast.While):
        node.body = self._rewrite_block(node.body)
        node.orelse = self._rewrite_block(node.orelse)
        return self.generic_visit(node)

    def visit_With(self, node: ast.With):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        node.body = self._rewrite_block(node.body)
        return self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        node.body = self._rewrite_block(node.body)
        node.orelse = self._rewrite_block(node.orelse)
        node.finalbody = self._rewrite_block(node.finalbody)
        for h in node.handlers:
            h.body = self._rewrite_block(h.body)
        return self.generic_visit(node)
