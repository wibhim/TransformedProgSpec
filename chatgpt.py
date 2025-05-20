import openai
# Imports the official openai Python client library so you
# can make API calls to ChatGPT / GPT-4.

import json
import time
# Imports the time module, which provides time-related utilities
# (later used for sleep delays between requests).


# === CONFIG ===
INPUT_JSON = "output/transformed_code_dataset.json"
OUTPUT_JSON = "output/chatgpt_specifications.json"
# Load API key from token.txt file for security

# Tries to open token.txt and read its lines:
# • If the file exists and has at least three lines, it assumes the API key is on
#   line 3 (lines[2] because indexing starts at 0) and strips the newline characters.
# • If the file exists but the key isn’t on line 3, it prints a warning and prompts
#   the user to paste an API key.
# • If token.txt is missing, the FileNotFoundError branch catches that and again
#   prompts the user for an API key.
try:
    with open("token.txt", "r") as f:
        lines = f.readlines()
        if len(lines) >= 3:  # Assuming API key is on the third line
            API_KEY = lines[2].strip()
        else:
            print("⚠️ API key not found in token.txt. Please provide an API key.")
            API_KEY = input("Enter your OpenAI API key: ")
except FileNotFoundError:
    print("⚠️ token.txt file not found.")
    API_KEY = input("Enter your OpenAI API key: ")
MODEL = "gpt-4.1"  # Or "gpt-3.5-turbo"
DELAY = 2  # Seconds between requests
MAX_REQUESTS = 100  # Limit for safety/testing

# === OpenAI API setup ===
openai.api_key = API_KEY

# openai confgured

# === Prompt builder ===
# Defines a helper function build_prompt that wraps a given Python snippet (code)
# in a Markdown code-block and appends clear instructions for ChatGPT:
# “generate a Dafny spec only, no extra commentary.”

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

# Iterates over each entry (up to MAX_REQUESTS).
# -- Pulls file_path metadata (fallback name if missing).
# -- Extracts the cleaned Python source (transformed_code).
# -- Builds the ChatGPT prompt.
# -- Prints progress.
# === Loop through each code snippet ===
for i, item in enumerate(dataset[:MAX_REQUESTS]):
    file_path = item.get("file_path", f"snippet_{i}.py")
    code = item.get("transformed_code", "").strip()
    prompt = build_prompt(code)
    print(f"[{i+1}/{min(MAX_REQUESTS, len(dataset))}] Generating spec for: {file_path}")

    try:
        # New OpenAI API format (v1.0.0+)
        # Instantiates an OpenAI client with your API key.
        # -- Calls chat.completions.create with:
        #      – model (e.g., "gpt-4.1").
        #      – A system message telling the model to output a Dafny specification.
        #      – A user message containing the prompt (the code snippet).
        #      - temperature=0.2 for low randomness.
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
    with open("chatgpt_spec_errors.txt", "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ Saved {len(results)} specifications to '{OUTPUT_JSON}'")
if errors:
    print(f"⚠️ Encountered {len(errors)} errors. See 'chatgpt_spec_errors.txt'")