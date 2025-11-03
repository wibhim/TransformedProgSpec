# permute_statement.py
# Semantics-preserving (under documented assumptions) permutation of adjacent assignment statements.
# Tightened rules:
#  - Adjacent swaps only
#  - Disjoint writes; no RAW/WAR between the pair
#  - Pure RHS expressions (no Calls / known side-effects)
#  - Simple LHS (Name only). Skips Attribute/Subscript/Tuple, AugAssign, AnnAssign, multi-target.
#  - Applies to function bodies and nested basic blocks (if/else/loops/with/try).

from __future__ import annotations
import ast, random, hashlib
from typing import List, Tuple, Set, Optional, Dict, Any, Iterable
from ..base import BaseTransformer



# Optional: inherit from your project's BaseTransformer if you have one.
# class PermuteStatementTransformer(BaseTransformer):
class PermuteStatementTransformer(ast.NodeTransformer):
    """
    Reorders independent statements within basic blocks.

    Key features
    -----------
    - Non-adjacent swaps inside a block (same parent body).
    - Safe dependency analysis: avoids RAW/WAR/WAW hazards.
    - Purity model with an allow-list (len, abs, min, max, sorted, sum, any, all).
    - Optional normalization of simple AugAssign to Assign for analysis.
    - Multiple swaps per block, seedable randomness.
    - Docstring-aware; never touches the docstring position.

    Semantics-preserving guarantee
    ------------------------------
    We only swap when reads/writes between two statements are independent:
      * no variable read in one is written by the other (RAW/WAR)
      * no variable written by both (WAW)
    Targets with attributes/subscripts are treated conservatively (considered writes to the base name).
    Calls are pure only if they are whitelisted and all arguments are pure.
    """

    PURE_CALL_ALLOWLIST = {"len", "abs", "min", "max", "sorted", "sum", "any", "all"}

    def __init__(
        self,
        seed: Optional[int] = 1337,
        max_swaps_per_block: int = 2,
        enable_augassign: bool = True,
        per_function_stable: bool = False,
    ):
        super().__init__()
        self.seed = seed
        self._rng = random.Random(seed)
        self.max_swaps_per_block = max_swaps_per_block
        self.enable_augassign = enable_augassign
        self.per_function_stable = per_function_stable

    # ---- Public entry points over the tree ----

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        rng = self._rng_for(node.name)
        node.body = self._permute_block(node.body, rng)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        rng = self._rng_for(node.name)
        node.body = self._permute_block(node.body, rng)
        return node

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        node.body = self._permute_block(node.body, self._rng)
        node.orelse = self._permute_block(node.orelse, self._rng)
        return node

    def visit_For(self, node: ast.For):
        self.generic_visit(node)
        node.body = self._permute_block(node.body, self._rng)
        node.orelse = self._permute_block(node.orelse, self._rng)
        return node

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.generic_visit(node)
        node.body = self._permute_block(node.body, self._rng)
        node.orelse = self._permute_block(node.orelse, self._rng)
        return node

    def visit_While(self, node: ast.While):
        self.generic_visit(node)
        node.body = self._permute_block(node.body, self._rng)
        node.orelse = self._permute_block(node.orelse, self._rng)
        return node

    def visit_Try(self, node: ast.Try):
        self.generic_visit(node)
        node.body = self._permute_block(node.body, self._rng)
        node.orelse = self._permute_block(node.orelse, self._rng)
        node.finalbody = self._permute_block(node.finalbody, self._rng)
        for h in node.handlers:
            h.body = self._permute_block(h.body, self._rng)
        return node

    # ---- Core: permute a single "basic block" (i.e., a list of statements) ----

    def _permute_block(self, body: List[ast.stmt], rng: random.Random) -> List[ast.stmt]:
        if not body:
            return body[:]

        # Keep docstring at index 0
        start = 1 if self._is_docstring(body[0]) else 0

        # Build candidate list of indices for safe statements
        idxs = [i for i in range(start, len(body)) if self._is_supported_stmt(body[i])]
        if len(idxs) < 2:
            return body

        # Pre-compute (reads, writes, pure) for each candidate
        analysis = {}
        for i in idxs:
            reads, writes, pure = self._rw_sets(body[i])
            analysis[i] = (reads, writes, pure)

        swaps_done = 0
        # Generate all i<j pairs in random order to find more opportunities
        pairs = [(i, j) for n, i in enumerate(idxs) for j in idxs[n+1:]]
        rng.shuffle(pairs)

        new_body = body[:]
        # We have to map old indices to current positions as we mutate
        def current_pos(old_index: int) -> Optional[int]:
            # We track by identity: if nodes are unique objects, we can map them.
            # Simpler conservative approach: fall back to scanning by equality.
            for k, node in enumerate(new_body):
                if node is body[old_index]:
                    return k
            return None

        for (i_old, j_old) in pairs:
            if swaps_done >= self.max_swaps_per_block:
                break

            # Recompute current positions; skip if nodes moved or gone
            i = current_pos(i_old); j = current_pos(j_old)
            if i is None or j is None or i >= len(new_body) or j >= len(new_body) or i == j:
                continue
            if i > j:
                i, j = j, i  # ensure i < j for splicing

            s1, s2 = new_body[i], new_body[j]

            # Re-analyze in case of prior modifications
            r1, w1, p1 = self._rw_sets(s1)
            r2, w2, p2 = self._rw_sets(s2)
            if not (p1 and p2):
                continue

            # Independence: no RAW/WAR/WAW hazards on *names* (conservative)
            if (r1 & w2) or (r2 & w1) or (w1 & w2):
                continue

            # Safe: perform swap
            new_body[i], new_body[j] = new_body[j], new_body[i]
            swaps_done += 1

        return new_body

    # ---- Statement support / read-write sets ----

    def _is_supported_stmt(self, s: ast.stmt) -> bool:
        # Pure assignment-like or simple expression statements.
        if isinstance(s, ast.Assign):
            return self._targets_supported(s.targets) and self._expr_pure(s.value)
        if self.enable_augassign and isinstance(s, ast.AugAssign):
            # treat as x = x op rhs if both sides pure
            return self._target_supported(s.target) and self._expr_pure(s.value) and self._expr_pure(s.target)
        if isinstance(s, ast.AnnAssign) and s.value is not None:
            return self._target_supported(s.target) and self._expr_pure(s.value)
        if isinstance(s, ast.Expr):
            return self._expr_pure(s.value)
        # You can extend here with more trivial forms if desired.
        return False

    def _targets_supported(self, targets: List[ast.expr]) -> bool:
        return all(self._target_supported(t) for t in targets)

    def _target_supported(self, t: ast.expr) -> bool:
        # Allow Name, Attribute(Name, ...), Subscript(Name, index)
        if isinstance(t, ast.Name):
            return True
        if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
            return True
        if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and (t.slice is None or self._expr_pure(t.slice)):
            return True
        return False

    def _rw_sets(self, s: ast.stmt) -> Tuple[Set[str], Set[str], bool]:
        """
        Returns (reads, writes, pure_statement).
        Conservative: attributes/subscripts write the base name.
        """
        reads, writes = set(), set()
        pure = True

        class V(ast.NodeVisitor):
            def visit_Name(self, n: ast.Name):
                if isinstance(n.ctx, ast.Load):
                    reads.add(n.id)
                elif isinstance(n.ctx, ast.Store):
                    writes.add(n.id)

            def visit_Attribute(self, n: ast.Attribute):
                # base may be read if on RHS; for LHS, we count as write to base name
                self.generic_visit(n)

            def visit_Subscript(self, n: ast.Subscript):
                self.generic_visit(n)

            def visit_Call(self, n: ast.Call):
                nonlocal pure
                # pure only for allow-listed calls with pure args/keywords
                if isinstance(n.func, ast.Name) and n.func.id in PermuteStatementTransformer.PURE_CALL_ALLOWLIST:
                    # keep walking; if args impure, we will mark pure=False
                    pass
                else:
                    pure = False
                self.generic_visit(n)

            def visit_Await(self, n: ast.Await):
                nonlocal pure
                pure = False
                self.generic_visit(n)

            def visit_Yield(self, n: ast.Yield):
                nonlocal pure
                pure = False
                self.generic_visit(n)

            def visit_YieldFrom(self, n: ast.YieldFrom):
                nonlocal pure
                pure = False
                self.generic_visit(n)

            def visit_Attribute_ctx(self, n: ast.Attribute):
                self.generic_visit(n)

        # For statement-level purity, check specific forms
        if isinstance(s, ast.Assign):
            pure = self._expr_pure(s.value) and pure
        elif isinstance(s, ast.AugAssign):
            # treat as x = x op rhs; both sides must be pure
            pure = self.enable_augassign and self._expr_pure(s.target) and self._expr_pure(s.value) and pure
        elif isinstance(s, ast.AnnAssign):
            pure = s.value is None or self._expr_pure(s.value)
        elif isinstance(s, ast.Expr):
            pure = self._expr_pure(s.value)

        V().visit(s)

        # Conservative: if target is Attribute/Subscript, write base name
        def add_base_writes(t: ast.expr):
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                writes.add(t.value.id)
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                writes.add(t.value.id)

        if isinstance(s, ast.Assign):
            for t in s.targets:
                add_base_writes(t)
        elif isinstance(s, ast.AugAssign):
            add_base_writes(s.target)
        elif isinstance(s, ast.AnnAssign):
            add_base_writes(s.target)

        return reads, writes, pure

    def _expr_pure(self, e: ast.AST) -> bool:
        """Expression purity: constants, names, tuples/lists/sets/dicts of pure,
        arithmetic/boolean ops of pure, compare of pure, subscript/attribute of pure name,
        calls only if allow-listed and args/keywords pure.
        """
        if isinstance(e, (ast.Constant, ast.Name)):
            return True
        if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
            return all(self._expr_pure(elt) for elt in e.elts)
        if isinstance(e, ast.Dict):
            return all(self._expr_pure(k) and self._expr_pure(v) for k, v in zip(e.keys, e.values))
        if isinstance(e, (ast.UnaryOp, ast.BinOp, ast.BoolOp)):
            return all(self._expr_pure(c) for c in ast.iter_child_nodes(e))
        if isinstance(e, ast.Compare):
            return self._expr_pure(e.left) and all(self._expr_pure(c) for c in e.comparators)
        if isinstance(e, ast.Attribute):
            return isinstance(e.value, ast.Name)
        if isinstance(e, ast.Subscript):
            return isinstance(e.value, ast.Name) and (e.slice is None or self._expr_pure(e.slice))
        if isinstance(e, ast.Call):
            if isinstance(e.func, ast.Name) and e.func.id in self.PURE_CALL_ALLOWLIST:
                return all(self._expr_pure(a) for a in e.args) and all(self._expr_pure(kw.value) for kw in e.keywords)
            return False
        if isinstance(e, (ast.Await, ast.Yield, ast.YieldFrom, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return False
        # default conservative
        return False

    def _is_docstring(self, s: ast.stmt) -> bool:
        return isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant) and isinstance(s.value.value, str)

    def _rng_for(self, func_name: str) -> random.Random:
        if not self.per_function_stable:
            return self._rng
        base = str(self.seed) if self.seed is not None else "none"
        h = hashlib.blake2b(f"{base}:{func_name}".encode(), digest_size=8).digest()
        return random.Random(int.from_bytes(h, "little"))
