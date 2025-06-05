#!/usr/bin/env python
"""
Analysis tool for comparing specifications across different types.
This script helps analyze and compare specifications generated from
original, transformed, and prompt-engineered programs.
"""

import sqlite3
import os
import sys
import argparse
import json
from tabulate import tabulate
from datetime import datetime
import difflib
from config import CONFIG

# Cache configuration
CACHE_DIR = os.path.join(CONFIG["OUTPUT_DIR"], "cache")
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")

def ensure_cache_exists():
    """Make sure the cache database exists."""
    if not os.path.exists(CACHE_DB):
        print(f"❌ Cache database not found at {CACHE_DB}")
        print("Please set up the cache database first using setup_cache.py")
        return False
    return True

def get_tables():
    """Get list of specification tables in the database."""
    if not ensure_cache_exists():
        return []
        
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get all tables that end with _specifications
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%specifications'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def list_specifications(spec_type=None, limit=10):
    """List specifications in the database."""
    if not ensure_cache_exists():
        return
        
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    if spec_type:
        # Check if the table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{spec_type}_specifications'")
        if not cursor.fetchone():
            print(f"❌ Table '{spec_type}_specifications' not found in the database")
            conn.close()
            return
            
        # Get specifications for the specified type
        cursor.execute(f"SELECT hash, file_path, timestamp FROM {spec_type}_specifications ORDER BY timestamp DESC LIMIT {limit}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No specifications found for type '{spec_type}'")
            conn.close()
            return
            
        print(f"\nSpecifications for {spec_type} programs:")
    else:
        # Get all specification tables
        spec_tables = get_tables()
        
        if not spec_tables:
            print("No specification tables found in the database")
            conn.close()
            return
            
        rows = []
        for table in spec_tables:
            cursor.execute(f"SELECT '{table.replace('_specifications', '')}' as type, hash, file_path, timestamp FROM {table} ORDER BY timestamp DESC LIMIT {limit}")
            rows.extend(cursor.fetchall())
            
        if not rows:
            print("No specifications found in the database")
            conn.close()
            return
            
        print("\nSpecifications across all types:")
    
    # Display the results
    headers = ["Type", "Hash (short)", "File Path", "Timestamp"] if not spec_type else ["Hash (short)", "File Path", "Timestamp"]
    table_data = []
    
    for row in rows:
        if spec_type:
            hash_short = row[0][:8] + "..."
            table_data.append([hash_short, row[1], row[2]])
        else:
            hash_short = row[1][:8] + "..."
            table_data.append([row[0], hash_short, row[2], row[3]])
    
    print(tabulate(table_data, headers, tablefmt="pretty"))
    
    # Count specifications for each type
    if not spec_type:
        print("\nCounts by type:")
        for table in spec_tables:
            type_name = table.replace("_specifications", "")
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"- {type_name}: {count}")
    
    conn.close()

def compare_specifications(file_path=None, hash_prefix=None):
    """Compare specifications across different types for the same code."""
    if not ensure_cache_exists():
        return
        
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get all specification tables
    spec_tables = get_tables()
    
    if not spec_tables:
        print("No specification tables found in the database")
        conn.close()
        return
    
    # Try to find matching specifications
    if file_path:
        print(f"\nComparing specifications for file: {file_path}")
        
        # Find specifications across all tables
        specs = {}
        for table in spec_tables:
            type_name = table.replace("_specifications", "")
            cursor.execute(f"SELECT hash, code, specification, timestamp FROM {table} WHERE file_path = ?", (file_path,))
            rows = cursor.fetchall()
            
            if rows:
                specs[type_name] = rows[0]  # Take the first match
    
    elif hash_prefix:
        print(f"\nComparing specifications for hash prefix: {hash_prefix}")
        
        # Find specifications across all tables
        specs = {}
        for table in spec_tables:
            type_name = table.replace("_specifications", "")
            cursor.execute(f"SELECT hash, code, specification, timestamp, file_path FROM {table} WHERE hash LIKE ?", (f"{hash_prefix}%",))
            rows = cursor.fetchall()
            
            if rows:
                specs[type_name] = rows[0]  # Take the first match
                file_path = rows[0][4]  # Get the file path from the first match
    
    else:
        print("❌ Either file path or hash prefix must be provided")
        conn.close()
        return
    
    if not specs:
        print("No matching specifications found")
        conn.close()
        return
    
    # Print the comparison
    print(f"\nFound {len(specs)} specifications for comparison:")
    for type_name, spec_data in specs.items():
        print(f"\n=== {type_name.upper()} SPECIFICATION ===")
        print(f"Hash: {spec_data[0]}")
        print(f"Timestamp: {spec_data[3]}")
        print(f"\nSpecification:")
        print(spec_data[2][:500] + "..." if len(spec_data[2]) > 500 else spec_data[2])
    
    # If we have both original and transformed, show a diff
    if "original" in specs and "transformed" in specs:
        print("\n=== DIFF: ORIGINAL vs TRANSFORMED ===")
        original_lines = specs["original"][2].splitlines()
        transformed_lines = specs["transformed"][2].splitlines()
        
        diff = list(difflib.unified_diff(
            original_lines, 
            transformed_lines,
            fromfile="original",
            tofile="transformed",
            lineterm=""
        ))
        
        for line in diff[:50]:  # Limit to first 50 lines to avoid overwhelming output
            print(line)
        
        if len(diff) > 50:
            print("... (diff truncated)")
    
    # Export the comparison if requested
    response = input("\nExport this comparison to a file? (y/n): ")
    if response.lower() == 'y':
        export_file = os.path.join(CONFIG["OUTPUT_DIR"], f"spec_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(f"SPECIFICATION COMPARISON FOR: {file_path}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            for type_name, spec_data in specs.items():
                f.write(f"=== {type_name.upper()} SPECIFICATION ===\n")
                f.write(f"Hash: {spec_data[0]}\n")
                f.write(f"Timestamp: {spec_data[3]}\n\n")
                f.write(f"Specification:\n{spec_data[2]}\n\n")
            
            if "original" in specs and "transformed" in specs:
                f.write("=== DIFF: ORIGINAL vs TRANSFORMED ===\n")
                original_lines = specs["original"][2].splitlines()
                transformed_lines = specs["transformed"][2].splitlines()
                
                diff = list(difflib.unified_diff(
                    original_lines, 
                    transformed_lines,
                    fromfile="original",
                    tofile="transformed",
                    lineterm=""
                ))
                
                for line in diff:
                    f.write(f"{line}\n")
        
        print(f"\nComparison exported to: {export_file}")
    
    conn.close()

def export_specifications(spec_type=None, output_format="json"):
    """Export specifications to a file."""
    if not ensure_cache_exists():
        return
        
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Determine which tables to export
    tables_to_export = []
    if spec_type:
        table = f"{spec_type}_specifications"
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            tables_to_export.append(table)
        else:
            print(f"❌ Table '{table}' not found in the database")
            conn.close()
            return
    else:
        tables_to_export = get_tables()
    
    if not tables_to_export:
        print("No tables to export")
        conn.close()
        return
    
    # Export each table
    for table in tables_to_export:
        type_name = table.replace("_specifications", "")
        
        # Get all rows from the table
        cursor.execute(f"SELECT hash, file_path, code, specification, timestamp, model, temperature FROM {table}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No data to export from {table}")
            continue
        
        # Format the data
        data = []
        for row in rows:
            item = {
                "hash": row[0],
                "file_path": row[1],
                "code": row[2],
                "specification": row[3],
                "timestamp": row[4],
                "model": row[5],
                "temperature": row[6]
            }
            data.append(item)
        
        # Export to file
        export_file = os.path.join(CONFIG["OUTPUT_DIR"], f"{type_name}_specifications_export.{output_format}")
        
        if output_format == "json":
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:  # Default to txt
            with open(export_file, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(f"=== {item['file_path']} ===\n")
                    f.write(f"Hash: {item['hash']}\n")
                    f.write(f"Timestamp: {item['timestamp']}\n")
                    f.write(f"Model: {item['model']}\n")
                    f.write(f"Temperature: {item['temperature']}\n\n")
                    f.write("Python Code:\n")
                    f.write(f"{item['code']}\n\n")
                    f.write("Specification:\n")
                    f.write(f"{item['specification']}\n\n")
                    f.write("-" * 80 + "\n\n")
        
        print(f"✅ Exported {len(data)} {type_name} specifications to {export_file}")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Analysis tool for specifications")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List specifications")
    list_parser.add_argument("-t", "--type", choices=["original", "transformed", "prompt_engineered"], 
                             help="Specification type to list")
    list_parser.add_argument("-l", "--limit", type=int, default=10, help="Maximum number of entries to show")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare specifications across types")
    compare_parser.add_argument("-f", "--file", help="File path to compare")
    compare_parser.add_argument("-H", "--hash", help="Hash prefix to compare")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export specifications")
    export_parser.add_argument("-t", "--type", choices=["original", "transformed", "prompt_engineered"], 
                              help="Specification type to export (defaults to all)")
    export_parser.add_argument("-f", "--format", choices=["json", "txt"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    # Handle default command (list)
    if not args.command:
        list_specifications()
        return
        
    # Handle explicit commands
    if args.command == "list":
        spec_type = args.type if hasattr(args, "type") else None
        limit = args.limit if hasattr(args, "limit") else 10
        list_specifications(spec_type, limit)
    elif args.command == "compare":
        file_path = args.file if hasattr(args, "file") else None
        hash_prefix = args.hash if hasattr(args, "hash") else None
        compare_specifications(file_path, hash_prefix)
    elif args.command == "export":
        spec_type = args.type if hasattr(args, "type") else None
        output_format = args.format if hasattr(args, "format") else "json"
        export_specifications(spec_type, output_format)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
