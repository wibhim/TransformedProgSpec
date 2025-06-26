import openai
import json
import time
import os
import hashlib
import sqlite3
from datetime import datetime
from config.settings import CONFIG

# === CONFIG ===
CHATGPT_CONFIG = CONFIG["chatgpt"]
INPUT_JSON = CHATGPT_CONFIG["input_json"]
OUTPUT_JSON = CHATGPT_CONFIG["output_json"]
ERROR_LOG = CHATGPT_CONFIG["error_log"]
DELAY = CHATGPT_CONFIG["delay"]
TEMPERATURE = CHATGPT_CONFIG["temperature"]
TOKEN_FILE = CHATGPT_CONFIG["token_file"]

# Cache configuration
CACHE_DIR = os.path.join(CONFIG["DATA_DIR"], "cache")
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")
USE_CACHE = CHATGPT_CONFIG.get("use_cache", True)  # Default to True

# Specification type (from environment variables set by main.py)
SPEC_TYPE = os.environ.get("SPEC_TYPE", "transformed")  # Default to transformed
PROMPT_TEMPLATE = os.environ.get("PROMPT_TEMPLATE", None)

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
    """
    Build a prompt for the specification generation based on the specification type.
    
    Args:
        code: The Python code to generate specification for
        
    Returns:
        The formatted prompt
    """
    # If a custom prompt template is specified and we're in prompt_engineered mode
    if PROMPT_TEMPLATE and SPEC_TYPE == "prompt_engineered":
        try:
            with open(PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
                template = f.read()
                # Replace the {{code}} placeholder with the actual code
                return template.replace("{{code}}", code)
        except Exception as e:
            print(f"❌ Error loading prompt template: {e}")
            print("Falling back to default prompt...")
    
    # Default prompts based on specification type
    if SPEC_TYPE == "original":
        return f"""Here is the original Python code snippet:
```python
{code}

Generate a formal specification and Dafny program for this Python code. Include preconditions and postconditions that precisely capture the behavior and constraints of the original program.
"""
    elif SPEC_TYPE == "prompt_engineered":
        # Default prompt-engineered approach (used if no template provided)
        return f"""Here is the Python code snippet to analyze:
```python
{code}

You are an expert in Dafny formal verification. Follow these steps:
1. Carefully analyze the Python code to understand its purpose and behavior
2. Identify the preconditions that must be true before execution
3. Determine the postconditions that should hold after execution
4. Write a complete Dafny program that implements the same functionality
5. Include detailed formal specifications (requires/ensures)
6. Add appropriate loop invariants where needed
7. Ensure the Dafny program will verify correctly

Provide only the Dafny program with specifications, without additional explanations.
"""
    else:  # Default "transformed" type
        return f"""Here is the Python code snippet:
```python
{code}

You should only generate the specification and Dafny program for the above Python code without any additional context or explanation.
"""

# === Cache functions ===
def setup_cache():
    """Initialize the cache database."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # First, ensure backward compatibility - create the legacy table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL
    )
    ''')
    
    # Create the new table structure
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transformed_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL
    )
    ''')
    
    # Check if we need to migrate data from the old structure
    cursor.execute("SELECT COUNT(*) FROM specifications")
    legacy_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM transformed_specifications")
    new_count = cursor.fetchone()[0]
    
    # Only migrate if there's data in the legacy table and none in the new table
    if legacy_count > 0 and new_count == 0:
        print("Migrating data from legacy 'specifications' table...")
        cursor.execute('''
        INSERT OR IGNORE INTO transformed_specifications 
        SELECT hash, file_path, code, specification, timestamp, model, temperature
        FROM specifications
        ''')
        migrated = cursor.rowcount
        print(f"Migrated {migrated} entries")
    
    conn.commit()
    print(f"💾 Cache setup complete at {CACHE_DB}")
    return conn

def get_cached_specification(conn, code, file_path, spec_type=SPEC_TYPE):
    """
    Try to retrieve a cached specification.
    
    Args:
        conn: Database connection
        code: Python code to look up
        file_path: Path of the file
        spec_type: Type of specification ("original", "transformed", "prompt_engineered")
    
    Returns:
        The cached specification if found, None otherwise
    """
    if not USE_CACHE:
        return None
        
    cursor = conn.cursor()
    code_hash = hashlib.md5(code.encode()).hexdigest()
    
    # Determine which table to query based on spec_type
    if spec_type == "original":
        table = "original_specifications"
    elif spec_type == "prompt_engineered":
        table = "prompt_engineered_specifications"
    else:  # Default to transformed
        table = "transformed_specifications"
    
    # Try the new table structure first
    cursor.execute(f"SELECT specification FROM {table} WHERE hash = ?", (code_hash,))
    result = cursor.fetchone()
    
    if result:
        print(f"🔄 Using cached result for {file_path} (type: {spec_type})")
        return result[0]
    
    # Fall back to legacy table if needed (but only for transformed specs)
    if spec_type == "transformed":
        cursor.execute("SELECT specification FROM specifications WHERE hash = ?", (code_hash,))
        result = cursor.fetchone()
        
        if result:
            print(f"🔄 Using cached result from legacy table for {file_path}")
            return result[0]
            
    return None

def cache_specification(conn, code, file_path, specification, spec_type=SPEC_TYPE, prompt_template=PROMPT_TEMPLATE):
    """
    Save a specification to the cache.
    
    Args:
        conn: Database connection
        code: Python code to cache
        file_path: Path of the file
        specification: The generated specification
        spec_type: Type of specification ("original", "transformed", "prompt_engineered")
        prompt_template: The prompt template used (only for prompt_engineered)
    """
    if not USE_CACHE:
        return
        
    cursor = conn.cursor()
    code_hash = hashlib.md5(code.encode()).hexdigest()
    
    # Determine which table to use based on spec_type
    if spec_type == "original":
        table = "original_specifications"
        cursor.execute(
            f"INSERT OR REPLACE INTO {table} (hash, file_path, code, specification, timestamp, model, temperature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code_hash, file_path, code, specification, datetime.now().isoformat(), MODEL, TEMPERATURE)
        )
    elif spec_type == "prompt_engineered":
        table = "prompt_engineered_specifications"
        cursor.execute(
            f"INSERT OR REPLACE INTO {table} (hash, file_path, code, specification, timestamp, model, temperature, prompt_template) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code_hash, file_path, code, specification, datetime.now().isoformat(), MODEL, TEMPERATURE, prompt_template)
        )
    else:  # Default to transformed
        table = "transformed_specifications"
        cursor.execute(
            f"INSERT OR REPLACE INTO {table} (hash, file_path, code, specification, timestamp, model, temperature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code_hash, file_path, code, specification, datetime.now().isoformat(), MODEL, TEMPERATURE)
        )
        
        # For backward compatibility, also update the legacy table
        cursor.execute(
            "INSERT OR REPLACE INTO specifications (hash, file_path, code, specification, timestamp, model, temperature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code_hash, file_path, code, specification, datetime.now().isoformat(), MODEL, TEMPERATURE)
        )
    
    conn.commit()
    print(f"💾 Cached specification for {file_path} (type: {spec_type})")

# Get the appropriate key based on specification type
def get_code_key():
    """Get the JSON key to use for code based on specification type."""
    if SPEC_TYPE == "original":
        return "code"  # Original code
    else:
        return "transformed_code"  # Default to transformed code

# === Load the input JSON ===
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    dataset = json.load(f)

results = []
errors = []

# Setup cache
conn = setup_cache()

# Determine which code field to use (original or transformed)
code_key = get_code_key()

# === Loop through each code snippet ===
for i, item in enumerate(dataset[:MAX_REQUESTS]):
    file_path = item.get("file_path", f"snippet_{i}.py")
    
    # Use either original code or transformed code based on spec type
    if code_key in item:
        code = item.get(code_key, "").strip()
    else:
        print(f"⚠️ Warning: '{code_key}' not found in item {i}, falling back to 'transformed_code'")
        code = item.get("transformed_code", "").strip()
        
    # Skip empty code
    if not code:
        print(f"⚠️ Warning: Empty code for {file_path}, skipping...")
        continue
        
    prompt = build_prompt(code)
    print(f"[{i+1}/{min(MAX_REQUESTS, len(dataset))}] Generating {SPEC_TYPE} spec for: {file_path}")

    # Check cache first
    cached_spec = get_cached_specification(conn, code, file_path)
    if cached_spec:
        results.append({
            "file_path": file_path,
            code_key: code,
            "program_specification": cached_spec,
            "spec_type": SPEC_TYPE
        })
        continue  # Skip to next item

    try:
        # New OpenAI API format (v1.0.0+)
        client = openai.OpenAI(api_key=API_KEY)
        
        # Adjust system message based on specification type
        system_message = "You are an expert in Dafny Language. Your task is to generate a formal specification and Dafny program for the Python program. The specification should include postconditions and preconditions."
        if SPEC_TYPE == "prompt_engineered":
            system_message += " Be extremely precise and thorough in your specifications."
            
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE
        )

        # And access the content differently
        spec = response.choices[0].message.content

        results.append({
            "file_path": file_path,
            code_key: code,
            "program_specification": spec,
            "spec_type": SPEC_TYPE
        })

        # Cache the result
        cache_specification(conn, code, file_path, spec)

        time.sleep(DELAY)

    except Exception as e:
        print(f"❌ Error on {file_path}: {e}")
        errors.append({
            "file_path": file_path,
            "error": str(e),
            "spec_type": SPEC_TYPE
        })
        time.sleep(5)

# Define output file name based on specification type
output_prefix = SPEC_TYPE
OUTPUT_JSON = OUTPUT_JSON.replace("chatgpt_specifications.json", f"{output_prefix}_specifications.json")

# === Save results ===
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# === Optionally save errors ===
if errors:
    ERROR_LOG = ERROR_LOG.replace("chatgpt_spec_errors.txt", f"{output_prefix}_spec_errors.txt")
    with open(ERROR_LOG, "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e['file_path']} - {e['error']}\n")

print(f"\n✅ Saved {len(results)} specifications to '{OUTPUT_JSON}'")
if errors:
    print(f"⚠️ Encountered {len(errors)} errors. See '{ERROR_LOG}'")