import json
import numpy as np

# --- CONFIG ---
INPUT_FILE = "dafny_verification_results.json"
K_VALUES = [1, 5, 10]  # you can add more like 20, 50, etc.

# --- pass@k Function ---
def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

# --- Load verification results ---
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

total = len(data)
correct = sum(1 for item in data if item["verified"] is True)

print(f"Total generated samples: {total}")
print(f"Correct (verified) samples: {correct}\n")

# --- Calculate pass@k for all desired k values ---
for k in K_VALUES:
    if k <= total:
        p = pass_at_k(total, correct, k)
        print(f"pass@{k}: {p:.4f}")
    else:
        print(f"pass@{k}: Not enough samples (need at least {k})")
