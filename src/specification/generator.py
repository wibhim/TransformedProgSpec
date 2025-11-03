"""
Enhanced Specification Generator with File-Based Prompt Management

This module generates formal Dafny specifications from Python code using LLMs.

PROMPT SYSTEM:
- All prompts are loaded from external text files (no hardcoded prompts)
- Default prompt files: prompts/system_prompt.txt and prompts/user_prompt.txt
- Custom prompts can be specified via environment variables

ENVIRONMENT VARIABLES:
- SYSTEM_PROMPT_TEMPLATE: Path to custom system prompt file (.txt)
- USER_PROMPT_TEMPLATE: Path to custom user prompt file (.txt) 
- PROMPT_TEMPLATE: Alternative name for USER_PROMPT_TEMPLATE (backward compatibility)

REQUIRED FILES:
- prompts/system_prompt.txt (default system prompt)
- prompts/user_prompt.txt (default user prompt template)

USAGE MODES:
1. DEFAULT: Uses prompts/system_prompt.txt and prompts/user_prompt.txt
2. CUSTOM: Set environment variables to point to your custom prompt files

TEMPLATE FORMAT:
- User prompt templates should include {code} or {{code}} placeholder
- System prompts are used as-is (no placeholders)

EXAMPLE:
set SYSTEM_PROMPT_TEMPLATE=my_prompts\\custom_system.txt
set USER_PROMPT_TEMPLATE=my_prompts\\custom_user.txt
python generate_specs.py --input data.json
"""

import openai
import json
import time
import os
import hashlib
import sqlite3
from datetime import datetime
from config.settings import CONFIG

# Import enhanced cache system
from enhanced_cache_system import (
    EnhancedCacheManager, 
    create_generation_session,
    cache_enhanced_specification,
    get_enhanced_cached_specification,
    export_session_to_json,
    get_session_progress
)

# Pricing for OpenAI models (per 1K tokens) - Updated August 2025
PRICING = {
    # GPT-4 family
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.0025, "output": 0.01},  # Updated pricing
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    
    # GPT-4.1 family (much cheaper!)
    "gpt-4.1": {"input": 0.002, "output": 0.008},  # Fixed from official pricing
    "gpt-4_1-2025-04-14": {"input": 0.002, "output": 0.008},  # Handle variants
    "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},  # Based on pattern
    "gpt-4.1-nano": {"input": 0.0001, "output": 0.0004},  # Based on pattern
    
    # GPT-3.5 family
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    
    # GPT-5 family (placeholder for future)
    "gpt-5": {"input": 0.00125, "output": 0.01},
    "gpt-5-mini": {"input": 0.00025, "output": 0.002},
    "gpt-5-nano": {"input": 0.00005, "output": 0.0004},
    
    # Conservative fallback for unknown models
    "default": {"input": 0.005, "output": 0.015}
}

# Last pricing update date for maintenance tracking
PRICING_LAST_UPDATED = "2025-08-13"

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
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")  # Legacy cache
ENHANCED_CACHE_DB = os.path.join(CACHE_DIR, "enhanced_specification_cache.db")  # New enhanced cache
USE_CACHE = CHATGPT_CONFIG.get("use_cache", True)  # Default to True
USE_ENHANCED_CACHE = CHATGPT_CONFIG.get("use_enhanced_cache", True)  # Use new enhanced cache by default

# Initialize enhanced cache manager
enhanced_cache_manager = EnhancedCacheManager(ENHANCED_CACHE_DB) if USE_ENHANCED_CACHE else None

# -----------------------------------------------------------------------------
# Local default environment overrides (optional)
#
# Edit these values if you want to avoid setting environment variables via CLI
# (e.g., Windows `set` commands). These act as defaults and will NOT override
# values already present in the environment.
# -----------------------------------------------------------------------------
os.environ.setdefault("SYSTEM_PROMPT_TEMPLATE", "prompts/from_spec_system.txt")
os.environ.setdefault("USER_PROMPT_TEMPLATE", "prompts/from_spec_user.txt")
os.environ.setdefault("SPEC_TYPE", "prompt_engineered")
os.environ.setdefault("INPUT_TEXT_FIELD", "original_spec")

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

MODEL = CHATGPT_CONFIG.get("model", "gpt-4.1")  # Get model from config, default to gpt-4.1
# MAX_REQUESTS will be set dynamically based on dataset size

# === OpenAI API setup ===
openai.api_key = API_KEY

# =============================================================================
# === PROMPT TEMPLATES SECTION ===
# =============================================================================

# Default prompt file paths (can be overridden by environment variables)
DEFAULT_SYSTEM_PROMPT_FILE = "prompts/system_prompt_2.txt"
DEFAULT_USER_PROMPT_FILE = "prompts/prompt_eng_14.txt"

# =============================================================================
# === PROMPT MANAGEMENT FUNCTIONS ===
# =============================================================================

def load_system_prompt():
    """
    Load system prompt from template file.
    
    Environment Variable: SYSTEM_PROMPT_TEMPLATE (overrides default file)
    Default: prompts/system_prompt.txt
    
    Returns:
        The system prompt string
    """
    system_template_path = os.environ.get("SYSTEM_PROMPT_TEMPLATE", DEFAULT_SYSTEM_PROMPT_FILE)
    
    if os.path.exists(system_template_path):
        try:
            with open(system_template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"📝 Using system prompt from: {system_template_path}")
                return content
        except Exception as e:
            print(f"❌ Error loading system prompt from {system_template_path}: {e}")
    else:
        print(f"❌ System prompt file not found: {system_template_path}")
    
    # If we reach here, there's a problem
    raise FileNotFoundError(f"System prompt file not found: {system_template_path}")

def load_user_prompt_template():
    """
    Load user prompt template from template file.
    
    Environment Variables: USER_PROMPT_TEMPLATE (overrides default) or PROMPT_TEMPLATE
    Default: prompts/user_prompt.txt
    
    Template should include {code} placeholder for Python code insertion.
    
    Returns:
        The user prompt template string (with {code} placeholder)
    """
    user_template_path = (os.environ.get("USER_PROMPT_TEMPLATE", None) or 
                          PROMPT_TEMPLATE or 
                          DEFAULT_USER_PROMPT_FILE)
    
    if os.path.exists(user_template_path):
        try:
            with open(user_template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📝 Using user prompt from: {user_template_path}")
                return content
        except Exception as e:
            print(f"❌ Error loading user prompt from {user_template_path}: {e}")
    else:
        print(f"❌ User prompt file not found: {user_template_path}")
    
    # If we reach here, there's a problem
    raise FileNotFoundError(f"User prompt file not found: {user_template_path}")

def build_prompt(code):
    """
    Build the final user prompt by inserting code into the template.
    
    Args:
        code: The Python code to generate specification for
        
    Returns:
        The formatted prompt
    """
    template = load_user_prompt_template()
    
    # Support multiple placeholder names commonly used in templates.
    # We treat the incoming 'code' value as the canonical input text and
    # substitute it for any of these placeholders if present.
    formatted_prompt = template
    for key in ("code", "spec", "text", "input"):
        formatted_prompt = formatted_prompt.replace(f"{{{{{key}}}}}", code)
        formatted_prompt = formatted_prompt.replace(f"{{{key}}}", code)

    # Simple diagnostic if placeholders seem un-replaced
    if "{code}" in formatted_prompt or "{spec}" in formatted_prompt:
        print("⚠️ Warning: Unreplaced placeholders remain in user prompt. Check template.")
    return formatted_prompt

def print_prompt_info(verbose=False):
    """
    Print information about the current prompt configuration.
    
    Args:
        verbose: If True, print the actual prompt content
    """
    system_template = os.environ.get("SYSTEM_PROMPT_TEMPLATE", DEFAULT_SYSTEM_PROMPT_FILE)
    user_template = (os.environ.get("USER_PROMPT_TEMPLATE", None) or 
                     PROMPT_TEMPLATE or 
                     DEFAULT_USER_PROMPT_FILE)
    
    print(f"📋 Prompt Configuration:")
    print(f"   System Prompt File: {system_template}")
    print(f"   User Prompt File: {user_template}")
    
    if verbose:
        try:
            print(f"\n--- Current System Prompt ---")
            print(load_system_prompt())
            print(f"\n--- Current User Prompt Template ---")
            print(load_user_prompt_template())
            print("--- End Prompt Content ---\n")
        except FileNotFoundError as e:
            print(f"❌ Cannot display prompt content: {e}")
            print("--- End Prompt Content ---\n")

# ============================================================================= Cache functions ===
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
    
    # Create table for original specifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS original_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL
    )
    ''')
    
    # Create table for prompt engineered specifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompt_engineered_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL,
        prompt_template TEXT
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
    try:
        cursor.execute(f"SELECT specification FROM {table} WHERE hash = ?", (code_hash,))
        result = cursor.fetchone()
        
        if result:
            print(f"🔄 Using cached result for {file_path} (type: {spec_type})")
            return result[0]
    except sqlite3.OperationalError as e:
        print(f"⚠️ Cache table {table} not accessible: {e}")
    
    # Fall back to legacy table if needed (but only for transformed specs)
    if spec_type == "transformed":
        try:
            cursor.execute("SELECT specification FROM specifications WHERE hash = ?", (code_hash,))
            result = cursor.fetchone()
            
            if result:
                print(f"🔄 Using cached result from legacy table for {file_path}")
                return result[0]
        except sqlite3.OperationalError as e:
            print(f"⚠️ Legacy cache table not accessible: {e}")
            
    return None

def normalize_model_name(model: str) -> str:
    """Normalize model names to handle variants and versions."""
    model = model.lower().strip()
    
    # Handle common variations and version-specific models
    if "gpt-4_1" in model or "gpt-4.1" in model:
        if "mini" in model:
            return "gpt-4.1-mini"
        elif "nano" in model:
            return "gpt-4.1-nano"
        else:
            return "gpt-4.1"
    elif "gpt-4o" in model:
        if "mini" in model:
            return "gpt-4o-mini"
        else:
            return "gpt-4o"
    elif "gpt-4" in model:
        if "turbo" in model:
            return "gpt-4-turbo"
        else:
            return "gpt-4"
    elif "gpt-5" in model:
        if "mini" in model:
            return "gpt-5-mini"
        elif "nano" in model:
            return "gpt-5-nano"
        else:
            return "gpt-5"
    elif "gpt-3.5" in model or "gpt3.5" in model:
        return "gpt-3.5-turbo"
    
    return model

def model_supports_temperature(model: str) -> bool:
    """Check if a model supports temperature parameter."""
    model_lower = model.lower().strip()
    
    # Models that don't support temperature
    no_temperature_models = [
        "gpt-5",
        "gpt-5-mini", 
        "gpt-5-nano"
    ]
    
    # Check if model is in the no-temperature list
    for no_temp_model in no_temperature_models:
        if no_temp_model in model_lower:
            return False
    
    # All other models support temperature by default
    return True

def get_temperature_support_info():
    """Get information about which models support temperature."""
    return {
        "supports_temperature": [
            "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", 
            "gpt-3.5-turbo"
        ],
        "no_temperature_support": [
            "gpt-5", "gpt-5-mini", "gpt-5-nano"
        ]
    }

def check_pricing_age():
    """Check if pricing table needs updating."""
    try:
        last_update = datetime.fromisoformat(PRICING_LAST_UPDATED)
        days_since_update = (datetime.now() - last_update).days
        
        if days_since_update > 30:
            print(f"⚠️ Pricing table is {days_since_update} days old")
            print(f"💡 Consider checking: https://openai.com/pricing")
            print(f"📅 Last updated: {PRICING_LAST_UPDATED}")
            return True
    except:
        print(f"⚠️ Could not parse pricing update date: {PRICING_LAST_UPDATED}")
        return True
    
    return False

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for OpenAI API usage with enhanced model handling."""
    # Check if pricing table is stale
    check_pricing_age()
    
    # Normalize model name for consistent lookup
    normalized_model = normalize_model_name(model)
    
    # Try to find pricing for normalized model
    if normalized_model in PRICING:
        pricing = PRICING[normalized_model]
    else:
        # Use fallback pricing for unknown models
        pricing = {"input": 0.01, "output": 0.03}  # Conservative fallback
        print(f"⚠️ Unknown model '{model}' (normalized: '{normalized_model}')")
        print(f"💰 Using fallback pricing: ${pricing['input']:.3f}/${pricing['output']:.3f} per 1K tokens")
    
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    total_cost = input_cost + output_cost
    
    # Debug logging for cost calculation
    if input_tokens > 0 or output_tokens > 0:
        print(f"💰 Cost breakdown for {model}:")
        print(f"   Input: {input_tokens:,} tokens × ${pricing['input']:.4f} = ${input_cost:.4f}")
        print(f"   Output: {output_tokens:,} tokens × ${pricing['output']:.4f} = ${output_cost:.4f}")
        print(f"   Total: ${total_cost:.4f}")
    
    return total_cost

def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"

def create_usage_stats(start_time: float, end_time: float, usage_data: dict, model: str) -> dict:
    """Create comprehensive usage statistics."""
    duration = end_time - start_time
    
    input_tokens = usage_data.get('prompt_tokens', 0)
    output_tokens = usage_data.get('completion_tokens', 0)
    total_tokens = usage_data.get('total_tokens', input_tokens + output_tokens)
    
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    return {
        "duration_seconds": round(duration, 3),
        "duration_formatted": format_duration(duration),
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens
        },
        "cost_usd": round(cost, 6),
        "model": model,
        "timestamp": datetime.now().isoformat()
    }

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
    try:
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
        
    except sqlite3.OperationalError as e:
        print(f"⚠️ Could not cache specification for {file_path}: {e}")
        # Try to setup cache again
        setup_cache()

def get_cache_stats(conn, spec_type=SPEC_TYPE):
    """Get statistics about cached specifications.
    
    Args:
        conn: Database connection
        spec_type: Type of specification to check
        
    Returns:
        Dictionary with cache statistics
    """
    cursor = conn.cursor()
    
    # Determine which table to query
    if spec_type == "original":
        table = "original_specifications"
    elif spec_type == "prompt_engineered":
        table = "prompt_engineered_specifications"
    else:
        table = "transformed_specifications"
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM {table}")
        time_range = cursor.fetchone()
        
        return {
            "cached_count": count,
            "first_cached": time_range[0] if time_range[0] else None,
            "last_cached": time_range[1] if time_range[1] else None,
            "table": table
        }
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return {
            "cached_count": 0,
            "first_cached": None,
            "last_cached": None,
            "table": table
        }

def build_output_from_cache(output_file=None, spec_type=SPEC_TYPE):
    """Build output JSON file from current cache contents.
    
    Args:
        output_file: Optional custom output file path
        spec_type: Type of specification to build
        
    Returns:
        Path to the created output file
    """
    conn = setup_cache()
    cursor = conn.cursor()
    
    # Determine which table to query
    if spec_type == "original":
        table = "original_specifications"
    elif spec_type == "prompt_engineered":
        table = "prompt_engineered_specifications"
    else:
        table = "transformed_specifications"
    
    # Get all cached specifications
    try:
        cursor.execute(f"""
            SELECT file_path, code, specification, timestamp, model, temperature 
            FROM {table} 
            ORDER BY timestamp ASC
        """)
        cached_specs = cursor.fetchall()
    except sqlite3.OperationalError:
        print(f"❌ Table {table} doesn't exist yet - no cached specifications")
        return None
    
    if not cached_specs:
        print(f"📭 No cached specifications found in {table}")
        return None
    
    # Build results list
    results = []
    for file_path, code, specification, timestamp, model, temperature in cached_specs:
        result = {
            "file_path": file_path,
            "code": code,
            "program_specification": specification,
            "spec_type": spec_type,
            "usage_stats": {
                "model": model,
                "temperature": temperature,
                "timestamp": timestamp,
                "source": "cache"
            }
        }
        results.append(result)
    
    # Create metadata
    metadata = {
        "summary": {
            "total_programs": len(results),
            "api_requests": 0,
            "cached_results": len(results),
            "errors": 0,
            "success_rate": "100.0%"
        },
        "note": f"Built from cache on {datetime.now().isoformat()}",
        "cache_info": {
            "table": table,
            "spec_type": spec_type,
            "first_cached": cached_specs[0][3] if cached_specs else None,
            "last_cached": cached_specs[-1][3] if cached_specs else None
        }
    }
    
    # Determine output file
    if not output_file:
        output_prefix = spec_type
        output_file = OUTPUT_JSON.replace("chatgpt_specifications.json", f"{output_prefix}_specifications_from_cache.json")
    
    # Save output
    output_data = {
        "metadata": metadata,
        "specifications": results
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Built output file from cache: {output_file}")
    print(f"📊 Contains {len(results)} specifications")
    conn.close()
    
    return output_file

def check_cache_progress(dataset_file=None, spec_type=SPEC_TYPE):
    """Check generation progress against a dataset.
    
    Args:
        dataset_file: Path to dataset file (uses INPUT_JSON if None)
        spec_type: Type of specification to check
        
    Returns:
        Dictionary with progress information
    """
    # Load dataset
    if not dataset_file:
        dataset_file = INPUT_JSON
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # Handle different dataset structures
    if isinstance(raw_data, dict) and 'data' in raw_data:
        dataset = raw_data['data']
    elif isinstance(raw_data, dict) and 'programs' in raw_data:
        dataset = raw_data['programs']
    elif isinstance(raw_data, list):
        dataset = raw_data
    else:
        raise ValueError(f"Unexpected dataset structure: {type(raw_data)}")
    
    # Get cache stats
    conn = setup_cache()
    cache_stats = get_cache_stats(conn, spec_type)
    conn.close()
    
    total_programs = len(dataset)
    cached_count = cache_stats['cached_count']
    remaining = total_programs - cached_count
    
    progress = {
        "total_programs": total_programs,
        "completed": cached_count,
        "remaining": remaining,
        "progress_percent": round((cached_count / total_programs) * 100, 1) if total_programs > 0 else 0,
        "cache_stats": cache_stats
    }
    
    return progress

# Get the appropriate key based on specification type
def get_code_key():
    """Get the JSON key to use for code based on specification type.

    Allows overriding via environment variable INPUT_TEXT_FIELD to support
    alternate dataset shapes (e.g., verified-only files where the text is
    under "original_spec"). Defaults to "code".
    """
    return os.environ.get("INPUT_TEXT_FIELD", "code")

def generate_specifications(limit=None):
    """Main function to generate specifications from the input dataset with enhanced caching.
    
    Args:
        limit (int, optional): Maximum number of programs to process. If None, processes all.
    """
    # Print prompt configuration info
    print_prompt_info(verbose=False)
    
    # === Load the input JSON ===
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # Handle common wrappers and direct list structures
    if isinstance(raw_data, dict) and 'data' in raw_data:
        dataset = raw_data['data']
        print(f"📊 Loaded dataset with metadata wrapper: {len(dataset)} programs")
    elif isinstance(raw_data, dict) and 'programs' in raw_data:
        dataset = raw_data['programs']
        print(f"📊 Loaded consolidated dataset: {len(dataset)} programs")
    elif isinstance(raw_data, dict) and 'results' in raw_data:
        # Support for verified-only JSON artifacts: { metadata: {...}, results: [...] }
        dataset = raw_data['results']
        print(f"📊 Loaded verified-only dataset: {len(dataset)} items")
    elif isinstance(raw_data, list):
        dataset = raw_data
        print(f"📊 Loaded direct dataset: {len(dataset)} programs")
    else:
        raise ValueError(f"Unexpected dataset structure: {type(raw_data)}")

    results = []
    errors = []

    # Setup legacy cache for backward compatibility
    conn = None
    if USE_CACHE:
        conn = setup_cache()
    
    # Create enhanced cache session
    session_id = None
    if USE_ENHANCED_CACHE and enhanced_cache_manager:
        session_id = create_generation_session(
            session_id=f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model=MODEL
        )
        print(f"🎯 Created enhanced cache session: {session_id}")
        print(f"💾 Using enhanced cache database: {ENHANCED_CACHE_DB}")
    elif USE_CACHE:
        print(f"💾 Using legacy cache database: {CACHE_DB}")
    else:
        print("⚠️ Cache is disabled - all API calls will be fresh")

    # Determine which code field to use (original or transformed)
    code_key = get_code_key()
    
    # Set max requests to process - use limit if provided, otherwise all programs
    if limit is not None and limit > 0:
        max_requests = min(limit, len(dataset))
        print(f"🎯 Processing {max_requests} programs (limited from {len(dataset)})")
        dataset_to_process = dataset[:max_requests]
    else:
        max_requests = len(dataset)
        print(f"🎯 Processing all {max_requests} programs")
        dataset_to_process = dataset

    # === Loop through each code snippet ===
    for i, item in enumerate(dataset_to_process):
        # File path and identifiers: support alternate keys from verified-only
        file_path = (
            item.get("file_path")
            or item.get("filename")
            or item.get("source_file")
            or f"program_{str(i+1).zfill(3)}.py"
        )
        task_id = item.get("task_id") or item.get("specification_index")
        transformation_type = (
            item.get("transformation_type")
            or item.get("transformation")
            or "unknown"
        )
        
        # Debug: show what transformation type we're processing
        print(f"Processing item {i}: transformation_type = {transformation_type}")
        
        # Use the code field (which contains original code for original transformation, 
        # and transformed code for other transformations). If the preferred key isn't
        # present, try common fallbacks to support verified-only inputs.
        code = None
        tried_keys = []
        candidate_keys = [code_key] if code_key else []
        candidate_keys += [
            k for k in ("code", "original_spec", "specification", "dafny_code", "text")
            if k not in candidate_keys
        ]
        for k in candidate_keys:
            tried_keys.append(k)
            if k in item and isinstance(item.get(k), str):
                code = item.get(k, "").strip()
                if code:
                    print(f"  Using key '{k}' for transformation '{transformation_type}'")
                    break
        if code is None or not code:
            print(f"❌ Error: none of {tried_keys} found with non-empty text in item {i}")
            continue
            
        # Skip empty code
        if not code:
            print(f"⚠️ Warning: Empty code for {file_path}, skipping...")
            continue

        print(f"  Code length: {len(code)} characters")
            
        prompt = build_prompt(code)
        print(f"[{i+1}/{max_requests}] Generating {SPEC_TYPE} spec for: {file_path}")

        # Check enhanced cache first
        cached_result = None
        if USE_ENHANCED_CACHE and enhanced_cache_manager:
            cached_result = get_enhanced_cached_specification(code, SPEC_TYPE)
            if cached_result:
                print(f"💾 Using ENHANCED cached specification")
        
        # Fall back to legacy cache
        if not cached_result and USE_CACHE and conn:
            cached_spec = get_cached_specification(conn, code, file_path)
            if cached_spec:
                print(f"💾 Using LEGACY cached specification")
                cached_result = {
                    "file_path": file_path,
                    "code": code,
                    "program_specification": cached_spec,
                    "spec_type": SPEC_TYPE,
                    "transformation_type": transformation_type,
                    "usage_stats": {
                        "cached": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }
        
        if cached_result:
            print(f"💾 Using cached specification")
            results.append(cached_result)
            continue  # Skip to next item

        try:
            # Record start time
            start_time = time.time()
            
            # New OpenAI API format (v1.0.0+)
            client = openai.OpenAI(api_key=API_KEY)
            
            # Get system prompt (default or custom)
            system_message = load_system_prompt()
            
            print(f"🔄 Making API call to {MODEL}...")
            
            # Prepare API call parameters
            api_params = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Add temperature only if model supports it
            if model_supports_temperature(MODEL):
                api_params["temperature"] = TEMPERATURE
                print(f"🌡️  Using temperature: {TEMPERATURE}")
            else:
                print(f"⚠️  Model {MODEL} doesn't support temperature - using default behavior")
                
            response = client.chat.completions.create(**api_params)

            # Record end time
            end_time = time.time()
            
            # Extract response content
            spec = response.choices[0].message.content
            
            # Create usage statistics
            usage_stats = create_usage_stats(
                start_time=start_time,
                end_time=end_time,
                usage_data=response.usage.__dict__ if hasattr(response, 'usage') else {},
                model=MODEL
            )
            
            # Print usage information
            print(f"⏱️  Duration: {usage_stats['duration_formatted']}")
            print(f"🎯 Tokens: {usage_stats['tokens']['total']} (in: {usage_stats['tokens']['input']}, out: {usage_stats['tokens']['output']})")
            print(f"💰 Cost: ${usage_stats['cost_usd']:.6f}")

            # Create result object
            result = {
                "file_path": file_path,
                "code": code,  # Always use "code" as the key
                "program_specification": spec,
                "spec_type": SPEC_TYPE,
                "transformation_type": item.get("transformation_type", "unknown"),
                "usage_stats": usage_stats
            }
            
            results.append(result)

            # Cache the result in both systems
            if USE_CACHE and conn:
                cache_specification(conn, code, file_path, spec)
                print(f"💾 Cached in LEGACY system")
                
            if USE_ENHANCED_CACHE and session_id and enhanced_cache_manager:
                cache_enhanced_specification(
                    session_id=session_id,
                    code=code,
                    file_path=file_path,
                    specification=spec,
                    spec_type=SPEC_TYPE,
                    transformation_type=transformation_type,
                    usage_stats=usage_stats
                )
                print(f"💾 Cached in ENHANCED system")
            
            # Auto-save progress every 10 programs
            if len(results) % 10 == 0:
                if USE_ENHANCED_CACHE and session_id:
                    # Update enhanced cache metadata
                    enhanced_cache_manager.update_session_metadata(session_id)
                    # Export current progress
                    progress_file = OUTPUT_JSON.replace(".json", f"_enhanced_progress_{len(results)}.json")
                    try:
                        export_session_to_json(session_id, progress_file)
                        print(f"📊 Enhanced progress saved: {len(results)} specifications completed")
                    except Exception as save_error:
                        print(f"⚠️ Could not save enhanced progress file: {save_error}")
                else:
                    # Legacy progress saving
                    progress_file = OUTPUT_JSON.replace(".json", f"_progress_{len(results)}.json")
                    try:
                        build_output_from_cache(progress_file, SPEC_TYPE)
                        print(f"📊 Progress saved: {len(results)} specifications completed")
                    except Exception as save_error:
                        print(f"⚠️ Could not save progress file: {save_error}")

            time.sleep(DELAY)

        except Exception as e:
            print(f"❌ Error on {file_path}: {e}")
            errors.append({
                "file_path": file_path,
                "error": str(e),
                "spec_type": SPEC_TYPE
            })
            time.sleep(5)

    # Calculate overall statistics
    total_requests = len([r for r in results if 'usage_stats' in r])
    total_cached = len(results) - total_requests
    
    if total_requests > 0:
        # Aggregate usage statistics
        total_duration = sum(r['usage_stats']['duration_seconds'] for r in results if 'usage_stats' in r)
        total_cost = sum(r['usage_stats']['cost_usd'] for r in results if 'usage_stats' in r)
        total_tokens = sum(r['usage_stats']['tokens']['total'] for r in results if 'usage_stats' in r)
        total_input_tokens = sum(r['usage_stats']['tokens']['input'] for r in results if 'usage_stats' in r)
        total_output_tokens = sum(r['usage_stats']['tokens']['output'] for r in results if 'usage_stats' in r)
        
        # Create summary statistics
        overall_stats = {
            "summary": {
                "total_programs": len(results),
                "api_requests": total_requests,
                "cached_results": total_cached,
                "errors": len(errors),
                "success_rate": f"{((len(results) / (len(results) + len(errors))) * 100):.1f}%" if results or errors else "0%"
            },
            "timing": {
                "total_duration_seconds": round(total_duration, 3),
                "total_duration_formatted": format_duration(total_duration),
                "average_per_request_seconds": round(total_duration / total_requests, 3) if total_requests > 0 else 0
            },
            "tokens": {
                "total": total_tokens,
                "input": total_input_tokens,
                "output": total_output_tokens,
                "average_per_request": round(total_tokens / total_requests, 1) if total_requests > 0 else 0
            },
            "cost": {
                "total_usd": round(total_cost, 6),
                "average_per_request_usd": round(total_cost / total_requests, 6) if total_requests > 0 else 0,
                "cost_per_token_usd": round(total_cost / total_tokens, 8) if total_tokens > 0 else 0
            },
            "model": MODEL,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n📊 GENERATION SUMMARY")
        print(f"=" * 50)
        print(f"✅ Total Programs: {overall_stats['summary']['total_programs']}")
        print(f"🔄 API Requests: {overall_stats['summary']['api_requests']}")
        print(f"💾 Cached Results: {overall_stats['summary']['cached_results']}")
        print(f"❌ Errors: {overall_stats['summary']['errors']}")
        print(f"📈 Success Rate: {overall_stats['summary']['success_rate']}")
        print(f"⏱️  Total Time: {overall_stats['timing']['total_duration_formatted']}")
        print(f"⚡ Avg per Request: {overall_stats['timing']['average_per_request_seconds']:.2f}s")
        print(f"🎯 Total Tokens: {overall_stats['tokens']['total']:,}")
        print(f"💰 Total Cost: ${overall_stats['cost']['total_usd']:.6f}")
        print(f"💵 Avg Cost/Request: ${overall_stats['cost']['average_per_request_usd']:.6f}")
        print(f"💸 Cost per Token: ${overall_stats['cost']['cost_per_token_usd']:.8f}")
    else:
        overall_stats = {
            "summary": {
                "total_programs": len(results),
                "api_requests": 0,
                "cached_results": len(results),
                "errors": len(errors),
                "success_rate": "100%" if results and not errors else "0%"
            },
            "note": "All results from cache - no API calls made"
        }
        print(f"\n📊 GENERATION SUMMARY")
        print(f"=" * 50)
        print(f"✅ Total Programs: {overall_stats['summary']['total_programs']}")
        print(f"💾 All results from cache - no API calls needed!")

    # Define output file name based on specification type
    output_prefix = SPEC_TYPE
    output_file = OUTPUT_JSON.replace("chatgpt_specifications.json", f"{output_prefix}_specifications.json")

    # === Save results with statistics ===
    output_data = {
        "metadata": overall_stats,
        "specifications": results
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # === Optionally save errors ===
    if errors:
        error_log = ERROR_LOG.replace("chatgpt_spec_errors.txt", f"{output_prefix}_spec_errors.txt")
        with open(error_log, "w", encoding="utf-8") as f:
            for e in errors:
                f.write(f"{e['file_path']} - {e['error']}\n")

    print(f"\n✅ Saved {len(results)} specifications to '{output_file}'")
    if errors:
        print(f"⚠️ Encountered {len(errors)} errors. See '{error_log}'")
    
    # Close database connections
    if conn:
        conn.close()
        print("💾 Closed legacy cache connection")
    
    return True

# For backward compatibility, run the function if the module is executed directly
if __name__ == "__main__":
    generate_specifications()