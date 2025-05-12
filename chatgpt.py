import openai
import json
import time

# === CONFIG ===
INPUT_JSON = "transformed_code_dataset.json"
OUTPUT_JSON = "chatgpt_specifications.json"
API_KEY = "your-api-key-here"  # 🔐 Replace this
MODEL = "gpt-4"  # Or "gpt-3.5-turbo"
DELAY = 2  # Seconds between requests
MAX_REQUESTS = 100  # Limit for safety/testing

# === OpenAI API setup ===
openai.api_key = API_KEY

# === Prompt builder ===
def build_prompt(code):
    return f"""You are a software engineer. Your task is to write a precise and concise specification for the following Python function.

```python
{code}
Please describe:

The purpose of the function

Its input parameters and types

Its output

Preconditions and postconditions (if applicable)

Be formal and clear, as if writing documentation or a verification contract.
"""

# === Load the input JSON ===
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    dataset = json.load(f)

results = []
errors = []

# === Loop through each code snippet ===
for i, item in enumerate(dataset[:MAX_REQUESTS]):
    file_path = item.get("file_path", f"snippet_{i}.py")
    code = item.get("transformed_code", "").strip()
    prompt = build_prompt(code)
    print(f"[{i+1}/{min(MAX_REQUESTS, len(dataset))}] Generating spec for: {file_path}")

try:
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    spec = response["choices"][0]["message"]["content"]

    results.append({
        "file_path": file_path,
        "transformed_code": code,
        "program_specification": spec
    })

    time.sleep(DELAY)

except Exception as e:
    print(f"❌ Error on {file_path}: {e}")
    errors.append({
        "file_path": file_path,
        "error": str(e)
    })
    time.sleep(5)

# === Save results ===
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# === Optionally save errors ===
if errors:
    with open("chatgpt_spec_errors.txt", "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ Saved {len(results)} specifications to '{OUTPUT_JSON}'")
if errors:
    print(f"⚠️ Encountered {len(errors)} errors. See 'chatgpt_spec_errors.txt'")