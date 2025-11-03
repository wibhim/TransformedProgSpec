#!/usr/bin/env python3
"""
Dafny Verification Script with Dual Mode Support

This script can:
1. Convert JSON specifications to Dafny programs and verify them
2. Verify existing Dafny files directly

Supports detailed error reporting in both modes.
"""

import os
import sys
import json
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

def extract_dafny_code(specification_text: str) -> Optional[str]:
    """
    Extract Dafny code from a specification text that may contain markdown formatting.
    
    Args:
        specification_text: The raw specification text from ChatGPT
        
    Returns:
        Clean Dafny code or None if no Dafny code found
    """
    # Look for Dafny code blocks in markdown
    dafny_patterns = [
        r'```dafny\s*\n(.*?)\n```',  # ```dafny ... ```
        r'```\s*\n(.*?)\n```',       # Generic code blocks
        r'module\s+\w+\s*\{.*?\}',   # Direct module definitions
    ]
    
    for pattern in dafny_patterns:
        matches = re.findall(pattern, specification_text, re.DOTALL | re.IGNORECASE)
        if matches:
            # Take the longest match (likely most complete)
            dafny_code = max(matches, key=len).strip()
            
            # Clean up common markdown artifacts
            dafny_code = re.sub(r'^#.*$', '', dafny_code, flags=re.MULTILINE)  # Remove markdown headers
            dafny_code = re.sub(r'\*\*(.*?)\*\*', r'\1', dafny_code)  # Remove bold formatting
            dafny_code = re.sub(r'\*(.*?)\*', r'\1', dafny_code)      # Remove italic formatting
            
            return dafny_code.strip()
    
    # If no code blocks found, check if the entire text looks like Dafny
    if any(keyword in specification_text for keyword in ['module', 'method', 'function', 'requires', 'ensures']):
        return specification_text.strip()
    
    return None

def save_dafny_program(dafny_code: str, output_path: Path) -> bool:
    """
    Save Dafny code to a .dfy file.
    
    Args:
        dafny_code: The Dafny program code
        output_path: Path to save the .dfy file
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dafny_code)
        
        return True
    except Exception as e:
        print(f"❌ Error saving {output_path}: {e}")
        return False

def verify_dafny_program(dfy_file: Path, timeout: int = 60) -> Dict:
    """
    Verify a Dafny program using the Dafny compiler with detailed error reporting.
    
    Args:
        dfy_file: Path to the .dfy file
        timeout: Timeout in seconds for verification
        
    Returns:
        Dictionary with detailed verification results and error information
    """
    result = {
        "file": str(dfy_file),
        "success": False,
        "verified": False,
        "compilation_success": False,
        "errors": [],
        "warnings": [],
        "parse_errors": [],
        "verification_errors": [],
        "verification_time": 0,
        "raw_output": "",
        "exit_code": None,
        "error_details": []
    }
    
    try:
        # Check if file exists
        if not dfy_file.exists():
            result["errors"].append(f"File not found: {dfy_file}")
            return result
        
        # Run Dafny verification
        start_time = datetime.now()
        
        # Try multiple Dafny commands (different versions/installations)
        dafny_commands = [
            ["dafny", "verify", str(dfy_file)],
            ["dafny", "/compile:0", str(dfy_file)],  # Older Dafny syntax
            ["Dafny.exe", "verify", str(dfy_file)],  # Windows executable
            ["Dafny.exe", "/compile:0", str(dfy_file)]  # Windows executable, older syntax
        ]
        
        process_result = None
        used_command = None
        
        for cmd in dafny_commands:
            try:
                process_result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
                used_command = ' '.join(cmd)
                break  # Success, use this command
            except FileNotFoundError:
                continue  # Try next command
            except subprocess.TimeoutExpired:
                result["errors"].append(f"Timeout after {timeout} seconds")
                result["exit_code"] = "TIMEOUT"
                return result
        
        if process_result is None:
            result["errors"].append("Dafny not found. Please ensure Dafny is installed and in PATH.")
            return result
        
        end_time = datetime.now()
        result["verification_time"] = (end_time - start_time).total_seconds()
        result["exit_code"] = process_result.returncode
        result["raw_output"] = process_result.stdout + process_result.stderr
        result["success"] = True
        
        # Parse Dafny output for detailed error analysis
        stdout = process_result.stdout
        stderr = process_result.stderr
        combined_output = result["raw_output"]
        
        # Check for verification success
        if process_result.returncode == 0:
            if "verified" in combined_output.lower() or "0 errors" in combined_output:
                result["verified"] = True
                result["compilation_success"] = True
        
        # Parse different types of errors
        lines = combined_output.split('\n')
        
        for line_num, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
                
            # Parse errors with line numbers and detailed information
            error_patterns = [
                (r'(.+?)\((\d+),(\d+)\):\s*Error:\s*(.+)', 'parse_error'),
                (r'(.+?)\((\d+),(\d+)\):\s*(.+?error.+)', 'general_error'),
                (r'Error:\s*(.+)', 'generic_error'),
                (r'(.+?)\((\d+),(\d+)\):\s*Warning:\s*(.+)', 'warning'),
                (r'Warning:\s*(.+)', 'generic_warning'),
            ]
            
            for pattern, error_type in error_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if error_type == 'parse_error':
                        file_path, line_no, col_no, message = match.groups()
                        error_detail = {
                            "type": "parse_error",
                            "file": file_path,
                            "line": int(line_no),
                            "column": int(col_no),
                            "message": message.strip(),
                            "raw_line": line_clean
                        }
                        result["parse_errors"].append(error_detail)
                        result["error_details"].append(error_detail)
                        
                    elif error_type == 'general_error':
                        file_path, line_no, col_no, message = match.groups()
                        error_detail = {
                            "type": "verification_error",
                            "file": file_path,
                            "line": int(line_no),
                            "column": int(col_no),
                            "message": message.strip(),
                            "raw_line": line_clean
                        }
                        result["verification_errors"].append(error_detail)
                        result["error_details"].append(error_detail)
                        
                    elif error_type == 'generic_error':
                        message = match.group(1)
                        error_detail = {
                            "type": "generic_error",
                            "message": message.strip(),
                            "raw_line": line_clean
                        }
                        result["errors"].append(message.strip())
                        result["error_details"].append(error_detail)
                        
                    elif error_type == 'warning':
                        file_path, line_no, col_no, message = match.groups()
                        warning_detail = {
                            "type": "warning",
                            "file": file_path,
                            "line": int(line_no),
                            "column": int(col_no),
                            "message": message.strip(),
                            "raw_line": line_clean
                        }
                        result["warnings"].append(warning_detail)
                        
                    elif error_type == 'generic_warning':
                        message = match.group(1)
                        result["warnings"].append({
                            "type": "generic_warning",
                            "message": message.strip(),
                            "raw_line": line_clean
                        })
                    break
            
            # Look for specific error types
            if "parse errors detected" in line_clean.lower():
                parse_error_match = re.search(r'(\d+)\s+parse\s+errors?\s+detected', line_clean, re.IGNORECASE)
                if parse_error_match:
                    error_count = int(parse_error_match.group(1))
                    result["errors"].append(f"{error_count} parse errors detected")
            
            if "verification errors" in line_clean.lower():
                verif_error_match = re.search(r'(\d+)\s+verification\s+errors?', line_clean, re.IGNORECASE)
                if verif_error_match:
                    error_count = int(verif_error_match.group(1))
                    result["errors"].append(f"{error_count} verification errors")
        
        # Determine compilation success
        if result["parse_errors"]:
            result["compilation_success"] = False
        elif process_result.returncode == 0 or "program parsed successfully" in combined_output.lower():
            result["compilation_success"] = True
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Exception during verification: {str(e)}")
        result["error_details"].append({
            "type": "exception",
            "message": str(e),
            "raw_line": f"Exception: {str(e)}"
        })
        return result

def process_specification_file(spec_file: Path, output_dir: Path, timeout: int = 60, limit: Optional[int] = None) -> List[Dict]:
    """
    Process a JSON specification file, convert to Dafny programs, and verify them.
    
    Args:
        spec_file: Path to the JSON specification file
        output_dir: Directory to save .dfy files
        timeout: Timeout for each verification
        limit: Optional limit on number of specifications to process
        
    Returns:
        List of verification results
    """
    results = []
    
    try:
        print(f"\n📄 Processing specification file: {spec_file}")
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct list of specifications
            specifications = data
        elif isinstance(data, dict):
            # Check for common field names containing specifications
            if "specifications" in data:
                specifications = data["specifications"]
            elif "programs" in data:
                specifications = data["programs"]
            elif "data" in data:
                specifications = data["data"]
            else:
                print(f"❌ Could not find specifications in {spec_file}")
                print(f"   Available keys: {list(data.keys())}")
                return []
        else:
            print(f"❌ Expected list or dict of specifications in {spec_file}")
            return []
        
        if not isinstance(specifications, list):
            print(f"❌ Specifications should be a list in {spec_file}")
            return []
        
        print(f"📊 Found {len(specifications)} specifications")
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            specifications = specifications[:limit]
            print(f"🔢 Limited to first {len(specifications)} specifications")
        
        # Create output directory for this specification file
        spec_name = spec_file.stem
        
        # Add timestamp to avoid overwriting existing directories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        spec_output_dir = output_dir / f"{spec_name}_{timestamp}"
        spec_output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, spec in enumerate(specifications, 1):
            print(f"\n📁 [{i}/{len(specifications)}] Processing specification {i}")
            
            # Extract specification text
            spec_text = ""
            if isinstance(spec, dict):
                # Look for Dafny specification keys first
                for key in ["program_specification", "dafny_specification", "specification", "content", "code", "program"]:
                    if key in spec:
                        spec_text = spec[key]
                        break
                
                # Also check for nested structures
                if not spec_text and "result" in spec:
                    result = spec["result"]
                    if isinstance(result, dict):
                        for key in ["program_specification", "dafny_specification", "specification", "content"]:
                            if key in result:
                                spec_text = result[key]
                                break
                    elif isinstance(result, str):
                        spec_text = result
            elif isinstance(spec, str):
                spec_text = spec
            
            if not spec_text:
                print(f"    ❌ No specification text found in item {i}")
                continue
            
            # Extract Dafny code
            dafny_code = extract_dafny_code(spec_text)
            if not dafny_code:
                print(f"    ❌ No Dafny code found in specification {i}")
                continue
            
            # Save to .dfy file
            dfy_filename = f"program_{i:03d}.dfy"
            dfy_path = spec_output_dir / dfy_filename
            
            if save_dafny_program(dafny_code, dfy_path):
                print(f"    💾 Saved: {dfy_filename}")
                
                # Verify the program
                verify_result = verify_dafny_program(dfy_path, timeout)
                
                # Add metadata
                verify_result.update({
                    "source_file": str(spec_file),
                    "specification_index": i,
                    "relative_path": str(dfy_path.relative_to(output_dir)),
                    "file_size": dfy_path.stat().st_size,
                    "original_spec": spec_text[:200] + "..." if len(spec_text) > 200 else spec_text
                })
                
                results.append(verify_result)
                
                # Print verification status
                if verify_result["verified"]:
                    print(f"    ✅ Verified successfully ({verify_result['verification_time']:.2f}s)")
                elif verify_result["compilation_success"]:
                    print(f"    ⚠️  Compiled but not verified ({verify_result['verification_time']:.2f}s)")
                else:
                    print(f"    ❌ Verification failed ({verify_result['verification_time']:.2f}s)")
                    if verify_result["parse_errors"]:
                        print(f"        🔴 Parse errors: {len(verify_result['parse_errors'])}")
            else:
                print(f"    ❌ Failed to save {dfy_filename}")
    
    except Exception as e:
        print(f"❌ Error processing {spec_file}: {e}")
    
    return results

def process_dafny_files(input_path: Path, timeout: int = 60) -> List[Dict]:
    """
    Process Dafny files from a directory or single file and verify them.
    
    Args:
        input_path: Path to .dfy file or directory containing .dfy files
        timeout: Timeout for each verification
        
    Returns:
        List of verification results
    """
    results = []
    dfy_files = []
    
    if input_path.is_file() and input_path.suffix == '.dfy':
        dfy_files = [input_path]
    elif input_path.is_dir():
        # Find all .dfy files recursively
        dfy_files = list(input_path.rglob("*.dfy"))
    else:
        print(f"❌ Invalid input path: {input_path}")
        return []
    
    if not dfy_files:
        print(f"❌ No .dfy files found in {input_path}")
        return []
    
    print(f"🔍 Found {len(dfy_files)} Dafny files to verify")
    
    for i, dfy_file in enumerate(dfy_files, 1):
        print(f"\n📁 [{i}/{len(dfy_files)}] Verifying: {dfy_file.name}")
        print(f"    📍 Path: {dfy_file}")
        
        # Verify the program
        verify_result = verify_dafny_program(dfy_file, timeout)
        
        # Add metadata
        verify_result.update({
            "relative_path": str(dfy_file.relative_to(input_path.parent)),
            "file_size": dfy_file.stat().st_size if dfy_file.exists() else 0,
            "verification_order": i
        })
        
        results.append(verify_result)
        
        # Print detailed verification status
        if verify_result["verified"]:
            print(f"    ✅ Verified successfully ({verify_result['verification_time']:.2f}s)")
        elif verify_result["compilation_success"]:
            print(f"    ⚠️  Compiled but not verified ({verify_result['verification_time']:.2f}s)")
            if verify_result["verification_errors"]:
                print(f"    🔶 Verification issues: {len(verify_result['verification_errors'])}")
        else:
            print(f"    ❌ Verification failed ({verify_result['verification_time']:.2f}s)")
            if verify_result["parse_errors"]:
                print(f"    🔴 Parse errors: {len(verify_result['parse_errors'])}")
                for error in verify_result["parse_errors"][:2]:  # Show first 2 parse errors
                    print(f"        Line {error.get('line', '?')}: {error.get('message', 'Unknown error')}")
            if verify_result["verification_errors"]:
                print(f"    🔶 Verification errors: {len(verify_result['verification_errors'])}")
                for error in verify_result["verification_errors"][:2]:  # Show first 2 verification errors
                    print(f"        Line {error.get('line', '?')}: {error.get('message', 'Unknown error')}")
            if verify_result["errors"]:
                for error in verify_result["errors"][:2]:  # Show first 2 generic errors
                    print(f"        🔴 {error}")
    
    return results
    """
    Process Dafny files from a directory or single file and verify them.
    
    Args:
        input_path: Path to .dfy file or directory containing .dfy files
        timeout: Timeout for each verification
        
    Returns:
        List of verification results
    """
    results = []
    dfy_files = []
    
    if input_path.is_file() and input_path.suffix == '.dfy':
        dfy_files = [input_path]
    elif input_path.is_dir():
        # Find all .dfy files recursively
        dfy_files = list(input_path.rglob("*.dfy"))
    else:
        print(f"❌ Invalid input path: {input_path}")
        return []
    
    if not dfy_files:
        print(f"❌ No .dfy files found in {input_path}")
        return []
    
    print(f"🔍 Found {len(dfy_files)} Dafny files to verify")
    
    for i, dfy_file in enumerate(dfy_files, 1):
        print(f"\n📁 [{i}/{len(dfy_files)}] Verifying: {dfy_file.name}")
        print(f"    📍 Path: {dfy_file}")
        
        # Verify the program
        verify_result = verify_dafny_program(dfy_file, timeout)
        
        # Add metadata
        verify_result.update({
            "relative_path": str(dfy_file.relative_to(input_path.parent)),
            "file_size": dfy_file.stat().st_size if dfy_file.exists() else 0,
            "verification_order": i
        })
        
        results.append(verify_result)
        
        # Print detailed verification status
        if verify_result["verified"]:
            print(f"    ✅ Verified successfully ({verify_result['verification_time']:.2f}s)")
        elif verify_result["compilation_success"]:
            print(f"    ⚠️  Compiled but not verified ({verify_result['verification_time']:.2f}s)")
            if verify_result["verification_errors"]:
                print(f"    🔶 Verification issues: {len(verify_result['verification_errors'])}")
        else:
            print(f"    ❌ Verification failed ({verify_result['verification_time']:.2f}s)")
            if verify_result["parse_errors"]:
                print(f"    🔴 Parse errors: {len(verify_result['parse_errors'])}")
                for error in verify_result["parse_errors"][:2]:  # Show first 2 parse errors
                    print(f"        Line {error.get('line', '?')}: {error.get('message', 'Unknown error')}")
            if verify_result["verification_errors"]:
                print(f"    🔶 Verification errors: {len(verify_result['verification_errors'])}")
                for error in verify_result["verification_errors"][:2]:  # Show first 2 verification errors
                    print(f"        Line {error.get('line', '?')}: {error.get('message', 'Unknown error')}")
            if verify_result["errors"]:
                for error in verify_result["errors"][:2]:  # Show first 2 generic errors
                    print(f"        🔴 {error}")
    
    return results

def save_verification_results(results: List[Dict], output_file: Path):
    """Save verification results to JSON file with detailed summary statistics."""
    
    # Calculate summary statistics
    total = len(results)
    verified = sum(1 for r in results if r.get("verified", False))
    compiled = sum(1 for r in results if r.get("compilation_success", False))
    failed = total - compiled
    parse_errors = sum(1 for r in results if r.get("parse_errors"))
    verification_errors = sum(1 for r in results if r.get("verification_errors"))
    
    # Calculate average verification time
    avg_time = sum(r.get("verification_time", 0) for r in results) / total if total > 0 else 0
    
    summary = {
        "total_programs": total,
        "verified_count": verified,
        "compiled_count": compiled,
        "failed_count": failed,
        "parse_error_count": parse_errors,
        "verification_error_count": verification_errors,
        "verification_rate": verified / total if total > 0 else 0,
        "compilation_rate": compiled / total if total > 0 else 0,
        "average_verification_time": avg_time,
        "generated_at": datetime.now().isoformat()
    }
    
    # Error analysis
    error_analysis = {
        "common_parse_errors": {},
        "common_verification_errors": {},
        "error_patterns": {}
    }
    
    # Analyze common error patterns
    for result in results:
        for error in result.get("parse_errors", []):
            msg = error.get("message", "Unknown")
            error_analysis["common_parse_errors"][msg] = error_analysis["common_parse_errors"].get(msg, 0) + 1
        
        for error in result.get("verification_errors", []):
            msg = error.get("message", "Unknown")
            error_analysis["common_verification_errors"][msg] = error_analysis["common_verification_errors"].get(msg, 0) + 1
    
    # Sort by frequency
    error_analysis["common_parse_errors"] = dict(sorted(
        error_analysis["common_parse_errors"].items(), 
        key=lambda x: x[1], reverse=True
    ))
    error_analysis["common_verification_errors"] = dict(sorted(
        error_analysis["common_verification_errors"].items(), 
        key=lambda x: x[1], reverse=True
    ))
    
    output_data = {
        "summary": summary,
        "error_analysis": error_analysis,
        "results": results
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 VERIFICATION SUMMARY:")
    print(f"  Total programs: {total}")
    print(f"  Verified: {verified} ({verified/total*100:.1f}%)")
    print(f"  Compiled: {compiled} ({compiled/total*100:.1f}%)")
    print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"  Parse errors: {parse_errors}")
    print(f"  Verification errors: {verification_errors}")
    print(f"  Average time: {avg_time:.2f}s")
    
    if error_analysis["common_parse_errors"]:
        print(f"\n� MOST COMMON PARSE ERRORS:")
        for error, count in list(error_analysis["common_parse_errors"].items())[:5]:
            print(f"  [{count}x] {error}")
    
    if error_analysis["common_verification_errors"]:
        print(f"\n🔶 MOST COMMON VERIFICATION ERRORS:")
        for error, count in list(error_analysis["common_verification_errors"].items())[:5]:
            print(f"  [{count}x] {error}")
    
    print(f"\n💾 Detailed results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Verify Dafny programs from JSON specifications or existing .dfy files")
    parser.add_argument("input", nargs="?",
                        help="JSON specification file, .dfy file, or directory path")
    parser.add_argument("--mode", choices=["json", "dfy", "auto"], default="auto",
                        help="Verification mode: 'json' for specifications, 'dfy' for existing files, 'auto' to detect")
    parser.add_argument("--output-dir", default="data/verification/programs",
                        help="Directory to save .dfy files (for JSON mode)")
    parser.add_argument("--results-file", 
                        help="File to save verification results (default: auto-generated with timestamp)")
    parser.add_argument("--timeout", type=int, default=60,
                        help="Timeout in seconds for each verification")
    parser.add_argument("--filter", 
                        help="Filter files by pattern (e.g., '*remove_docstrings*')")
    parser.add_argument("--list-specs", action="store_true",
                        help="List available JSON specification files")
    parser.add_argument("--no-timestamp", action="store_true",
                        help="Don't add timestamp to output filename")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of specifications to verify (for testing)")
    
    args = parser.parse_args()
    
    # List available specification files if requested
    if args.list_specs:
        print("📄 Available JSON specification files:")
        spec_dir = Path("output/specification")
        if spec_dir.exists():
            spec_files = list(spec_dir.glob("*.json"))
            for spec_file in sorted(spec_files):
                print(f"  📁 {spec_file.name}")
                try:
                    with open(spec_file, 'r') as f:
                        data = json.load(f)
                        count = len(data) if isinstance(data, list) else 1
                        print(f"      📊 {count} specifications")
                except:
                    print(f"      ❌ Error reading file")
        else:
            print("❌ No specification directory found")
        return
    
    # Determine input path and mode
    if args.input:
        input_path = Path(args.input)
    else:
        # Default paths based on mode
        if args.mode == "json":
            input_path = Path("output/specification")
        else:
            input_path = Path("data/verification/programs")
    
    # Auto-detect mode if not specified
    mode = args.mode
    if mode == "auto":
        if input_path.is_file():
            if input_path.suffix == ".json":
                mode = "json"
            elif input_path.suffix == ".dfy":
                mode = "dfy"
            else:
                print(f"❌ Unknown file type: {input_path.suffix}")
                return
        elif input_path.is_dir():
            # Check what's in the directory
            json_files = list(input_path.glob("*.json"))
            dfy_files = list(input_path.glob("*.dfy"))
            
            if json_files and not dfy_files:
                mode = "json"
            elif dfy_files and not json_files:
                mode = "dfy"
            elif json_files and dfy_files:
                print("🤔 Directory contains both JSON and .dfy files")
                print(f"   📄 {len(json_files)} JSON files")
                print(f"   📁 {len(dfy_files)} .dfy files")
                print("💡 Use --mode to specify which to process")
                return
            else:
                print(f"❌ No JSON or .dfy files found in {input_path}")
                return
    
    if not input_path.exists():
        print(f"❌ Input path not found: {input_path}")
        if mode == "json":
            print("💡 Available JSON specification files:")
            spec_dir = Path("output/specification")
            if spec_dir.exists():
                for f in spec_dir.glob("*.json"):
                    print(f"  📄 {f}")
        else:
            print("💡 Available .dfy directories:")
            for p in Path(".").rglob("*"):
                if p.is_dir() and any(p.glob("*.dfy")):
                    print(f"  📁 {p}")
        return
    
    print(f"🎯 Mode: {mode.upper()}")
    print(f"📍 Input: {input_path}")
    
    if args.filter:
        print(f"🔍 Filter: {args.filter}")
    
    # Process based on mode
    all_results = []
    
    if mode == "json":
        # JSON specification mode
        output_dir = Path(args.output_dir)
        
        if input_path.is_file():
            # Single JSON file
            all_results = process_specification_file(input_path, output_dir, args.timeout, args.limit)
        else:
            # Directory with JSON files
            json_files = list(input_path.glob("*.json"))
            if not json_files:
                print(f"❌ No JSON files found in {input_path}")
                return
            
            print(f"📄 Found {len(json_files)} JSON specification files")
            
            for spec_file in json_files:
                results = process_specification_file(spec_file, output_dir, args.timeout, args.limit)
                all_results.extend(results)
    
    elif mode == "dfy":
        # Direct .dfy file mode
        all_results = process_dafny_files(input_path, args.timeout)
    
    # Apply filter if specified
    if args.filter and all_results:
        original_count = len(all_results)
        filtered_results = []
        filter_pattern = args.filter.replace("*", "")
        
        for result in all_results:
            file_path = result.get("file", "")
            relative_path = result.get("relative_path", "")
            source_file = result.get("source_file", "")
            
            if (filter_pattern in file_path or 
                filter_pattern in relative_path or 
                filter_pattern in source_file):
                filtered_results.append(result)
        
        print(f"🔍 Filtered from {original_count} to {len(filtered_results)} files matching '{args.filter}'")
        all_results = filtered_results
    
    if not all_results:
        print("❌ No programs to verify!")
        return
    
    # Generate output filename with timestamp and mode info
    if args.results_file:
        results_file = Path(args.results_file)
    else:
        # Auto-generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if not args.no_timestamp else ""
        
        if mode == "json":
            # Include source file info for JSON mode
            if input_path.is_file():
                source_name = input_path.stem
            else:
                source_name = "multiple_specs"
            
            if timestamp:
                filename = f"verification_{mode}_{source_name}_{timestamp}.json"
            else:
                filename = f"verification_{mode}_{source_name}.json"
        else:
            # For .dfy mode, include directory info
            if input_path.is_file():
                source_name = input_path.parent.name
            else:
                source_name = input_path.name
            
            if timestamp:
                filename = f"verification_{mode}_{source_name}_{timestamp}.json"
            else:
                filename = f"verification_{mode}_{source_name}.json"
        
        results_file = Path("output") / filename
    
    # Save results
    save_verification_results(all_results, results_file)
    
    print(f"\n✅ Verification complete!")
    if mode == "json":
        print(f"📁 Dafny files saved to: {args.output_dir}")
    print(f"📊 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
