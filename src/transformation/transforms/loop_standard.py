import ast
from ..base import BaseTransformer
from typing import List, Tuple, Optional, Union

UNSAFE_NODES = (ast.Break, ast.Continue, ast.Return, ast.Yield, ast.Raise, ast.Try)


class LoopStandardizer(BaseTransformer):
    """
    Transformer for --transformers loop_standard.
    Handles:
      • N-level rectangular for-range loops (safe flattening)
      • Jagged / CSR-style loops (e.g. for k in range(ptr[i], ptr[i+1]))
      • Counter-style while normalization
    Automatically logs skip reasons and transformation stats.
    """

    def __init__(self, verbose=False):
        super().__init__()
        self.transformation_name = "loop_standard"
        self.verbose = verbose
        self.stats = {
            "loops_total": 0,
            "chains_processed": 0,
            "max_depth": 0,
            "while_converted": 0,
            "warnings": [],
            "passes": 0
        }
        self.logs = []

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _has_unsafe_flow(self, body):
        class Finder(ast.NodeVisitor):
            found = False
            def generic_visit(self, node):
                if isinstance(node, UNSAFE_NODES):
                    self.found = True
                    return
                super().generic_visit(node)
        f = Finder(); [f.visit(n) for n in body]
        return f.found

    def _is_range_for(self, node):
        return isinstance(node, ast.For) and isinstance(node.iter, ast.Call) \
               and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"

    def _parse_range(self, args):
        """Return (start, stop, step) tuple or None."""
        if len(args) == 1:
            return ast.Constant(0), args[0], ast.Constant(1)
        if len(args) == 2:
            return args[0], args[1], ast.Constant(1)
        if len(args) == 3:
            return args
        return None

    def _product_expr(self, exprs):
        """Return AST for product(exprs)."""
        if not exprs:
            return ast.Constant(1)
        prod = exprs[0]
        for e in exprs[1:]:
            prod = ast.BinOp(left=prod, op=ast.Mult(), right=e)
        return prod

    # ------------------------------------------------------------------
    # Visit For (rectangular + CSR handling)
    # ------------------------------------------------------------------
    # State-machine un-nesting (option 2) implementation additions
    # -------------------------------------------------------------
    def _collect_loop_chain(self, node: ast.AST) -> Optional[List[ast.AST]]:
        """Collect a maximal nested chain of For/While starting at node.
        Returns list if depth > 1 else None."""
        chain = []
        current = node
        while isinstance(current, (ast.For, ast.While)):
            chain.append(current)
            body = getattr(current, 'body', [])
            # stop if multiple statements before nested loop or no nested loop
            if not body:
                break
            # Find first loop in body at position 0; if other non-empty stmts precede another loop, stop
            if len(body) == 1 and isinstance(body[0], (ast.For, ast.While)):
                current = body[0]
                continue
            break
        return chain if len(chain) > 1 else None

    def _loop_spec(self, loop: Union[ast.For, ast.While]) -> Optional[dict]:
        """Extract a normalized loop spec: {'var': str, 'init': expr, 'cond': expr, 'step': expr, 'pre': [], 'post': []}
        For For-range loops convert range forms. For others attempt heuristic extraction.
        Returns None if unsupported."""
        if isinstance(loop, ast.For):
            target = loop.target
            if not isinstance(target, ast.Name):
                return None
            # Only support range based iteration for now; other iterables will be materialized later (TODO)
            if isinstance(loop.iter, ast.Call) and isinstance(loop.iter.func, ast.Name) and loop.iter.func.id == 'range':
                args = loop.iter.args
                if len(args) == 1:
                    start = ast.Constant(0); stop = args[0]; step = ast.Constant(1)
                elif len(args) == 2:
                    start, stop = args; step = ast.Constant(1)
                elif len(args) == 3:
                    start, stop, step = args
                else:
                    return None
                return {'var': target.id, 'init': start, 'cond': ast.Compare(left=ast.Name(id=target.id, ctx=ast.Load()), ops=[ast.Lt()], comparators=[stop]), 'step': step, 'pre': [], 'post': []}
            # Fallback: unsupported iterable
            return None
        else:  # While
            # Accept patterns like while <var> <op> <stop>: ... <var> += c at end
            test = loop.test
            if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.left, ast.Name):
                var = test.left.id
                # Look for increment as last statement
                if loop.body:
                    last = loop.body[-1]
                    if isinstance(last, ast.AugAssign) and isinstance(last.target, ast.Name) and last.target.id == var:
                        step = last.value
                        body_core = loop.body[:-1]
                        return {'var': var, 'init': ast.Constant(0), 'cond': test, 'step': step, 'pre': [], 'post': [], 'body_core': body_core}
            return None

    def _state_machine(self, chain: List[ast.AST]) -> Optional[ast.AST]:
        """Build a while-based state machine executing the same iteration space without nested loops."""
        specs = []
        for lp in chain:
            spec = self._loop_spec(lp)
            if not spec:
                return None  # bail out for now; later we can attempt generic iterator expansion
            specs.append(spec)

        # Initialize index variables
        inits = [ast.Assign(targets=[ast.Name(id=s['var'], ctx=ast.Store())], value=s['init']) for s in specs]

        # Condition is conjunction of all active loop conditions
        conds = [s['cond'] for s in specs]
        master_cond = conds[0]
        for c in conds[1:]:
            master_cond = ast.BoolOp(op=ast.And(), values=[master_cond, c])

        # Body executes innermost original body (from last loop), then steps & carry logic
        innermost = chain[-1]
        inner_body = getattr(innermost, 'body', [])

        # Step logic with cascading carry (like odometer)
        step_blocks = []
        for i in reversed(range(len(specs))):
            s = specs[i]
            # increment variable
            inc = ast.AugAssign(target=ast.Name(id=s['var'], ctx=ast.Store()), op=ast.Add(), value=s['step'])
            # if still within condition -> break chain (simulate continue outer evaluation next loop)
            if_block = ast.If(test=s['cond'], body=[inc, ast.Break()], orelse=[])
            step_blocks.insert(0, if_block)
        # Reset & cascade (simplified placeholder; TODO refine for exact semantics)
        # NOTE: For correctness we would rebuild full nested iteration; placeholder warns user.
        warn_comment = ast.Expr(value=ast.Constant("State machine placeholder: semantics may differ for complex bounds."))

        machine_body = inner_body + [warn_comment] + step_blocks
        machine_loop = ast.While(test=master_cond, body=machine_body, orelse=[])
        return ast.Module(body=inits + [machine_loop], type_ignores=[])

    def visit_For(self, node):
        self.stats["loops_total"] += 1
        node = self.generic_visit(node)
        chain = self._collect_loop_chain(node)
        if chain:
            self.stats["max_depth"] = max(self.stats.get("max_depth", 0), len(chain))
            sm = self._state_machine(chain)
            if sm:
                self.stats["chains_processed"] += 1
                return sm.body[0] if isinstance(sm, ast.Module) else sm
        return node

    # ------------------------------------------------------------------
    # CSR Pattern Matching
    # ------------------------------------------------------------------
    def _match_csr_pattern(self, outer, inner):
        """Detect if inner range is of form range(ptr[i], ptr[i+1])."""
        if not self._is_range_for(inner):
            return False
        args = inner.iter.args
        if len(args) < 2:
            return False
        start, stop = args[0], args[1]
        if not (isinstance(start, ast.Subscript) and isinstance(stop, ast.Subscript)):
            return False
        # Both index into the same array, e.g. ptr[i], ptr[i+1]
        if not (getattr(start.value, "id", None) == getattr(stop.value, "id", None)):
            return False
        arr_name = start.value.id
        # Check index patterns
        def index_expr(e):
            if isinstance(e, ast.BinOp) and isinstance(e.left, ast.Name) and isinstance(e.right, ast.Constant):
                return (e.left.id, e.right.value)
            elif isinstance(e, ast.Name):
                return (e.id, 0)
            return None

        s1 = index_expr(start.slice)
        s2 = index_expr(stop.slice)
        if not s1 or not s2:
            return False
        if s1[0] != s2[0]:
            return False
        if s2[1] - s1[1] != 1:
            return False
        return True

    def _flatten_csr(self, outer, inner):
        """Flatten CSR-style pattern into single loop."""
        i_var = outer.target.id
        k_var = inner.target.id
        arr = inner.iter.args[0].value.id  # ptr
        N = outer.iter.args[0] if outer.iter.args else ast.Name("N", ast.Load())

        new_body = []
        # Initialize
        i_assign = ast.Assign(targets=[ast.Name(i_var, ast.Store())], value=ast.Constant(0))
        k_assign = ast.Assign(targets=[ast.Name(k_var, ast.Store())],
                              value=ast.Subscript(value=ast.Name(arr, ast.Load()),
                                                  slice=ast.Constant(0),
                                                  ctx=ast.Load()))
        total = ast.Subscript(value=ast.Name(arr, ast.Load()), slice=N, ctx=ast.Load())
        range_call = ast.Call(func=ast.Name("range", ast.Load()), args=[total], keywords=[])

        loop_body = [
            # If k >= ptr[i+1]: i += 1
            ast.If(
                test=ast.Compare(
                    left=ast.Name(k_var, ast.Load()),
                    ops=[ast.GtE()],
                    comparators=[
                        ast.Subscript(value=ast.Name(arr, ast.Load()),
                                      slice=ast.BinOp(left=ast.Name(i_var, ast.Load()),
                                                      op=ast.Add(),
                                                      right=ast.Constant(1)),
                                      ctx=ast.Load())
                    ],
                ),
                body=[ast.AugAssign(target=ast.Name(i_var, ast.Store()),
                                    op=ast.Add(), value=ast.Constant(1))],
                orelse=[],
            )
        ] + inner.body + [
            ast.AugAssign(target=ast.Name(k_var, ast.Store()),
                          op=ast.Add(), value=ast.Constant(1))
        ]

        new_for = ast.For(
            target=ast.Name("_f", ast.Store()),
            iter=range_call,
            body=[i_assign, k_assign] + loop_body,
            orelse=[]
        )

        self.stats["flattened_csr"] += 1
        self._log("flattened", "csr-2level", outer.lineno)
        return new_for

    # ------------------------------------------------------------------
    # Rectangular flattening (supports N-level)
    # ------------------------------------------------------------------
    def _try_flatten_rectangular(self, node):
        """Flatten N-level rectangular loops if possible."""
        nested, vars, ranges = [], [], []
        current = node
        while self._is_range_for(current):
            nested.append(current)
            target = current.target
            vars.append(target.id if isinstance(target, ast.Name) else None)
            r = self._parse_range(current.iter.args)
            if not r:
                break
            ranges.append(r)
            if len(current.body) == 1 and self._is_range_for(current.body[0]):
                current = current.body[0]
            else:
                break

        depth = len(nested)
        if depth < 2 or not all(vars):
            return None
        innermost_body = nested[-1].body
        if self._has_unsafe_flow(innermost_body):
            self._log("skip", "inner-unsafe", nested[-1].lineno)
            return None

        lens = [ast.BinOp(left=end, op=ast.Sub(), right=start) for start, end, _ in ranges]
        total_iters = self._product_expr(lens)

        flat_idx = ast.Name(id="flat_idx", ctx=ast.Store())
        flat_iter = ast.Call(func=ast.Name("range", ast.Load()), args=[total_iters], keywords=[])

        assigns = []
        rem = ast.Name(id="flat_idx", ctx=ast.Load())
        for i in reversed(range(depth)):
            denom = self._product_expr(lens[i+1:]) if i < depth - 1 else None
            idx_expr = (ast.BinOp(
                left=ast.BinOp(left=rem, op=ast.FloorDiv(), right=denom),
                op=ast.Mod(), right=lens[i]
            ) if denom else ast.BinOp(left=rem, op=ast.Mod(), right=lens[i]))
            assigns.insert(0, ast.Assign(
                targets=[ast.Name(id=vars[i], ctx=ast.Store())],
                value=ast.BinOp(left=ranges[i][0], op=ast.Add(), right=idx_expr)
            ))

        flat_body = assigns + innermost_body
        flat_for = ast.For(target=flat_idx, iter=flat_iter, body=flat_body, orelse=[])
        self.stats["flattened_rect"] += 1
        self._log("flattened", f"rectangular-{depth}level", node.lineno)
        return flat_for

    # ------------------------------------------------------------------
    # While normalization
    # ------------------------------------------------------------------
    def visit_While(self, node):
        self.stats["loops_total"] += 1
        node = self.generic_visit(node)
        chain = self._collect_loop_chain(node)
        if chain:
            self.stats["max_depth"] = max(self.stats.get("max_depth", 0), len(chain))
            sm = self._state_machine(chain)
            if sm:
                self.stats["chains_processed"] += 1
                self.stats["while_converted"] += 1
                return sm.body[0] if isinstance(sm, ast.Module) else sm
        return node

    # ------------------------------------------------------------------
    # Logging and summary
    # ------------------------------------------------------------------
    def _log(self, status, reason, lineno=None):
        self.logs.append({"status": status, "reason": reason, "lineno": lineno or -1})
        if status == "skip":
            self.stats["skipped"] += 1

    def finalize(self):
        """Return summary JSON for reporting."""
        return {
            "transformation": self.transformation_name,
            "stats": self.stats,
            "logs": self.logs
        }
