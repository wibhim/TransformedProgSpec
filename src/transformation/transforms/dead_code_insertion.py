import ast, random, hashlib
from typing import Iterable, Set, Literal
from ..base import BaseTransformer

PositionPolicy = Literal["random", "top", "middle", "bottom"]

class DeadCodeInsertionTransformer(BaseTransformer):
    def __init__(
        self,
        verbose: bool = False,
        seed: int | None = None,                # None => new randomness each run
        position_policy: PositionPolicy = "random",
        payload_kinds: Iterable[str] = ("assign", "call", "loop"),
        p_insert: float = 1.0,                  # prob a given function gets any insertion
        min_inserts: int = 1,                   # random count of blocks per function
        max_inserts: int = 1,                   # e.g., set to 3 for 1–3 blocks
        per_function_stable: bool = False,      # True => random but stable per function
    ):
        super().__init__()
        self.transformation_name = "dead_code_insertion"
        self.verbose = verbose
        self.global_seed = seed
        self.position_policy = position_policy
        self.payload_kinds = tuple(payload_kinds)
        self.p_insert = float(p_insert)
        self.min_inserts = int(min_inserts)
        self.max_inserts = int(max_inserts)
        self.per_function_stable = per_function_stable
        self._rng = random.Random(seed)
        self._counter = 0

    # --------- random helpers ---------
    def _rng_for_func(self, func_name: str) -> random.Random:
        if not self.per_function_stable:
            return self._rng
        # derive a stable sub-seed per function (works even when global seed is None)
        base = str(self.global_seed) if self.global_seed is not None else "none"
        h = hashlib.blake2b(f"{base}:{func_name}".encode(), digest_size=8).digest()
        sub_seed = int.from_bytes(h, "little")
        return random.Random(sub_seed)

    # --------- name and position helpers ---------
    def _fresh_name(self, taken: Set[str]) -> str:
        while True:
            cand = f"_unused_{self._counter}"
            self._counter += 1
            if cand not in taken:
                return cand

    def _collect_local_names(self, body: list[ast.stmt]) -> Set[str]:
        names: Set[str] = set()
        class V(ast.NodeVisitor):
            def visit_Name(self, n: ast.Name):
                if isinstance(n.ctx, ast.Store):
                    names.add(n.id)
        for s in body:
            V().visit(s)
        return names

    def _choose_index(self, body_len: int, rng: random.Random, start_idx: int) -> int:
        if body_len <= start_idx:
            return start_idx
        if self.position_policy == "top":
            return max(start_idx, 1)
        if self.position_policy == "middle":
            return max(start_idx, body_len // 2)
        if self.position_policy == "bottom":
            return body_len
        # random position each insertion
        return rng.randrange(start_idx, body_len + 1)

    # --------- payloads (always unreachable via if False) ---------
    def _make_payload(self, rng: random.Random, varname: str) -> ast.stmt:
        kind = rng.choice(self.payload_kinds)
        if kind == "assign":
            inner = ast.Assign(targets=[ast.Name(id=varname, ctx=ast.Store())],
                               value=ast.Constant(value=0))
        elif kind == "call":
            inner = ast.Expr(value=ast.Call(
                func=ast.Lambda(args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
                                                   kw_defaults=[], defaults=[]),
                                body=ast.Constant(value=None)),
                args=[], keywords=[]))
        elif kind == "loop":
            inner = ast.For(target=ast.Name(id="_i", ctx=ast.Store()),
                            iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()),
                                          args=[ast.Constant(value=0)], keywords=[]),
                            body=[ast.Pass()], orelse=[])
        else:
            inner = ast.Pass()
        return ast.If(test=ast.Constant(value=False), body=[inner], orelse=[])

    # --------- insertion core ---------
    def _insert_dead_once(self, body: list[ast.stmt], rng: random.Random) -> None:
        # keep docstring in place
        start_idx = 1 if body and isinstance(body[0], ast.Expr) \
            and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str) else 0

        idx = self._choose_index(len(body), rng, start_idx)
        taken = self._collect_local_names(body)
        name = self._fresh_name(taken)
        wrapped = self._make_payload(rng, name)
        body.insert(idx, wrapped)

    # --------- visitors ---------
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        rng = self._rng_for_func(node.name)
        if rng.random() <= self.p_insert:
            count = rng.randint(self.min_inserts, self.max_inserts)
            for _ in range(count):
                self._insert_dead_once(node.body, rng)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        rng = self._rng_for_func(node.name)
        if rng.random() <= self.p_insert:
            count = rng.randint(self.min_inserts, self.max_inserts)
            for _ in range(count):
                self._insert_dead_once(node.body, rng)
        return node
