
#!/usr/bin/env python3
import os, json, re, argparse
from collections import Counter
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import pandas as pd

# ---------------- Normalization ----------------
NORMALIZATION_PATTERNS = [
    (r'".*?"', '""'),
    (r"'[^']*'", "''"),
    (r'\bline\s*\d+\b', 'line N'),
    (r'\bcol(?:umn)?\s*\d+\b', 'col N'),
    (r'\b\d+:\d+\b', 'N:N'),
    (r'\b\d+\b', 'N'),
    (r'\b[A-Za-z]:[/\\][^\s:]+', '<PATH>'),
    (r'[/\\][^\s:]+', '<PATH>'),
    (r'\s+', ' '),
]
def normalize(msg: str) -> str:
    m = (msg or '').strip().casefold()
    for pat, repl in NORMALIZATION_PATTERNS:
        m = re.sub(pat, repl, m)
    return m

# ---------------- Rules ----------------
RULES: List[Tuple[str, List[str]]] = [
    ('Verification', [
        r'\b(post|pre)[ -]?condition.*might not hold',
        r'\b(assert|ensures|requires).*might not hold',
        r'\binvariant.*might not (hold|be maintained)',
        r'\bcould not be (proved|proven)',
        r'\b(decreases|termination|well[- ]?founded)',
        r'\breads\b|\bmodifies\b|\bframe\b',
    ]),
    ('Parser', [
        r'\b(expected|unexpected)\b',
        r'\binvalid (token|statement|expression|unaryexpression|whilestmt|forspec|ifstmt|block)\b',
        r'paren|bracket|brace|semicolon|comma|verticalbar',
        r'\bsyntax error\b|\bparse error\b',
    ]),
    ('Name/Type Resolution', [
        r'\b(undeclared|unknown|not (found|declared))\b',
        r'\b(member .* does not exist|no such (member|field|method))\b',
        r'\bwrong number of (arguments|type arguments)|arity\b',
        r'\btype (mismatch|incompatible|convert|cast|assignable)\b',
        r'\bexpect(s|ed) type\b|\bcommon supertype\b|\bco/contra-?variant\b',
        r'\bbitvector\b|\bordinal\b|\bnat\b',
        r'\barray selection requires\b|\bmap .* expects\b|\belement selection requires\b',
        r'\barguments must have comparable types\b',
    ]),
    ('Ghost/Spec Context', [
        r'\bold\b|\bfresh\b|\bunchanged\b.*only in specification',
        r'\bghost\b.*not allowed\b|\bprint statement .* ghost\b',
        r'\bexpression is not allowed to invoke a method\b|\bmethod call .* not allowed in expression\b',
        r'\bmatch expression .* ghost constructor\b',
    ]),
    ('Determinism', [
        r'\benforce-determinism\b|\bnondeterministic (assignment|if|loop)\b|assign-such-that',
    ]),
    ('Compilation', [
        r'\bfeature not supported\b|\bcannot be compiled\b|\babstract type .* cannot be compiled\b',
        r'\bunable to start target\b|\bprocess .* exit code\b|\bunsupportedfeatures\b',
    ]),
    ('Command-line', [
        r'\bunknown (switch|option)\b|\bnot a recognized option\b',
        r'\bno dafny source files\b|\bfilename extension .* is not supported\b',
        r'\bonly one \.dfy file\b|\bmodelview file must be specified\b|\bcannot be formatted in place\b',
    ]),
]
CATEGORY_ORDER = ['Verification','Parser','Name/Type Resolution','Ghost/Spec Context','Determinism','Compilation','Command-line','Other']
SEVERITY = {
    'Verification': 'Critical',
    'Parser': 'High',
    'Name/Type Resolution': 'High',
    'Compilation': 'High',
    'Ghost/Spec Context': 'Medium',
    'Determinism': 'Medium',
    'Command-line': 'Low',
    'Other': 'Low',
}

# ------------- Collect -------------
POSSIBLE_KEYS = [
    'common_parse_errors',
    'common_verify_errors',
    'common_type_errors',
    'common_compilation_errors',
    'common_errors',
    'errors',
]

def collect_errors(d: dict) -> Dict[str,int]:
    merged = Counter()
    ea = d.get('error_analysis', {}) if isinstance(d, dict) else {}
    for k in POSSIBLE_KEYS:
        v = ea.get(k)
        if isinstance(v, dict):
            merged.update(v)
    flat = ea.get('messages') or d.get('messages')
    if isinstance(flat, list):
        for m in flat:
            merged[m] += 1
    return dict(merged)

# ------------- Categorize -------------
def cat_for(msg: str) -> str:
    m = normalize(msg)
    for cat, pats in RULES:
        for p in pats:
            if re.search(p, m, flags=re.IGNORECASE):
                return cat
    return 'Other'

def categorize(errors: Dict[str,int]) -> Dict[str, List[Tuple[str,int]]]:
    out = {k: [] for k in CATEGORY_ORDER}
    for raw, cnt in errors.items():
        out[cat_for(raw)].append((raw, cnt))
    return out

# ------------- Plots -------------
def pie_pastel(df: pd.DataFrame, out_png: str, title: str):
    df2 = df[df['count']>0]
    # Pastel palette (explicitly asked by user)
    pastel = ['#A8DADC','#BDE0FE','#CDEAC0','#FFD6A5','#E2C2FF','#FAD2E1','#FFF1B6','#D1E8E2']
    colors = (pastel * ((len(df2)//len(pastel))+1))[:len(df2)]
    fig, ax = plt.subplots(figsize=(7,7))
    ax.pie(df2['count'].tolist(), labels=df2['category'].tolist(), autopct='%1.1f%%', startangle=90, colors=colors)
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close(fig)

def bar_top_messages(top_df: pd.DataFrame, out_png: str, title: str):
    # Take overall top messages regardless of category
    if top_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No messages', ha='center')
        plt.savefig(out_png, dpi=160); plt.close(fig); return
    df = top_df.sort_values('count', ascending=True)
    fig, ax = plt.subplots(figsize=(9,6))
    ax.barh(df['message'].tolist(), df['count'].tolist())
    ax.set_xlabel('Frequency of Occurrence')
    ax.set_title(title)
    # add value labels
    for i, v in enumerate(df['count'].tolist()):
        ax.text(v + max(df['count']) * 0.01, i, str(v), va='center')
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close(fig)

def bar_severity(df: pd.DataFrame, out_png: str, title: str):
    # Map category -> severity, then sum by severity
    order = ['Critical', 'High', 'Medium', 'Low']
    sev_counts = df.groupby('severity')['count'].sum().reindex(order).fillna(0)

    # Distinct severity colors (Critical=red, High=orange, Medium=yellow, Low=green)
    colors = {
        'Critical': '#E74C3C',  # red
        'High': '#F39C12',      # orange
        'Medium': '#F1C40F',    # yellow
        'Low': '#27AE60'        # green
    }

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(
        sev_counts.index.tolist(),
        sev_counts.values.tolist(),
        color=[colors[s] for s in sev_counts.index.tolist()]
    )

    ax.set_ylabel('Number of Error Instances')
    ax.set_title(title)

    # Add count labels on top
    for bar, label in zip(bars, sev_counts.values.tolist()):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(sev_counts.values.tolist()) * 0.02,
            f"{int(label)}",
            ha='center', va='bottom', fontsize=10, fontweight='bold'
        )

    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close(fig)


# ------------- CLI -------------
def load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser(description='Analyze Dafny verification results (single merged output).')
    ap.add_argument('--input', required=True, help='JSON file or directory of JSON files')
    ap.add_argument('--output', required=True, help='Output directory')
    ap.add_argument('--top', type=int, default=12, help='Top-N messages to display')
    args = ap.parse_args()
    os.makedirs(args.output, exist_ok=True)

    # Gather JSONs
    files = []
    if os.path.isdir(args.input):
        for name in os.listdir(args.input):
            if name.lower().endswith('.json'):
                files.append(os.path.join(args.input, name))
    else:
        files.append(args.input)

    # Merge all errors
    merged = Counter()
    for fp in files:
        try:
            d = load_json(fp)
        except Exception as e:
            print(f"[WARN] cannot read {fp}: {e}")
            continue
        errs = collect_errors(d)
        merged.update(errs)

    categories = categorize(dict(merged))

    # Build DataFrames
    rows = []
    for cat in CATEGORY_ORDER:
        cnt = sum(c for _, c in categories.get(cat, []))
        rows.append({'category': cat, 'count': cnt, 'severity': SEVERITY.get(cat,'Low')})
    df = pd.DataFrame(rows)

    # Top messages across ALL categories
    top_rows = []
    for cat in categories:
        for msg, cnt in categories[cat]:
            top_rows.append({'category': cat, 'message': msg, 'count': cnt})
    top_df = pd.DataFrame(top_rows).sort_values('count', ascending=False).head(args.top)

    # Write CSVs
    df.to_csv(os.path.join(args.output, 'categories.csv'), index=False)
    top_df.to_csv(os.path.join(args.output, 'top_messages.csv'), index=False)

    # Summary text
    total = int(df['count'].sum())
    with open(os.path.join(args.output, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write('Severity mapping:\n')
        for k,v in SEVERITY.items():
            f.write(f'  - {k}: {v}\n')
        f.write('\nCategory counts:\n')
        for _, r in df.sort_values('count', ascending=False).iterrows():
            pct = (r['count'] / total * 100.0) if total else 0.0
            f.write(f"  - {r['category']:<22} {int(r['count']):>6} ({pct:5.1f}%)\n")

    # Plots
    pie_pastel(df, os.path.join(args.output, 'pie.png'), 'Error Categories')
    bar_top_messages(top_df, os.path.join(args.output, 'bar_top_errors.png'), 'Top Error Messages (Merged)')
    bar_severity(df, os.path.join(args.output, 'bar_severity.png'), 'Severity Levels')

if __name__ == '__main__':
    main()
