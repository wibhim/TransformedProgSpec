import json
import os
import re
from config.settings import CONFIG

# Configuration
DAFNY_CONFIG = CONFIG["dafny"]
INPUT_JSON = DAFNY_CONFIG["input_json"]
OUTPUT_FOLDER = DAFNY_CONFIG["dafny_programs_dir"]

def extract_dafny_code(text):
    """Extract Dafny code from the specification text.
    Looks for code blocks between ```dafny and ``` markers.
    If no explicit Dafny blocks are found, looks for any code blocks.
    """
    # Try to find Dafny-specific code blocks first
    dafny_pattern = r"```(?:dafny|Dafny)(.*?)```"
    matches = re.findall(dafny_pattern, text, re.DOTALL)
    
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    
    # If no Dafny blocks found, try to find any code blocks
    code_pattern = r"```(.*?)```"
    matches = re.findall(code_pattern, text, re.DOTALL)
    
    if matches:
        # Filter out blocks that are clearly not Dafny
        dafny_blocks = []
        for match in matches:
            # Skip code blocks explicitly marked as other languages
            if match.startswith("python") or match.startswith("java") or match.startswith("csharp"):
                continue
            # Include blocks that have Dafny-like syntax
            if ("method" in match or "function" in match or 
                "predicate" in match or "requires" in match or 
                "ensures" in match or "class" in match):
                dafny_blocks.append(match.strip())
        
        if dafny_blocks:
            return "\n\n".join(dafny_blocks)
    
    # If still no code blocks found that look like Dafny, return empty string
    return ""

def sanitize_filename(file_path):
    """Convert file path to a valid filename."""
    # Remove the file extension if present
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    # Replace invalid characters
    valid_filename = re.sub(r'[\\/*?:"<>|]', "_", base_name)
    return valid_filename

def main():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created directory: {OUTPUT_FOLDER}")
    
    try:
        # Load the specifications
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} items from {INPUT_JSON}")
        
        # Process each item
        success_count = 0
        for item in data:
            file_path = item.get("file_path", "unknown")
            specification = item.get("program_specification", "")
            
            # Extract Dafny code
            dafny_code = extract_dafny_code(specification)
            
            if dafny_code:
                # Create a valid filename
                dafny_filename = sanitize_filename(file_path) + ".dfy"
                output_path = os.path.join(OUTPUT_FOLDER, dafny_filename)
                
                # Write the Dafny code to file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(dafny_code)
                    
                print(f"✅ Extracted Dafny code for {file_path} -> {dafny_filename}")
                success_count += 1
            else:
                print(f"❌ No Dafny code found for {file_path}")
        
        print(f"\nSummary: Extracted {success_count} out of {len(data)} Dafny programs to {OUTPUT_FOLDER}")
    
    except FileNotFoundError:
        print(f"❌ Error: Input file '{INPUT_JSON}' not found.")
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse '{INPUT_JSON}' as JSON.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()