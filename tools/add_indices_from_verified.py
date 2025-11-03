#!/usr/bin/env python
import argparse, glob, json, os, re
from pathlib import Path

def load_verified_order(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = obj.get("results", obj if isinstance(obj, list) else [])
    order = []
    for r in rows:
        si = r.get("specification_index")
        try:
            order.append(int(si))
        except Exception:
            pass
    return order

def best_verified_for(regen_path, verified_candidates):
    rn = Path(regen_path).name.lower()
    rtoks = set(re.split(r"[_\-.]+", rn))
    best, score = None, -1
    for v in verified_candidates:
        vtoks = set(re.split(r"[_\-.]+", Path(v).name.lower()))
        s = len(rtoks & vtoks)
        if s > score:
            best, score = v, s
    return best

def extract_python_block(text):
    if not isinstance(text, str): return ""
    m = re.search(r"```(?:python|py)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else text.strip()

def normalize_one(regen_path, verified_path, code_field, extract_py, filename_tpl):
    obj = json.loads(Path(regen_path).read_text(encoding="utf-8"))
    rows = obj.get("specifications") or obj.get("results") or (obj if isinstance(obj, list) else [])
    order = load_verified_order(verified_path)

    out, dropped = [], 0
    fname_stem = Path(regen_path).stem  # e.g., "remove_parentheses" from "remove_parentheses.json"

    for pos, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue
        if pos > len(order):
            dropped += 1
            continue
        spec_idx = order[pos - 1]
        raw = r.get(code_field) or r.get("regenerated_code") or r.get("code") or ""
        code = extract_python_block(raw) if extract_py else (raw or "").strip()

        # prefer existing metadata; otherwise fall back to file name
        trans = r.get("transformation") or r.get("transformation_type")
        if not trans or str(trans).strip().lower() in {"", "unknown", "none", "null"}:
            trans = fname_stem

        out.append({
            "source_file": filename_tpl.format(index=spec_idx),
            "specification_index": spec_idx,
            "transformation": trans,
            "regenerated_code": code
        })
    return out, dropped, len(rows), len(order)

def main():
    ap = argparse.ArgumentParser(description="Map regen → verified only; synthesize filename via template.")
    ap.add_argument("--regen", required=True, help='Glob for regenerated JSONs (e.g., "output/regenerate/*.json")')
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--verified-file", help="Single verified JSON to align with")
    grp.add_argument("--verified-glob", help='Glob for verified JSONs; auto-pick best by filename tokens')
    ap.add_argument("--outdir", required=True, help="Directory for normalized JSONs")
    ap.add_argument("--code-field", default="program_specification", help="Field containing Python")
    ap.add_argument("--extract-python", action="store_true", help="Extract fenced ```python blocks")
    ap.add_argument("--filename-template", default="program_{index:03d}.py",
                    help='Filename format; available key: {index}. Default: "program_{index:03d}.py"')
    args = ap.parse_args()

    verified_pool = []
    if args.verified_file:
        verified_pool = [args.verified_file]
    else:
        verified_pool = glob.glob(args.verified_glob)
        if not verified_pool:
            raise SystemExit("No verified files match the given glob.")

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    total_files = total_out = total_in = total_drop = 0
    for rp in glob.glob(args.regen):
        vp = args.verified_file or best_verified_for(rp, verified_pool)
        norm, dropped, nrows, vlen = normalize_one(
            rp, vp, args.code_field, args.extract_python, args.filename_template
        )
        (outdir / Path(rp).name).write_text(
            json.dumps({"results": norm}, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        total_files += 1; total_out += len(norm); total_in += nrows; total_drop += dropped
        print(f"[{Path(rp).name}] ↔ [{Path(vp).name}]  in:{nrows}  verified_idx:{vlen}  out:{len(norm)}  dropped:{dropped}")
    print(f"✅ Normalized {total_files} file(s). In:{total_in}  Out:{total_out}  Dropped:{total_drop} → {args.outdir}")

if __name__ == "__main__":
    main()
