import ast
import json
import textwrap

# -----------------------------------------------------------------------------
# transform_final.py  —  second-pass AST transformation
#
# Purpose
# -------
# • Load the “cleaned” snippets produced earlier (cleaned_code_dataset_ast.json).
# • Apply a lighter AST transform that *preserves variable names* while:
#     – stripping type hints from functions
#     – deleting try/except blocks (keeps the try-body only)
#     – removing else / elif branches from if-statements
#     – deleting docstrings and standalone string literals that act as comments
# • Save the fully transformed code to  output/transformed_code_dataset.json.
# • Log any snippets that failed to parse/transform to errors/transformation_errors.txt.
#
# Key classes / functions
# -----------------------
# CodeTransformer  : ast.NodeTransformer subclass that performs the edits above.
# transform_code() : helper that normalises tabs/indent, runs CodeTransformer, and
#                    unparses the AST back to source (using ast.unparse or astor).
#
# Pipeline
# --------
# 1. Read INPUT_JSON  (output/cleaned_code_dataset_ast.json).
# 2. For each entry:
#       • call transform_code(entry["cleaned_code"])
#       • on success  -> add "transformed_code" field  -> append to transformed_data
#       • on failure  -> append {file_path, error}     -> errors list
# 3. Write transformed_data  to OUTPUT_JSON.
# 4. Write errors            to ERROR_FILE.
# 5. Print summary and a sample of transformed code.
# -----------------------------------------------------------------------------

# --- CONFIG ---
INPUT_JSON = "output/cleaned_code_dataset_ast.json"
OUTPUT_JSON = "output/transformed_code_dataset.json"
ERROR_FILE = "errors/transformation_errors.txt"

# --- AST Node Transformer that preserves variable names ---
class CodeTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()

    # Remove type hints
    def visit_FunctionDef(self, node):
        node.returns = None
        node.args.args = [ast.arg(arg=arg.arg, annotation=None) for arg in node.args.args]
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        # Keep the variable name, remove only annotations
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
try:
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"Successfully loaded {len(data)} entries from {INPUT_JSON}")
except Exception as e:
    print(f"Error loading input file: {e}")
    data = []

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
try:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(transformed_data, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved transformed data to {OUTPUT_JSON}")
except Exception as e:
    print(f"Error saving output file: {e}")

try:
    with open(ERROR_FILE, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e['file_path']} - {e['error']}\n")
    print(f"Logged {len(errors)} errors to: {ERROR_FILE}")
except Exception as e:
    print(f"Error saving error file: {e}")

print(f"\n✅ Transformed {len(transformed_data)} code snippets.")
if errors:
    print(f"⚠️ Encountered {len(errors)} errors.")

# Print a sample of the transformed code to verify variable names are preserved
if transformed_data:
    print("\nSample of transformed code with preserved variable names:")
    sample = transformed_data[0]["transformed_code"]
    print(sample[:500] + "..." if len(sample) > 500 else sample)
