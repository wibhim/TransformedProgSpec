"""
Reporter module for generating verification reports.
"""

import os
import json
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime

from config.settings import CONFIG

def generate_html_report(results: List[Dict[str, Any]], output_dir: str) -> str:
    """
    Generate an HTML report from verification results.
    
    Args:
        results: List of verification results
        output_dir: Directory to save the report
    
    Returns:
        Path to the generated report
    """
    # Count successes and failures
    success_count = sum(1 for r in results if r.get("success", False))
    failure_count = len(results) - success_count
    success_rate = (success_count / len(results)) * 100 if results else 0
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dafny Verification Report</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Dafny Verification Report</h1>
        <p class="timestamp">Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Total Programs:</span>
                    <span class="stat-value">{len(results)}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Successful:</span>
                    <span class="stat-value success">{success_count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Failed:</span>
                    <span class="stat-value failure">{failure_count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Success Rate:</span>
                    <span class="stat-value">{success_rate:.1f}%</span>
                </div>
            </div>
        </div>
        
        <div class="results">
            <h2>Individual Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Program</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add rows for each result
    for result in results:
        file_name = os.path.basename(result.get("file_path", "Unknown"))
        success = result.get("success", False)
        duration = f"{result.get('duration', 0):.2f}s"
        status_class = "success" if success else "failure"
        status_text = "Success" if success else "Failed"
        
        html_content += f"""
                    <tr>
                        <td>{file_name}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{duration}</td>
                        <td><a href="individual/{file_name}.html">Details</a></td>
                    </tr>
"""
    
    # Close the HTML
    html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    
    # Create CSS file
    css_content = """
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

h1, h2 {
    color: #2c3e50;
}

.timestamp {
    color: #7f8c8d;
    margin-bottom: 20px;
}

.summary {
    background-color: #ecf0f1;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.stats {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}

.stat {
    padding: 10px;
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    flex: 1;
    min-width: 150px;
}

.stat-label {
    font-weight: bold;
    display: block;
}

.stat-value {
    font-size: 1.5em;
    display: block;
}

.success {
    color: #27ae60;
}

.failure {
    color: #e74c3c;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th, td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background-color: #2c3e50;
    color: #fff;
}

tr:hover {
    background-color: #f5f5f5;
}

a {
    color: #3498db;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
"""
    
    # Save the HTML report
    report_path = os.path.join(output_dir, "index.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Save the CSS file
    css_path = os.path.join(output_dir, "style.css")
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    # Create individual reports
    individual_dir = os.path.join(output_dir, "individual")
    os.makedirs(individual_dir, exist_ok=True)
    
    # Generate individual reports
    for result in results:
        file_name = os.path.basename(result.get("file_path", "Unknown"))
        individual_path = os.path.join(individual_dir, f"{file_name}.html")
        
        # Create individual report
        with open(individual_path, 'w', encoding='utf-8') as f:
            f.write(generate_individual_report(result))
    
    return report_path

def generate_individual_report(result: Dict[str, Any]) -> str:
    """Generate an individual HTML report for a single verification result."""
    file_name = os.path.basename(result.get("file_path", "Unknown"))
    success = result.get("success", False)
    duration = f"{result.get('duration', 0):.2f}s"
    status_class = "success" if success else "failure"
    status_text = "Success" if success else "Failed"
    output = result.get("output", "").replace("\n", "<br>")
    error = result.get("error", "").replace("\n", "<br>")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Details: {file_name}</title>
    <link rel="stylesheet" href="../style.css">
    <style>
        .output-box {{
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
            overflow-x: auto;
        }}
        .error-box {{
            background-color: #fff3f3;
            border: 1px solid #e74c3c;
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Verification Details: {file_name}</h1>
        <p><a href="../index.html">← Back to Summary</a></p>
        
        <div class="summary">
            <h2>Result Summary</h2>
            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value {status_class}">{status_text}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Duration:</span>
                    <span class="stat-value">{duration}</span>
                </div>
            </div>
        </div>
        
        <div class="details">
            <h2>Output</h2>
            <div class="output-box">
                {output}
            </div>
            
            {f'<h2>Errors</h2><div class="output-box error-box">{error}</div>' if error else ''}
        </div>
    </div>
</body>
</html>
"""
    return html_content

def generate_summary_text(results: List[Dict[str, Any]]) -> str:
    """Generate a plain text summary of verification results."""
    success_count = sum(1 for r in results if r.get("success", False))
    failure_count = len(results) - success_count
    success_rate = (success_count / len(results)) * 100 if results else 0
    
    summary = f"""
Dafny Verification Summary
=========================
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Summary:
  - Total Programs: {len(results)}
  - Successful: {success_count}
  - Failed: {failure_count}
  - Success Rate: {success_rate:.1f}%

Individual Results:
"""
    
    for result in results:
        file_name = os.path.basename(result.get("file_path", "Unknown"))
        success = result.get("success", False)
        duration = f"{result.get('duration', 0):.2f}s"
        status_text = "✓ Success" if success else "✗ Failed"
        
        summary += f"  - {file_name}: {status_text} ({duration})\n"
    
    return summary

def main():
    """Generate reports from verification results."""
    print("Generating verification reports...")
    
    input_file = CONFIG["report"]["input_json"]
    output_dir = CONFIG["report"]["output_dir"]
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read verification results
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Generate HTML report
        report_path = generate_html_report(results, output_dir)
        
        # Generate text summary
        summary_text = generate_summary_text(results)
        summary_path = os.path.join(output_dir, "dafny_verification_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        print(f"Generated HTML report: {report_path}")
        print(f"Generated summary text: {summary_path}")
        
    except FileNotFoundError:
        print(f"Error: Results file not found at {input_file}")
    except json.JSONDecodeError:
        print(f"Error: Could not parse {input_file} as JSON")
    except Exception as e:
        print(f"Error generating reports: {str(e)}")

if __name__ == "__main__":
    main()
