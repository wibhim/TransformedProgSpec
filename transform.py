import ast
import json
import re
import textwrap
import keyword

# --- CONFIG ---
INPUT_JSON = "cleaned_code_dataset_ast.json"
OUTPUT_JSON = "transformed_code_dataset.json"

# --- AST Node Transformer for Multiple Transformations ---
class CodeTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.var_counter = 0
        self.var_map = {}
        self.exclude = set(dir(__builtins__))

    def _new_name(self):
        self.var_counter += 1
        return f"var_{self.var_counter}"

    def _abstract_name(self, name):
        if name in self.exclude or name in keyword.kwlist:
            return name
        if name not in self.var_map:
            self.var_map[name] = self._new_name()
        return self.var_map[name]

    # Remove type hints
    def visit_FunctionDef(self, node):
        node.returns = None
        node.args.args = [ast.arg(arg=arg.arg, annotation=None) for arg in node.args.args]
        self.generic_visit(node)
        return node

    # Abstract variable and identifier names
    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
            node.id = self._abstract_name(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self._abstract_name(node.arg)
        node.annotation = None
        return node

    # Remove try-except blocks (error handling)
    def visit_Try(self, node):
        self.generic_visit(node)
        return node.body  # just keep the try body

    # Simplify if-elif-else to just `if` block (for illustration)
    def visit_If(self, node):
        self.generic_visit(node)
        node.orelse = []  # strip else/elif
        return node

    # Remove docstrings at module, class, and function level
    def remove_docstrings(self, node):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body.pop(0)
        return node

    def visit_Module(self, node):
        self.remove_docstrings(node)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        self.remove_docstrings(node)
        self.generic_visit(node)
        return node

    def visit_Expr(self, node):
        # remove standalone string expressions (likely comments)
        if isinstance(node.value, ast.Str):
            return None
        return node

# --- Cleanup and Transform Function ---
def transform_code(code):
    try:
        code = code.replace('\t', '    ')
        code = textwrap.dedent(code)

        tree = ast.parse(code)
        transformer = CodeTransformer()
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)

        try:
            transformed_code = ast.unparse(tree)
        except AttributeError:
            import astor
            transformed_code = astor.to_source(tree)

        # Final dedent to prevent global indent issues
        transformed_code = textwrap.dedent(transformed_code)
        return transformed_code, None

    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    except Exception as e:
        return None, f"Unhandled error: {e}"

# --- Load Dataset ---
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

transformed_data = []
errors = []

# --- Process Each Code Entry ---
for entry in data:
    code = entry.get("cleaned_code", "")
    file_path = entry.get("file_path", "unknown")
    transformed, error = transform_code(code)

    if transformed:
        entry["transformed_code"] = transformed
        transformed_data.append(entry)
    else:
        errors.append({
            "file_path": file_path,
            "error": error
        })

# --- Save Transformed Output ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(transformed_data, f, indent=2, ensure_ascii=False)

with open("transformation_errors.txt", "w", encoding="utf-8") as f:
    for e in errors:
        f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ Transformed {len(transformed_data)} code snippets.")
print(f"⚠️ Logged {len(errors)} errors to: transformation_errors.txt")
