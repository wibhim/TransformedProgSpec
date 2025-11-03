import json, hashlib, pathlib, random, os

# ---------- CONFIG ----------
INPUT_DIR   = "datasets/sliced_single"                 # folder with one-function .py files
MANIFEST_JL = "datasets/sliced_single_manifest.jsonl"  # optional (set None if you don't have it)
OUT_JSON    = "datasets/sliced_single_eval.json"       # output JSON (array)
LIMIT       = 500                                      # cap (use min(LIMIT, available))
SEED        = 2025                                     # for deterministic sampling
# ----------------------------

def short_hash(text: str) -> str:
    norm = "\n".join(ln.rstrip() for ln in (text or "").splitlines())
    return hashlib.sha1(norm.encode("utf-8", "ignore")).hexdigest()[:12]

def load_manifest(manifest_path):
    idx = {}
    p = pathlib.Path(manifest_path)
    if not p.exists(): 
        return idx
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # key by output path basename (matches files in INPUT_DIR)
            key = os.path.basename(obj.get("out_path", "")) if obj.get("out_path") else None
            if key:
                idx[key] = obj
    return idx

def main():
    random.seed(SEED)

    files = sorted(pathlib.Path(INPUT_DIR).rglob("*.py"))
    if not files:
        raise SystemExit(f"No .py files found under {INPUT_DIR}")

    manifest = load_manifest(MANIFEST_JL) if MANIFEST_JL else {}

    # Build records
    records = []
    for p in files:
        try:
            code = p.read_text(encoding="utf-8")
        except Exception:
            try:
                code = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

        loc = sum(1 for ln in code.splitlines() if ln.strip())
        fname = p.name
        meta = manifest.get(fname, {})

        rec = {
            "id": f"{fname}::{short_hash(code)}",
            "file_name": fname,
            "file_path": str(p),
            "code": code,
            "loc": loc,
            # optional metadata from manifest, if available
            "function": meta.get("function"),
            "source_path": meta.get("source_path"),
            "imports_included": meta.get("imports_included"),
            "stubbed_helpers": meta.get("stubbed_helpers"),
            "needed_consts": meta.get("needed_consts"),
        }
        records.append(rec)

    # Deterministic sampling to LIMIT
    random.shuffle(records)
    selected = records[: min(LIMIT, len(records))]

    # Write JSON array
    outp = pathlib.Path(OUT_JSON)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Found {len(records)} sliced functions; wrote {len(selected)} to {OUT_JSON}")

if __name__ == "__main__":
    main()
