import ast, pathlib, json, os, textwrap, builtins
from typing import List, Set, Dict, Tuple

# ---------------- CONFIG ----------------
INPUT_DIR  = "datasets/programs_kept"          # source programs (full files)
OUT_DIR    = "datasets/sliced_single"          # one function per file goes here
MANIFEST   = "datasets/sliced_single_manifest.jsonl"
INCLUDE_ALL_IMPORTS = True                     # safe default; set False to try minimal imports
STUB_HELPERS = True                            # create stubs for local helpers referenced by the function
MAX_CONST_SIZE = 4000                          # skip huge literals/constants
# ----------------------------------------

BUILTINS = set(dir(builtins))

def is_simple_literal(node: ast.AST) -> bool:
    """Allow constants and shallow collections of constants (for safe constant lifting)."""
    if isinstance(node, (ast.Constant,)):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(is_simple_literal(elt) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return all(is_simple_literal(k) and is_simple_literal(v) for k, v in zip(node.keys, node.values))
    return False

def collect_imports(module: ast.Module) -> List[ast.stmt]:
    return [n for n in module.body if isinstance(n, (ast.Import, ast.ImportFrom))]

def collect_toplevel_funcs(module: ast.Module) -> Dict[str, ast.FunctionDef]:
    return {n.name: n for n in module.body if isinstance(n, ast.FunctionDef)}

def collect_toplevel_consts(module: ast.Module) -> Dict[str, ast.Assign]:
    consts = {}
    for n in module.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            val = n.value
            if is_simple_literal(val):
                consts[name] = n
    return consts

def locals_of_func(fn: ast.FunctionDef) -> Set[str]:
    names = set(arg.arg for arg in fn.args.args + fn.args.kwonlyargs)
    if fn.args.vararg: names.add(fn.args.vararg.arg)
    if fn.args.kwarg: names.add(fn.args.kwarg.arg)

    class LVisitor(ast.NodeVisitor):
        def __init__(self): self.locals = set()
        def visit_Name(self, node: ast.Name):
            if isinstance(node.ctx, ast.Store): self.locals.add(node.id)
        def visit_For(self, node: ast.For):
            # targets in for-comprehensions are locals
            def add_targets(t):
                if isinstance(t, ast.Name): self.locals.add(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    for x in t.elts: add_targets(x)
            add_targets(node.target)
            self.generic_visit(node)
        def visit_With(self, node: ast.With):
            for item in node.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    self.locals.add(item.optional_vars.id)
            self.generic_visit(node)
        def visit_ExceptHandler(self, node: ast.ExceptHandler):
            if node.name and isinstance(node.name, str):
                self.locals.add(node.name)
            self.generic_visit(node)

    lv = LVisitor(); lv.visit(fn)
    return names | lv.locals

def free_names_in_func(fn: ast.FunctionDef) -> Set[str]:
    localish = locals_of_func(fn)
    used = set()

    class UVisitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name):
            if isinstance(node.ctx, ast.Load):
                used.add(node.id)

    UVisitor().visit(fn)
    # free = used - locals - builtins
    return {n for n in used if n not in localish and n not in BUILTINS}

def direct_callees(fn: ast.FunctionDef) -> Set[str]:
    calls = set()
    class CVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                # module.func or obj.method -> take attr name; if module attr, import will handle it
                name = node.func.attr
            if name:
                calls.add(name)
            self.generic_visit(node)
    CVisitor().visit(fn)
    return calls

def stub_for_func(name: str, orig: ast.FunctionDef | None = None) -> ast.FunctionDef:
    """
    Build a minimal stub for a local helper so the single-function module parses.
    If we know the original signature, reuse it; otherwise use (*args, **kwargs).
    """
    if orig is not None:
        args = orig.args  # reuse signature
    else:
        args = ast.arguments(
            posonlyargs=[],
            args=[],                        # no positional names
            vararg=ast.arg(arg="args"),     # *args
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=ast.arg(arg="kwargs"),    # **kwargs
            defaults=[],
        )

    # def helper(...): raise NotImplementedError
    body = [
        ast.Raise(
            exc=ast.Call(func=ast.Name(id="NotImplementedError", ctx=ast.Load()), args=[], keywords=[]),
            cause=None,
        )
    ]

    return ast.FunctionDef(
        name=name,
        args=args,
        body=body,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )

def minimal_imports_for_fn(module: ast.Module, fn: ast.FunctionDef) -> List[ast.stmt]:
    # Conservative approach: include all imports at module level
    return collect_imports(module)

def write_slice(out_path: pathlib.Path, stmts: list[ast.stmt]) -> None:
    mod = ast.Module(body=stmts, type_ignores=[])
    # <<< important: synthesize missing line/column info for all nodes >>>
    mod = ast.fix_missing_locations(mod)
    code = ast.unparse(mod)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")

def process_file(py_path: pathlib.Path) -> List[Tuple[str, pathlib.Path, Dict]]:
    src = py_path.read_text(encoding="utf-8", errors="ignore")
    try:
        module = ast.parse(src)
    except Exception:
        return []
    imports = collect_imports(module)
    funcs = collect_toplevel_funcs(module)
    consts = collect_toplevel_consts(module)

    results = []
    for fname, fnode in funcs.items():
        # names the function reads from outer scope
        free = free_names_in_func(fnode)

        # constants actually used
        needed_consts = []
        for name in free:
            if name in consts:
                node = consts[name]
                # avoid gigantic literals
                if len(ast.unparse(node)) <= MAX_CONST_SIZE:
                    needed_consts.append(node)

        # local helper calls
        callees = direct_callees(fnode)
        local_helpers = [name for name in callees if name in funcs and name != fname]

        # choose imports (safe: all module imports)
        used_imports = imports if INCLUDE_ALL_IMPORTS else minimal_imports_for_fn(module, fnode)

        # create stubs for local helpers if requested
        stub_nodes = []
        if STUB_HELPERS and local_helpers:
            for h in local_helpers:
                stub_nodes.append(stub_for_func(h, funcs[h]))

        # assemble module: imports -> constants -> stubs -> target fn
        body: List[ast.stmt] = []
        body.extend(used_imports)
        body.extend(needed_consts)
        body.extend(stub_nodes)
        body.append(fnode)

        # file name
        rel = py_path.relative_to(INPUT_DIR)
        stem = rel.with_suffix("").as_posix().replace("/", "__")
        out_file = pathlib.Path(OUT_DIR) / f"{stem}__{fname}.py"

        write_slice(out_file, body)

        meta = {
            "source_path": str(py_path),
            "out_path": str(out_file),
            "function": fname,
            "needed_consts": [getattr(t.targets[0], "id", "") for t in needed_consts],
            "stubbed_helpers": local_helpers if STUB_HELPERS else [],
            "imports_included": len(used_imports),
            "lines_out": sum(1 for _ in open(out_file, "r", encoding="utf-8")),
        }
        results.append((fname, out_file, meta))
    return results

def main():
    out_dir = pathlib.Path(OUT_DIR); out_dir.mkdir(parents=True, exist_ok=True)
    man_fp = pathlib.Path(MANIFEST)
    written = 0
    with man_fp.open("w", encoding="utf-8") as mf:
        for p in pathlib.Path(INPUT_DIR).rglob("*.py"):
            slices = process_file(p)
            for _, _, meta in slices:
                mf.write(json.dumps(meta, ensure_ascii=False) + "\n")
                written += 1
    print(f"Done. Wrote {written} single-function files to {OUT_DIR}")
    print(f"Manifest: {MANIFEST}")

if __name__ == "__main__":
    main()
