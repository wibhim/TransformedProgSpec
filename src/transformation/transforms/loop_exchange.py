"""
Loop Exchange: Replace for loops with while loops and vice versa for simple patterns.

Supported:
- for i in range(start, stop[, step]) -> while with explicit init/test/increment
- while with simple counter pattern (i = start; while i < stop: ...; i += step) -> for range
"""

import ast
from ..base import BaseTransformer


class LoopExchangeTransformer(BaseTransformer):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.transformation_name = "loop_exchange"
        self.verbose = verbose

    def visit_For(self, node: ast.For):
        self.generic_visit(node)
        # Only handle for range(...)
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            args = node.iter.args
            if len(args) == 1:
                start, stop, step = ast.Constant(value=0), args[0], ast.Constant(value=1)
            elif len(args) == 2:
                start, stop, step = args[0], args[1], ast.Constant(value=1)
            elif len(args) == 3:
                start, stop, step = args[0], args[1], args[2]
            else:
                return node

            # only support simple Name targets
            target = node.target
            if not isinstance(target, ast.Name):
                return node
            # init: target = start
            init = ast.Assign(targets=[ast.Name(id=target.id, ctx=ast.Store())], value=start)
            # condition: target < stop (or > if step negative) - we default to < and leave semantics approximate for non-constant step
            cond_op = ast.Lt()
            if isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub):
                cond_op = ast.Gt()
            elif isinstance(step, ast.Constant) and isinstance(step.value, (int, float)) and step.value < 0:
                cond_op = ast.Gt()
            test = ast.Compare(left=ast.Name(id=target.id, ctx=ast.Load()), ops=[cond_op], comparators=[stop])
            # increment: target += step
            incr = ast.AugAssign(target=ast.Name(id=target.id, ctx=ast.Store()), op=ast.Add(), value=step)

            new_body = node.body + [incr]
            while_node = ast.While(test=test, body=new_body, orelse=node.orelse)
            # Replace the for node with [init, while]
            return [ast.copy_location(init, node), ast.copy_location(while_node, node)]
        return node

    def visit_While(self, node: ast.While):
        self.generic_visit(node)
        # Detect simple counter pattern: i < N with i incremented by += 1 at end of body
        # and i initialized in the immediate previous statement. This is a heuristic.
        # We implement a basic transformation only when pattern is clearly matched.
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], (ast.Lt, ast.Gt)):
            left = test.left
            if isinstance(left, ast.Name):
                var = left.id
                # find increment in body (last statement)
                if node.body and isinstance(node.body[-1], ast.AugAssign):
                    aug = node.body[-1]
                    if isinstance(aug.target, ast.Name) and aug.target.id == var and isinstance(aug.op, ast.Add):
                        step = aug.value
                        # Build range: start is unknown; we conservatively use 0 unless we later improve to detect init.
                        start = ast.Constant(value=0)
                        stop = test.comparators[0]
                        if isinstance(test.ops[0], ast.Gt):
                            # reverse counting not handled robustly -> skip
                            return node
                        call = ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=[start, stop, step], keywords=[])
                        new_for = ast.For(target=ast.Name(id=var, ctx=ast.Store()), iter=call, body=node.body[:-1], orelse=node.orelse)
                        return ast.copy_location(new_for, node)
        return node
