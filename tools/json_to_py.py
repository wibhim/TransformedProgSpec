# save as json_to_py.py
import json
import os
import argparse
import ast
import re

def load_json_or_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)  # full JSON
        except json.JSONDecodeError:
            f.seek(0)
            data = [json.loads(line) for line in f if line.strip()]
    if isinstance(data, dict):
        data = [data]
    return data

def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "func"

def split_top_level_functions(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    lines = code.splitlines()
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    results = []
    for n in funcs:
        start = n.lineno
        end = getattr(n, "end_lineno", None) or len(lines)
        segment = "\n".join(lines[start-1:end]) + "\n"
        results.append((n.name, segment))
    return results

def write_task_as_is(task, out_dir):
    task_id = task.get("task_id", "unknown")
    code = (task.get("code") or "").strip()
    if not code:
        return
    fname = f"program_{str(task_id).zfill(3)}.py"
    with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
        f.write(code + "\n")
    print(f"Saved {fname}")

def write_task_split(task, out_dir):
    task_id = task.get("task_id", "unknown")
    code = (task.get("code") or "").strip()
    if not code:
        return
    funcs = split_top_level_functions(code)
    if not funcs:  # fallback
        write_task_as_is(task, out_dir)
        return
    for i, (func_name, func_src) in enumerate(funcs, start=1):
        fname = f"program_{str(task_id).zfill(3)}_{sanitize_name(func_name)}.py"
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(func_src)
        print(f"Saved {fname}")

def main():
    parser = argparse.ArgumentParser(description="Convert JSON/JSONL dataset to .py files")
    parser.add_argument("--in", dest="json_file", required=True, help="Input JSON/JSONL file")
    parser.add_argument("--out", dest="output_dir", default="output_py", help="Output directory")
    parser.add_argument("--mode", choices=["task", "split"], default="task", help="task = one file per JSON task, split = one file per top-level def")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    data = load_json_or_jsonl(args.json_file)

    for task in data:
        if args.mode == "split":
            write_task_split(task, args.output_dir)
        else:
            write_task_as_is(task, args.output_dir)

if __name__ == "__main__":
    main()
