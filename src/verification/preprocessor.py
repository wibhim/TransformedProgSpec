import json
import os
import re
from config.settings import CONFIG

# Configuration
DAFNY_CONFIG = CONFIG["dafny"]
INPUT_JSON = DAFNY_CONFIG["input_json"]
OUTPUT_FOLDER = DAFNY_CONFIG["dafny_programs_dir"]

def fix_common_errors(dafny_code):
    """Fix common syntax errors in generated Dafny code."""
    # Fix 1: Replace 'foreach' with 'for' (Dafny uses 'for' not 'foreach')
    fixed_code = re.sub(r'foreach\s+(\w+)\s+in\s+', r'for \1 in ', dafny_code)
    
    # Fix 2: Fix sum trigger syntax
    fixed_code = re.sub(r'sum\s+(\w+):\s+int\s+\{:trigger\s+(.*?)\}\s+::', 
                        r'sum(\1: int | \2 :: ', fixed_code)
    
    # Fix 3: Fix 2D array declarations
    fixed_code = re.sub(r'var\s+(\w+)\s*:=\s*new\s+bool\[(\w+)\]\[(\w+)\]', 
                        r'var \1 := new bool[\2, \3]', fixed_code)
    
    # Fix 4: Fix array access 
    fixed_code = re.sub(r'(\w+)\[(\w+)\]\[(\w+)\]', r'\1[\2, \3]', fixed_code)
    
    # Fix 5: Convert method use in ensures/requires to function
    # This is trickier because it requires actual code restructuring
    # For now, we'll add a warning comment
    if re.search(r'ensures.*\w+\(.*\)', fixed_code) or re.search(r'requires.*\w+\(.*\)', fixed_code):
        fixed_code = "// WARNING: This spec may use methods in ensures/requires clauses, which is not allowed.\n" + fixed_code
        fixed_code += "\n// NOTE: You should convert methods to functions when used in specifications."
    
    return fixed_code

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

def create_standalone_dafny(dafny_code, original_file_path):
    """Create a standalone Dafny file with debugging comments."""
    header = f"// Auto-generated Dafny file for {original_file_path}\n"
    header += f"// Generated from ChatGPT spec with automatic syntax fixes\n\n"
    
    return header + dafny_code

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
                # Apply syntax fixes
                fixed_dafny = fix_common_errors(dafny_code)
                
                # Create complete file content
                final_dafny = create_standalone_dafny(fixed_dafny, file_path)
                
                # Create a valid filename
                dafny_filename = sanitize_filename(file_path) + ".dfy"
                output_path = os.path.join(OUTPUT_FOLDER, dafny_filename)
                
                # Write the Dafny code to file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(final_dafny)
                    
                print(f"✅ Processed Dafny code for {file_path} -> {dafny_filename}")
                success_count += 1
            else:
                print(f"❌ No Dafny code found for {file_path}")
        
        print(f"\nSummary: Processed {success_count} out of {len(data)} Dafny programs to {OUTPUT_FOLDER}")
        print(f"Note: Fixed common syntax issues in the extracted Dafny code")
    
    except FileNotFoundError:
        print(f"❌ Error: Input file '{INPUT_JSON}' not found.")
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse '{INPUT_JSON}' as JSON.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
