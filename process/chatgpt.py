import openai
import json
import time
import os
from config import CONFIG

# === CONFIG ===
CHATGPT_CONFIG = CONFIG["chatgpt"]
INPUT_JSON = CHATGPT_CONFIG["input_json"]
OUTPUT_JSON = CHATGPT_CONFIG["output_json"]
ERROR_LOG = CHATGPT_CONFIG["error_log"]
DELAY = CHATGPT_CONFIG["delay"]
TEMPERATURE = CHATGPT_CONFIG["temperature"]
TOKEN_FILE = CHATGPT_CONFIG["token_file"]

# Load API key from token file for security
try:
    with open(TOKEN_FILE, "r") as f:
        API_KEY = f.read().strip()
except FileNotFoundError:
    print(f"⚠️ Token file not found at: {TOKEN_FILE}")
    API_KEY = input("Enter your OpenAI API key: ")

MODEL = "gpt-4.1"  # Or "gpt-3.5-turbo"
MAX_REQUESTS = 100  # Limit for safety/testing

# === OpenAI API setup ===
openai.api_key = API_KEY

# === Prompt builder ===
def build_prompt(code):
    return f"""Here is the Python code snippet:
```python
{code}

You should only generate the specification and Dafny program for the above Python code withoutany additional context or explanation.
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
        # New OpenAI API format (v1.0.0+)
        client = openai.OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert in Dafny Language. Your task is to generate a formal specification and Dafny prograam for the following Python program. The specification should include postconditions and preconditions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        # And access the content differently
        spec = response.choices[0].message.content

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
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ Saved {len(results)} specifications to '{OUTPUT_JSON}'")
if errors:
    print(f"⚠️ Encountered {len(errors)} errors. See '{ERROR_LOG}'")