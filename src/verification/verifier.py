"""
Verifier module for verifying Dafny code.
"""

import os
import json
import subprocess
import time
from typing import Dict, Any, List, Tuple

from config.settings import CONFIG

def verify_dafny_file(file_path: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Verify a Dafny file using the Dafny verifier.
    
    Args:
        file_path: Path to the Dafny file
        timeout: Timeout in seconds
    
    Returns:
        Dictionary with verification results
    """
    result = {
        "file_path": file_path,
        "success": False,
        "duration": 0,
        "output": "",
        "error": "",
    }
    
    start_time = time.time()
    
    try:
        # Run Dafny verification command
        cmd = ["dafny", "/compile:0", "/timeLimit:" + str(timeout), file_path]
        process = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout + 5,  # Add a small buffer to the timeout
        )
        
        # Record results
        result["duration"] = time.time() - start_time
        result["output"] = process.stdout
        result["error"] = process.stderr
        result["success"] = process.returncode == 0
        result["return_code"] = process.returncode
        
    except subprocess.TimeoutExpired:
        result["duration"] = timeout
        result["error"] = "Verification timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """Verify all Dafny programs and save results."""
    print("Starting Dafny verification...")
    
    dafny_dir = CONFIG["dafny"]["dafny_programs_dir"]
    output_file = CONFIG["dafny"]["output_json"]
    timeout = CONFIG["dafny"]["timeout"]
    
    if not os.path.exists(dafny_dir):
        print(f"Error: Dafny programs directory {dafny_dir} does not exist.")
        return
    
    # Get all Dafny files
    dafny_files = [
        os.path.join(dafny_dir, f) for f in os.listdir(dafny_dir) 
        if f.endswith(".dfy")
    ]
    
    print(f"Found {len(dafny_files)} Dafny files to verify.")
    
    # Verify each file
    results = []
    for file_path in dafny_files:
        print(f"Verifying {os.path.basename(file_path)}...")
        result = verify_dafny_file(file_path, timeout)
        
        status = "✅ Success" if result["success"] else "❌ Failed"
        duration = f"{result['duration']:.2f}s"
        print(f"{status} ({duration})")
        
        results.append(result)
    
    # Save results to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    success_count = sum(1 for r in results if r["success"])
    print(f"\nVerification completed: {success_count}/{len(results)} successful.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
