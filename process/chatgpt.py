import openai
import json
import time
import os
import hashlib
import sqlite3
from datetime import datetime
from config import CONFIG

# === CONFIG ===
CHATGPT_CONFIG = CONFIG["chatgpt"]
INPUT_JSON = CHATGPT_CONFIG["input_json"]
OUTPUT_JSON = CHATGPT_CONFIG["output_json"]
ERROR_LOG = CHATGPT_CONFIG["error_log"]
DELAY = CHATGPT_CONFIG["delay"]
TEMPERATURE = CHATGPT_CONFIG["temperature"]
TOKEN_FILE = CHATGPT_CONFIG["token_file"]

# Cache configuration
CACHE_DIR = os.path.join(CONFIG["OUTPUT_DIR"], "cache")
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")
USE_CACHE = CHATGPT_CONFIG.get("use_cache", True)  # Default to True

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

def get_cached_specification(conn, code, file_path, spec_type="transformed"):
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

def cache_specification(conn, code, file_path, specification, spec_type="transformed", prompt_template=None):
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

# === Load the input JSON ===
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    dataset = json.load(f)

results = []
errors = []

# Setup cache
conn = setup_cache()

# === Loop through each code snippet ===
for i, item in enumerate(dataset[:MAX_REQUESTS]):
    file_path = item.get("file_path", f"snippet_{i}.py")
    code = item.get("transformed_code", "").strip()
    prompt = build_prompt(code)
    print(f"[{i+1}/{min(MAX_REQUESTS, len(dataset))}] Generating spec for: {file_path}")

    # Check cache first
    cached_spec = get_cached_specification(conn, code, file_path)
    if cached_spec:
        results.append({
            "file_path": file_path,
            "transformed_code": code,
            "program_specification": cached_spec
        })
        continue  # Skip to next item

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

        # Cache the result
        cache_specification(conn, code, file_path, spec)

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