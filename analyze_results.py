#!/usr/bin/env python
"""
Entry point for results analysis functionality.
Analyzes verification results and generates statistics and visualizations.

Usage:
    python analyze_results.py [--specs FILE] [--results FILE] [--output DIR]
"""
import os
import sys
import argparse
import json
from typing import Dict, List, Any

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import settings
try:
    from config.settings import CONFIG
    OUTPUT_DIR = CONFIG.get("OUTPUT_DIR", "output")
except (ImportError, KeyError):
    OUTPUT_DIR = "output"

# Import visualization module if available
try:
    from src.utils.visualization import generate_visualizations
    has_visualization = True
except ImportError:
    has_visualization = False
    def generate_visualizations(*args, **kwargs):
        print("Visualization module not available.")

def analyze_verification_results(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze verification results and generate statistics.
    
    Args:
        results_data: The verification results data
        
    Returns:
        Dictionary containing analysis results and statistics
    """
    summary = results_data.get("summary", {})
    details = results_data.get("details", [])
    
    # Calculate statistics
    total = summary.get("total", 0)
    successful = summary.get("successful", 0)
    failed = summary.get("failed", 0)
    timeout = summary.get("timeout", 0)
    
    # Calculate success rate
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # Categorize failure types
    failure_categories = {}
    for detail in details:
        if detail.get("status") == "failed":
            error_type = detail.get("error_type", "unknown")
            failure_categories[error_type] = failure_categories.get(error_type, 0) + 1
    
    # Calculate average verification time
    verification_times = [d.get("verification_time", 0) for d in details if d.get("verification_time") is not None]
    avg_time = sum(verification_times) / len(verification_times) if verification_times else 0
    
    return {
        "summary": {
            "total": total,
            "successful": successful,
            "failed": failed,
            "timeout": timeout,
            "success_rate": success_rate,
            "avg_verification_time": avg_time
        },
        "failure_categories": failure_categories
    }

def main():
    """Main entry point for results analysis"""
    parser = argparse.ArgumentParser(
        description="Analyze verification results and generate statistics"
    )
    
    parser.add_argument("--specs", "-s", 
                        default=os.path.join(OUTPUT_DIR, "transformed_specifications.json"),
                        help="Input JSON file containing specifications")
    
    parser.add_argument("--results", "-r", 
                        default=os.path.join(OUTPUT_DIR, "dafny_verification_results.json"),
                        help="Input JSON file containing verification results")
    
    parser.add_argument("--output", "-o", 
                        default=os.path.join(OUTPUT_DIR, "verification_reports"),
                        help="Output directory for analysis reports and visualizations")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Load the specifications
    if args.verbose:
        print(f"Loading specifications from: {args.specs}")
    
    try:
        with open(args.specs, 'r', encoding='utf-8') as f:
            specifications = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading specifications file: {e}")
        return 1
    
    # Load the verification results
    if args.verbose:
        print(f"Loading verification results from: {args.results}")
    
    try:
        with open(args.results, 'r', encoding='utf-8') as f:
            verification_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading verification results file: {e}")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Analyze results
    if args.verbose:
        print("Analyzing verification results...")
    
    analysis = analyze_verification_results(verification_results)
    
    # Generate visualizations
    if args.verbose:
        print("Generating visualizations...")
    
    try:
        if has_visualization:
            generate_visualizations(verification_results, analysis, output_dir=args.output)
        else:
            if args.verbose:
                print("Visualization module not available, skipping visualization generation.")
    except Exception as e:
        if args.verbose:
            print(f"Error generating visualizations: {e}")
    
    # Save analysis results
    analysis_file = os.path.join(args.output, "analysis_summary.json")
    
    if args.verbose:
        print(f"Saving analysis results to: {analysis_file}")
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    
    # Generate HTML report if possible
    report_file = os.path.join(args.output, "verification_report.html")
    try:
        # Simple HTML report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Verification Results Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Verification Results Summary</h1>
    
    <div class="summary">
        <h2>Summary Statistics</h2>
        <p>Total specifications: {analysis['summary']['total']}</p>
        <p>Successful verifications: <span class="success">{analysis['summary']['successful']}</span></p>
        <p>Failed verifications: <span class="failure">{analysis['summary']['failed']}</span></p>
        <p>Timeout verifications: {analysis['summary']['timeout']}</p>
        <p>Success rate: <strong>{analysis['summary']['success_rate']:.2f}%</strong></p>
        <p>Average verification time: {analysis['summary']['avg_verification_time']:.2f} seconds</p>
    </div>
    
    <h2>Failure Categories</h2>
    <table>
        <tr>
            <th>Error Type</th>
            <th>Count</th>
        </tr>
        {"".join(f"<tr><td>{error_type}</td><td>{count}</td></tr>" for error_type, count in analysis['failure_categories'].items())}
    </table>
</body>
</html>""")
        
        if args.verbose:
            print(f"HTML report generated: {report_file}")
    except Exception as e:
        if args.verbose:
            print(f"Error generating HTML report: {e}")
    
    # Print summary
    print("\nAnalysis Summary:")
    print(f"- Total specifications: {analysis['summary']['total']}")
    print(f"- Successful verifications: {analysis['summary']['successful']}")
    print(f"- Failed verifications: {analysis['summary']['failed']}")
    print(f"- Timeout verifications: {analysis['summary']['timeout']}")
    print(f"- Success rate: {analysis['summary']['success_rate']:.2f}%")
    print(f"- Average verification time: {analysis['summary']['avg_verification_time']:.2f} seconds")
    
    if analysis['failure_categories']:
        print("\nFailure Categories:")
        for error_type, count in analysis['failure_categories'].items():
            print(f"- {error_type}: {count}")
    
    if args.verbose:
        print(f"Analysis complete. Results saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
