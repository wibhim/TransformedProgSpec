import ast
import json
import textwrap
import re
from config import CONFIG

# --- Get Configuration ---
CLEANUP_CONFIG = CONFIG["cleanup"]
INPUT_JSON = CLEANUP_CONFIG["input_json"]
OUTPUT_JSON = CLEANUP_CONFIG["output_json"]
ERROR_LOG = CLEANUP_CONFIG["error_log"]

# --- AST Transformer to Remove Docstrings ---
class DocstringStripper(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            node.body.pop(0)
        return node

# --- Cleanup Function ---
def clean_code(code):
    try:
        # Step 1: Normalize tabs → spaces
        code = code.replace('\t', '    ').strip()

        # Step 2: Fix Python 2 print statements
        lines = []
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("print ") and not stripped.startswith("print("):
                indent = len(line) - len(line.lstrip())
                lines.append(" " * indent + "print(" + stripped[6:] + ")")
            else:
                lines.append(line)
        code = "\n".join(lines)

        # Step 3: Fix Python 2 except syntax
        code = re.sub(r'except\s+(\w+),\s*(\w+):', r'except \1 as \2:', code)

        # Step 4: Dedent before parsing
        code = textwrap.dedent(code)

        # Step 5: Remove docstrings via AST
        tree = ast.parse(code)
        tree = DocstringStripper().visit(tree)
        ast.fix_missing_locations(tree)

        # Step 6: Unparse code
        try:
            cleaned_code = ast.unparse(tree)
        except AttributeError:
            import astor
            cleaned_code = astor.to_source(tree)

        # Step 7: If top lines are wrongly indented, dedent again
        lines = cleaned_code.splitlines()
        if lines and all((line.startswith("    ") or line.strip() == "") for line in lines[:5]):
            cleaned_code = textwrap.dedent(cleaned_code)

        # Step 8: Final validation
        ast.parse(cleaned_code)

        return cleaned_code, None

    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    except Exception as e:
        return None, f"Unhandled error: {e}"

# --- Load and Process Dataset ---
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_data = []
errors = []

for entry in data:
    code = entry.get("code", "")
    file_path = entry.get("file_path", "unknown")
    cleaned, error = clean_code(code)

    if cleaned:
        entry["cleaned_code"] = cleaned
        cleaned_data.append(entry)
    else:
        errors.append({
            "file_path": file_path,
            "error": error
        })

# --- Save Cleaned Output ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

# --- Save Error Log ---
with open(ERROR_LOG, "w", encoding="utf-8") as f:
    for e in errors:
        f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ AST-based cleaned {len(cleaned_data)} snippets.")
print(f"⚠️ Logged {len(errors)} errors to: {ERROR_LOG}")
