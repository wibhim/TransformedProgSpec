"""
Switch to If: Replace Python 3.10+ match/case constructs with equivalent if/elif/else chains
for simple value patterns.

Supported patterns per case:
- MatchValue(Constant or Name): translates to subject == value
- Or patterns of MatchValue: (a | b) -> subject in (a, b)
Unsupported patterns are left unchanged (the match is returned as-is).
"""

import ast
from ..base import BaseTransformer


class SwitchToIfTransformer(BaseTransformer):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "switch_to_if"
        self.verbose = verbose

    def visit_Match(self, node: ast.Match):
        # Only handle simple subject expressions
        self.generic_visit(node)
        subject = node.subject
        if not node.cases:
            return node

        tests_bodies = []
        default_body = None

        for case in node.cases:
            pat = case.pattern
            guard = case.guard
            condition = None

            # case value
            if isinstance(pat, ast.MatchValue):
                value = pat.value
                condition = ast.Compare(left=ast.copy_location(ast.parse(ast.unparse(subject)).body[0].value, subject), ops=[ast.Eq()], comparators=[value])
            # case a | b | c
            elif isinstance(pat, ast.MatchOr) and all(isinstance(p, ast.MatchValue) for p in pat.patterns):
                values = [p.value for p in pat.patterns]
                tuple_values = ast.Tuple(elts=values, ctx=ast.Load())
                condition = ast.Compare(left=ast.copy_location(ast.parse(ast.unparse(subject)).body[0].value, subject), ops=[ast.In()], comparators=[tuple_values])
            # wildcard case _
            elif isinstance(pat, ast.MatchAs) and pat.name is None:
                default_body = case.body
                continue
            else:
                # unsupported pattern; bail out by keeping original match
                return node

            if guard is not None:
                condition = ast.BoolOp(op=ast.And(), values=[condition, guard])

            tests_bodies.append((condition, case.body))

        if not tests_bodies and default_body is None:
            return node

        # Build if/elif/else chain
        test0, body0 = tests_bodies[0]
        current = ast.If(test=test0, body=body0, orelse=[])
        chain = current
        for test, body in tests_bodies[1:]:
            new_if = ast.If(test=test, body=body, orelse=[])
            chain.orelse = [new_if]
            chain = new_if
        if default_body is not None:
            chain.orelse = default_body

        return ast.copy_location(current, node)
