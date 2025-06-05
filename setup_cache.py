#!/usr/bin/env python
"""
Enhanced caching setup script for the Python to Dafny pipeline.
This script sets up the database structure for caching specifications,
GitHub API requests, and Dafny verifications using separate tables.
"""

import sqlite3
import os
import sys
import argparse
from config import CONFIG

# Cache configuration from the original caching system
CACHE_DIR = os.path.join(CONFIG["OUTPUT_DIR"], "cache")
CACHE_DB = os.path.join(CACHE_DIR, "specification_cache.db")

def setup_cache_structure():
    """Initialize an enhanced cache database structure."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    print("Creating/updating database tables...")
    
    # Specifications for original programs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS original_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL
    )
    ''')
    print("- Created table: original_specifications")
    
    # Specifications for transformed programs (preserve existing data)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transformed_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL
    )
    ''')
    print("- Created table: transformed_specifications")
    
    # Specifications for prompt-engineered programs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompt_engineered_specifications (
        hash TEXT PRIMARY KEY,
        file_path TEXT,
        code TEXT,
        specification TEXT,
        timestamp TEXT,
        model TEXT,
        temperature REAL,
        prompt_template TEXT
    )
    ''')
    print("- Created table: prompt_engineered_specifications")
    
    # GitHub API cache
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS github_requests (
        request_url TEXT PRIMARY KEY,
        response_data TEXT,
        timestamp TEXT,
        status_code INTEGER
    )
    ''')
    print("- Created table: github_requests")
    
    # Dafny verification cache
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dafny_verifications (
        dafny_code_hash TEXT PRIMARY KEY,
        file_path TEXT,
        dafny_code TEXT,
        verification_result TEXT,
        verification_time REAL,
        timestamp TEXT,
        success INTEGER
    )
    ''')
    print("- Created table: dafny_verifications")
    
    conn.commit()
    
    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[table[0] for table in tables]}")
    
    # Check if we need to migrate data from the original specifications table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='specifications'")
    if cursor.fetchone():
        print("Original 'specifications' table found. Would you like to migrate data to the new structure?")
        response = input("Migrate data to 'transformed_specifications'? (y/n): ")
        if response.lower() == 'y':
            cursor.execute('''
            INSERT OR IGNORE INTO transformed_specifications 
            SELECT hash, file_path, code, specification, timestamp, model, temperature
            FROM specifications
            ''')
            conn.commit()
            print(f"✅ Data migrated from 'specifications' to 'transformed_specifications'")
    
    print(f"💾 Enhanced cache structure setup complete at {CACHE_DB}")
    
    # Print table summary
    print("\nDatabase Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"- {table_name}: {count} entries")
    
    conn.close()
    return True

def view_cache_stats():
    """Display statistics about the cache database."""
    if not os.path.exists(CACHE_DB):
        print(f"❌ Cache database not found: {CACHE_DB}")
        return
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    print("\n📊 Cache Database Statistics:")
    
    # Get database size
    db_size_mb = os.path.getsize(CACHE_DB) / (1024 * 1024)
    print(f"Database size: {db_size_mb:.2f} MB")
    
    # Get table statistics
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT 1")
            timestamp_row = cursor.fetchone()
            last_update = timestamp_row[0] if timestamp_row else "N/A"
            
            print(f"\n{table_name}:")
            print(f"  - Entries: {count}")
            print(f"  - Last updated: {last_update}")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Setup and manage the enhanced cache structure")
    parser.add_argument("--setup", action="store_true", help="Setup or upgrade the cache database structure")
    parser.add_argument("--stats", action="store_true", help="View cache statistics")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_cache_structure()
    elif args.stats:
        view_cache_stats()
    else:
        setup_cache_structure()  # Default action

if __name__ == "__main__":
    main()
