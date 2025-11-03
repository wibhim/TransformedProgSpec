"""
Insert a simple log statement at a random location inside function bodies.

We keep logging lightweight (print) to avoid import side-effects.
"""

import ast
import random
from ..base import BaseTransformer


class LogStatementTransformer(BaseTransformer):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "log_statement"
        self.verbose = verbose
        self._rng = random.Random()

    def _insert_log(self, body):
        log_stmt = ast.parse("print('LOG: reached')").body[0]
        idx = self._rng.randrange(0, len(body) + 1) if body else 0
        body.insert(idx, log_stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        self._insert_log(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        self._insert_log(node.body)
        return node
