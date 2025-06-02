import json
import re
import os
from datetime import datetime
from config import CONFIG

# === CONFIG ===
REPORT_CONFIG = CONFIG["report"]
INPUT_JSON = REPORT_CONFIG["input_json"]
OUTPUT_FOLDER = REPORT_CONFIG["output_dir"]
OUTPUT_HTML = f"{OUTPUT_FOLDER}/dafny_verification_report.html"
OUTPUT_TXT = f"{OUTPUT_FOLDER}/dafny_verification_summary.txt"

def parse_dafny_output(output):
    """Parse Dafny output into structured format with errors and warnings."""
    result = {
        "errors": [],
        "warnings": [],
        "verification_status": "",
        "parse_errors": 0
    }
    
    # Extract verification status
    status_match = re.search(r"Dafny program verifier finished with (\d+) verified, (\d+) error", output)
    if status_match:
        verified = int(status_match.group(1))
        errors = int(status_match.group(2))
        result["verification_status"] = f"{verified} verified, {errors} errors"
    
    # Extract parse error count
    parse_errors_match = re.search(r"(\d+) parse errors detected", output)
    if parse_errors_match:
        result["parse_errors"] = int(parse_errors_match.group(1))
    
    # Extract errors
    error_pattern = r"(.*?)\((\d+),(\d+)\): Error: (.*?)(?=\n\s+\||\n\n|\Z)"
    for match in re.finditer(error_pattern, output, re.DOTALL):
        file_path, line, col, message = match.groups()
        result["errors"].append({
            "file": os.path.basename(file_path),
            "line": int(line),
            "column": int(col),
            "message": message.strip()
        })
    
    # Extract warnings
    warning_pattern = r"(.*?)\((\d+),(\d+)\): Warning: (.*?)(?=\n\s+\||\n\n|\Z)"
    for match in re.finditer(warning_pattern, output, re.DOTALL):
        file_path, line, col, message = match.groups()
        result["warnings"].append({
            "file": os.path.basename(file_path),
            "line": int(line),
            "column": int(col),
            "message": message.strip()
        })
    
    return result

def generate_html_report(results):
    """Generate an HTML report from the parsed results."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dafny Verification Report</title>
        <link rel="stylesheet" type="text/css" href="style.css">
    </head>
    <body>
        <h1>Dafny Verification Report</h1>
        <div class="summary">
            <p><strong>Total files processed:</strong> {total_files}</p>
            <p><strong>Files verified successfully:</strong> {verified_files}</p>
            <p><strong>Files with verification errors:</strong> {error_files}</p>
        </div>
    """.format(
        total_files=len(results),
        verified_files=sum(1 for item in results if item["verified"]),
        error_files=sum(1 for item in results if not item["verified"])
    )
    
    for item in results:
        file_path = item["file_path"]
        verified = item["verified"]
        parsed = parse_dafny_output(item["dafny_output"])
        
        html += f"""
        <div class="file-item">
            <div class="file-header">
                <div class="file-name">{file_path}</div>
                <div class="verification-status {'verified' if verified else 'not-verified'}">
                    {'✅ Verified' if verified else '❌ Not Verified'}
                </div>
            </div>
        """
        
        # Verification status
        if parsed["verification_status"]:
            html += f"<p><strong>Verification status:</strong> {parsed['verification_status']}</p>"
        if parsed["parse_errors"] > 0:
            html += f"<p><strong>Parse errors:</strong> {parsed['parse_errors']}</p>"
        
        # Errors
        if parsed["errors"]:
            html += "<div class='error-list'><h3>Errors</h3>"
            for error in parsed["errors"]:
                html += f"""
                <div class="error-item">
                    <div class="location">Line {error['line']}, Column {error['column']}</div>
                    <div class="message">{error['message']}</div>
                </div>
                """
            html += "</div>"
        
        # Warnings
        if parsed["warnings"]:
            html += "<div class='warning-list'><h3>Warnings</h3>"
            for warning in parsed["warnings"]:
                html += f"""
                <div class="warning-item">
                    <div class="location">Line {warning['line']}, Column {warning['column']}</div>
                    <div class="message">{warning['message']}</div>
                </div>
                """
            html += "</div>"
        
        html += "</div>"
    
    html += f"""
        <div class="timestamp">Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </body>
    </html>
    """
    
    return html

def generate_text_summary(results):
    """Generate a plain text summary of the verification results."""
    summary = "Dafny Verification Summary\n"
    summary += "=" * 30 + "\n\n"
    summary += f"Total files processed: {len(results)}\n"
    summary += f"Files verified successfully: {sum(1 for item in results if item['verified'])}\n"
    summary += f"Files with verification errors: {sum(1 for item in results if not item['verified'])}\n\n"
    
    for item in results:
        file_path = item["file_path"]
        verified = item["verified"]
        parsed = parse_dafny_output(item["dafny_output"])
        
        summary += f"\n{'-' * 50}\n"
        summary += f"File: {file_path}\n"
        summary += f"Status: {'✅ Verified' if verified else '❌ Not Verified'}\n"
        
        if parsed["verification_status"]:
            summary += f"Verification details: {parsed['verification_status']}\n"
        if parsed["parse_errors"] > 0:
            summary += f"Parse errors: {parsed['parse_errors']}\n"
        
        # Errors
        if parsed["errors"]:
            summary += "\nERRORS:\n"
            for error in parsed["errors"]:
                summary += f"  Line {error['line']}, Col {error['column']}: {error['message']}\n"
        
        # Warnings
        if parsed["warnings"]:
            summary += "\nWARNINGS:\n"
            for warning in parsed["warnings"]:
                summary += f"  Line {warning['line']}, Col {warning['column']}: {warning['message']}\n"
    
    summary += f"\n{'-' * 50}\n"
    summary += f"\nReport generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return summary

def create_individual_report(item):
    """Create an individual HTML report for a single file."""
    file_path = item["file_path"]
    verified = item["verified"]
    parsed = parse_dafny_output(item["dafny_output"])
    
    # Create filename from the original file path
    safe_name = os.path.basename(file_path).replace(".", "_")
    output_file = f"{OUTPUT_FOLDER}/individual/{safe_name}_report.html"
    
    # Simplified HTML with minimal styling
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dafny Verification: {file_path}</title>
        <link rel="stylesheet" href="../style.css">
    </head>
    <body>
        <h1>Dafny Verification: {file_path}</h1>
        
        <div class="{'verified' if verified else 'not-verified'}">
            {'✅ Verified' if verified else '❌ Not Verified'}
        </div>
    """
    
    # Verification status
    if parsed["verification_status"]:
        html += f"<p><strong>Verification status:</strong> {parsed['verification_status']}</p>"
    if parsed["parse_errors"] > 0:
        html += f"<p><strong>Parse errors:</strong> {parsed['parse_errors']}</p>"
    
    # Errors
    if parsed["errors"]:
        html += "<div class='error-list'><h3>Errors</h3>"
        for error in parsed["errors"]:
            html += f"""
            <div class="error-item">
                <div class="location">Line {error['line']}, Column {error['column']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        html += "</div>"
    
    # Warnings
    if parsed["warnings"]:
        html += "<div class='warning-list'><h3>Warnings</h3>"
        for warning in parsed["warnings"]:
            html += f"""
            <div class="warning-item">
                <div class="location">Line {warning['line']}, Column {warning['column']}</div>
                <div class="message">{warning['message']}</div>
            </div>
            """
        html += "</div>"
    
    # Full output
    html += """
    <h3>Full Dafny Output</h3>
    <div class="dafny-output">
    """
    html += item["dafny_output"].replace("\n", "<br>").replace(" ", "&nbsp;")
    html += """
    </div>
    """
    
    html += f"""
        <div class="timestamp">Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </body>
    </html>
    """
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    return os.path.basename(output_file)

def main():
    # Create output directories
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(f"{OUTPUT_FOLDER}/individual", exist_ok=True)
    
    # Create CSS file
    css_content = """
    body {font-family: Arial, sans-serif; margin: 20px;}
    h1 {color: #2c3e50;}
    .summary {margin: 20px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px;}
    .verified {color: green;}
    .not-verified {color: red;}
    .error-item {background-color: #ffdddd; padding: 10px; margin: 5px 0;}
    .warning-item {background-color: #ffffdd; padding: 10px; margin: 5px 0;}
    .dafny-output {
        background-color: #f0f0f0; 
        padding: 10px; 
        font-family: monospace; 
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }
    """
    
    with open(f"{OUTPUT_FOLDER}/style.css", "w", encoding="utf-8") as f:
        f.write(css_content)
        
    # Load verification results
    try:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            results = json.load(f)
        
        print(f"Loaded {len(results)} verification results from {INPUT_JSON}")
        
        # Generate HTML report
        html_content = generate_html_report(results)
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report saved to {OUTPUT_HTML}")
        
        # Generate text summary
        text_summary = generate_text_summary(results)
        with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
            f.write(text_summary)
        print(f"Text summary saved to {OUTPUT_TXT}")
        
        # Generate individual reports
        individual_files = []
        for item in results:
            report_file = create_individual_report(item)
            individual_files.append({
                "file": item["file_path"],
                "report": report_file,
                "verified": item["verified"]
            })
        
        # Create an index for individual reports
        index_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dafny Verification Reports</title>
            <link rel="stylesheet" type="text/css" href="style.css">
        </head>
        <body>
            <h1>Dafny Verification Reports</h1>
            <p><a href="dafny_verification_report.html">View Overall Summary Report</a></p>
            <table>
                <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Report</th>
                </tr>
        """
        
        for item in individual_files:
            index_html += f"""
            <tr>
                <td>{item['file']}</td>
                <td class="{'verified' if item['verified'] else 'not-verified'}">
                    {'✅ Verified' if item['verified'] else '❌ Not Verified'}
                </td>
                <td><a href="individual/{item['report']}">View Report</a></td>
            </tr>
            """
        
        index_html += f"""
            </table>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        with open(f"{OUTPUT_FOLDER}/index.html", "w", encoding="utf-8") as f:
            f.write(index_html)
        print(f"Index of reports saved to {OUTPUT_FOLDER}/index.html")
        
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_JSON}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not parse '{INPUT_JSON}' as JSON.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()