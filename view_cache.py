#!/usr/bin/env python
"""
Simple script to view the cache database content.
This provides a command-line interface for examining the specification cache.
"""

import os
import sqlite3
import argparse
import json
from config import CONFIG
from tabulate import tabulate
import hashlib

# Cache configuration
CACHE_DIR = os.path.join(CONFIG["OUTPUT_DIR"], "cache")
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")

def ensure_cache_exists():
    """Make sure the cache database exists."""
    if not os.path.exists(CACHE_DB):
        print(f"❌ Cache database not found at {CACHE_DB}")
        print("Please run the main script first to generate the cache.")
        return False
    return True

def list_entries(limit=10, query=None):
    """List entries in the cache database."""
    if not ensure_cache_exists():
        return
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Base query for listing entries
    sql = "SELECT hash, file_path, timestamp, model, temperature FROM specifications"
    params = []
    
    # Add search condition if query provided
    if query:
        sql += " WHERE file_path LIKE ? OR code LIKE ? OR specification LIKE ?"
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    
    # Add order and limit
    sql += " ORDER BY timestamp DESC"
    if limit > 0:
        sql += f" LIMIT {limit}"
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    if not rows:
        print("No cache entries found.")
        return
    
    # Format the output using tabulate
    headers = ["Hash (short)", "File Path", "Timestamp", "Model", "Temp"]
    table_data = []
    
    for row in rows:
        hash_short = row[0][:8] + "..."  # Truncate the hash
        table_data.append([hash_short, row[1], row[2], row[3], row[4]])
    
    print(tabulate(table_data, headers, tablefmt="pretty"))
    print(f"Total entries shown: {len(rows)}")
    
    # Show total count in database
    cursor.execute("SELECT COUNT(*) FROM specifications")
    count = cursor.fetchone()[0]
    print(f"Total entries in database: {count}")
    
    conn.close()

def get_entry_by_hash(hash_prefix):
    """Retrieve a specific entry by hash prefix."""
    if not ensure_cache_exists():
        return
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Find all entries that start with the provided hash prefix
    cursor.execute("SELECT hash, file_path, code, specification, timestamp, model, temperature FROM specifications WHERE hash LIKE ?", 
                   [f"{hash_prefix}%"])
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No entries found with hash prefix '{hash_prefix}'")
        return
    
    if len(rows) > 1:
        print(f"Multiple entries found with hash prefix '{hash_prefix}':")
        for row in rows:
            print(f"- {row[0]}: {row[1]}")
        print("Please provide a more specific hash prefix.")
        return
    
    # Display the entry details
    row = rows[0]
    print("\n=== CACHE ENTRY DETAILS ===")
    print(f"Hash: {row[0]}")
    print(f"File: {row[1]}")
    print(f"Timestamp: {row[4]}")
    print(f"Model: {row[5]}")
    print(f"Temperature: {row[6]}")
    
    print("\n=== PYTHON CODE ===")
    print(row[2])
    
    print("\n=== SPECIFICATION ===")
    print(row[3])
    
    conn.close()

def get_entry_by_path(file_path):
    """Retrieve entries for a specific file path."""
    if not ensure_cache_exists():
        return
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Find all entries for the given file path
    cursor.execute("SELECT hash, file_path, code, specification, timestamp FROM specifications WHERE file_path = ?", 
                   [file_path])
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No entries found for file path '{file_path}'")
        return
    
    # Display summary of entries
    print(f"\nFound {len(rows)} entries for '{file_path}':")
    for i, row in enumerate(rows):
        print(f"\n--- Entry {i+1} ---")
        print(f"Hash: {row[0]}")
        print(f"Timestamp: {row[4]}")
        print(f"Code preview: {row[2][:100]}...")
    
    conn.close()

def find_hash_for_code(code_snippet):
    """Calculate hash for a given code snippet and find matching entries."""
    if not ensure_cache_exists():
        return
    
    # Calculate the hash for the code snippet
    code_hash = hashlib.md5(code_snippet.encode()).hexdigest()
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Look for entries with this hash
    cursor.execute("SELECT hash, file_path, timestamp FROM specifications WHERE hash = ?", [code_hash])
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No entries found with hash {code_hash}")
        print("This code snippet is not cached.")
        return
    
    print(f"\nCalculated hash: {code_hash}")
    print(f"Found {len(rows)} matching entries:")
    
    for row in rows:
        print(f"- {row[1]} (timestamp: {row[2]})")
    
    conn.close()

def clear_cache(confirm=False):
    """Clear the cache database."""
    if not ensure_cache_exists():
        return
    
    if not confirm:
        response = input("Are you sure you want to clear the cache? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get current count for reporting
    cursor.execute("SELECT COUNT(*) FROM specifications")
    count = cursor.fetchone()[0]
    
    # Delete all records
    cursor.execute("DELETE FROM specifications")
    conn.commit()
    
    print(f"🗑️  Cache cleared: {count} entries removed")
    conn.close()

def main():
    """Main function to parse arguments and run commands."""
    parser = argparse.ArgumentParser(description="View and manage the specification cache database.")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List cache entries")
    list_parser.add_argument("-l", "--limit", type=int, default=10, help="Number of entries to show (default: 10, use 0 for all)")
    list_parser.add_argument("-q", "--query", type=str, help="Search string to filter entries")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific cache entry")
    get_parser.add_argument("hash", help="Hash prefix of the entry to retrieve")
    
    # Find by file path command
    file_parser = subparsers.add_parser("file", help="Find entries for a specific file path")
    file_parser.add_argument("path", help="File path to search for")
    
    # Find hash for code snippet
    hash_parser = subparsers.add_parser("hash", help="Calculate hash for a code snippet and check if it's cached")
    hash_parser.add_argument("file", help="File containing the code snippet")
    
    # Clear cache command
    clear_parser = subparsers.add_parser("clear", help="Clear the cache database")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "list" or args.command is None:
        # Default to list if no command specified
        limit = args.limit if hasattr(args, "limit") else 10
        query = args.query if hasattr(args, "query") else None
        list_entries(limit, query)
    elif args.command == "get":
        get_entry_by_hash(args.hash)
    elif args.command == "file":
        get_entry_by_path(args.path)
    elif args.command == "hash":
        # Read code from file
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()
            find_hash_for_code(code)
        except FileNotFoundError:
            print(f"File not found: {args.file}")
    elif args.command == "clear":
        clear_cache(args.yes)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
