import subprocess
import json
import os
import tempfile
import re

# === CONFIG ===
GENERATED_OUTPUT_JSON = "output/chatgpt_specifications.json"
VERIFICATION_RESULTS_JSON = "output/dafny_verification_results.json"

# Check Dafny installation
def check_dafny_installed():
    try:
        result = subprocess.run(["dafny", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        print(f"Using Dafny version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("⚠️ Dafny not found. Ensure Dafny is installed and in your PATH.")
        return False

# Verify Dafny code snippet
def verify_with_dafny(code):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dfy", mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    # Run Dafny verification with modern syntax
    try:
        # Try modern syntax first
        result = subprocess.run(
            ["dafny", "verify", tmp_path, "/timeLimit:60"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        # Fall back to legacy syntax if needed
        result = subprocess.run(
            ["dafny", "/timeLimit:60", tmp_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            encoding="utf-8"
        )
    
    # Clean up temporary file
    os.remove(tmp_path)

    output = result.stdout + result.stderr

    # Check for actual verification, not just absence of errors
    verified = False
    
    # Look for this pattern in the output
    if "Dafny program verifier finished with" in output:
        # Parse the verification count - should be greater than 0
        match = re.search(r"(\d+) verified, (\d+) errors", output)
        if match:
            verified_count = int(match.group(1))
            error_count = int(match.group(2))
            verified = verified_count > 0 and error_count == 0

    return verified, output

# Extract Dafny code from the specification
def extract_dafny_code(text):
    """Extract Dafny code from the specification text."""
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

# Main verification function
def main():
    if not check_dafny_installed():
        return

    # Load your generated output dataset
    with open(GENERATED_OUTPUT_JSON, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for i, item in enumerate(dataset):
        file_path = item.get("file_path", f"snippet_{i}.dfy")
        spec_text = item.get("program_specification", "")
        
        # Extract Dafny code from specification
        dafny_code = extract_dafny_code(spec_text)
        
        if not dafny_code:
            print(f"⚠️ No Dafny code found for {file_path}. Skipping...")
            results.append({
                "file_path": file_path,
                "verified": False,
                "dafny_output": "No Dafny code found in specification"
            })
            continue

        print(f"🔍 Verifying {file_path}...")

        verified, output = verify_with_dafny(dafny_code)

        results.append({
            "file_path": file_path,
            "verified": verified,
            "dafny_output": output
        })

        if verified:
            print(f"✅ {file_path} verified successfully.")
        else:
            print(f"❌ {file_path} failed verification.")

    # Save verification results
    with open(VERIFICATION_RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Verification results saved to '{VERIFICATION_RESULTS_JSON}'.")

if __name__ == "__main__":
    main()
