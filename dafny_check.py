import subprocess
import json
import os
import tempfile

# === CONFIG ===
GENERATED_OUTPUT_JSON = "cleaned_code_dataset_ast.json"
VERIFICATION_RESULTS_JSON = "dafny_verification_results.json"

# Check Dafny installation
def check_dafny_installed():
    try:
        subprocess.run(["dafny", "/version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        print("⚠️ Dafny not found. Ensure Dafny is installed and in your PATH.")
        return False

# Verify Dafny code snippet
def verify_with_dafny(code):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dfy", mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    # Run Dafny verification
    result = subprocess.run(["dafny", tmp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    
    # Clean up temporary file
    os.remove(tmp_path)

    output = result.stdout + result.stderr

    verified = "0 errors" in output.lower() and "verified" in output.lower()

    return verified, output

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
        generated_code = item.get("generated_code", "")

        print(f"🔍 Verifying {file_path}...")

        verified, output = verify_with_dafny(generated_code)

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
