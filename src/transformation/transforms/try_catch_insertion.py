import ast, random, hashlib
from ..base import BaseTransformer




class TryCatchInsertionTransformer(BaseTransformer):
    def __init__(self, verbose: bool=False, seed: int|None=None,
                 p_insert: float=1.0, min_inserts:int=1, max_inserts:int=1,
                 per_function_stable: bool=False, mode: str="reraising"):
        super().__init__()
        self.transformation_name = "try_catch_insertion"
        self.verbose = verbose
        self._rng = random.Random(seed)
        self._seed = seed
        self.p_insert, self.min_inserts, self.max_inserts = p_insert, min_inserts, max_inserts
        self.per_function_stable = per_function_stable
        self.mode = mode  # "reraising" (default) | "masking" | "finally"

    def _rng_for(self, funcname: str) -> random.Random:
        if not self.per_function_stable: return self._rng
        base = str(self._seed) if self._seed is not None else "none"
        h = hashlib.blake2b(f"{base}:{funcname}".encode(), digest_size=8).digest()
        return random.Random(int.from_bytes(h, "little"))

    def _is_docstring(self, stmt: ast.stmt) -> bool:
        return isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str)

    def _make_handler(self) -> ast.excepthandler:
        if self.mode == "masking":
            body = [ast.Pass()]
        elif self.mode == "finally":
            # not used here; see _wrap_stmt for finally path
            body = [ast.Pass()]
        else:  # "reraising"
            body = [ast.Raise(exc=None, cause=None)]
        return ast.ExceptHandler(type=ast.Name(id="Exception", ctx=ast.Load()), name=None, body=body)

    def _wrap_stmt(self, stmt: ast.stmt) -> ast.stmt:
        if self.mode == "finally":
            node = ast.Try(body=[stmt], handlers=[], orelse=[], finalbody=[ast.Pass()])
        else:
            node = ast.Try(body=[stmt], handlers=[self._make_handler()], orelse=[], finalbody=[])
        ast.copy_location(node, stmt)
        ast.fix_missing_locations(node)
        return node

    def _wrap_random_stmt(self, body: list[ast.stmt], rng: random.Random):
        if not body: return
        start = 1 if body and self._is_docstring(body[0]) else 0
        candidates = [i for i in range(start, len(body)) if not isinstance(body[i], ast.Pass)]
        if not candidates: return
        idx = rng.choice(candidates)
        body[idx] = self._wrap_stmt(body[idx])

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        rng = self._rng_for(node.name)
        if rng.random() <= self.p_insert:
            for _ in range(rng.randint(self.min_inserts, self.max_inserts)):
                self._wrap_random_stmt(node.body, rng)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        rng = self._rng_for(node.name)
        if rng.random() <= self.p_insert:
            for _ in range(rng.randint(self.min_inserts, self.max_inserts)):
                self._wrap_random_stmt(node.body, rng)
        return node
