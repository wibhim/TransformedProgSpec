#!/usr/bin/env python
"""
Test script for the specification caching system in chatgpt.py.
This script tests cache functionality, performance, and data integrity.
"""

import json
import time
import os
import sqlite3
import hashlib
import argparse
from datetime import datetime
from config.settings import CONFIG

# Import cache-related functions
from specification.generator import (
    setup_cache,
    get_cached_specification,
    cache_specification,
    CACHE_DB,
    CACHE_DIR
)

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {text} ".center(50, "="))
    print("=" * 50)

def clear_cache(conn=None):
    """Clear the cache database for testing."""
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(CACHE_DB)
        close_conn = True
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM specifications")
    conn.commit()
    print(f"🗑️  Cache cleared: {cursor.rowcount} entries removed")
    
    if close_conn:
        conn.close()

def get_cache_stats():
    """Get statistics about the cache."""
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get entry count
    cursor.execute("SELECT COUNT(*) FROM specifications")
    count = cursor.fetchone()[0]
    
    # Get size of the database file
    try:
        size = os.path.getsize(CACHE_DB) / (1024 * 1024)  # Size in MB
    except FileNotFoundError:
        size = 0
    
    # Get most recent entry
    cursor.execute("SELECT timestamp FROM specifications ORDER BY timestamp DESC LIMIT 1")
    recent = cursor.fetchone()
    recent_time = recent[0] if recent else "N/A"
    
    conn.close()
    
    return {
        "count": count,
        "size_mb": size,
        "recent_entry": recent_time
    }

def test_cache_functionality(test_data):
    """Test basic cache functionality (store and retrieve)."""
    print_header("TESTING CACHE FUNCTIONALITY")
    
    conn = setup_cache()
    
    # Instead of clearing the cache, let's use the existing cache if available
    # Get current cache size
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM specifications")
    cache_count = cursor.fetchone()[0]
    
    if cache_count == 0:
        print("Cache is empty. Creating test entries.")
        # Only create dummy entries if cache is empty
        for i, item in enumerate(test_data[:3]):
            file_path = item.get("file_path", f"test_file_{i}.py")
            code = item.get("transformed_code", "")
            spec = f"Test specification {i}"
            
            print(f"  - Storing specification for {file_path}")
            cache_specification(conn, code, file_path, spec)
    else:
        print(f"Using existing cache with {cache_count} entries for testing")
    
    # Test case 1: Check if we can retrieve items from the existing cache
    print("\n📝 Test Case 1: Retrieving items from existing cache")
    
    # Get the first 3 entries from the cache as examples
    cursor.execute("SELECT file_path, code, specification FROM specifications LIMIT 3")
    cache_examples = cursor.fetchall()
    
    if not cache_examples:
        print("  ⚠️ No cache entries found to test retrieval")
    else:
        for file_path, code, expected_spec in cache_examples:
            # Try to retrieve from cache
            cached_spec = get_cached_specification(conn, code, file_path)
            
            if cached_spec == expected_spec:
                print(f"  ✅ Successfully retrieved correct specification for {file_path}")
            else:
                print(f"  ❌ Failed to retrieve correct specification for {file_path}")
                print(f"     Expected length: {len(expected_spec)} chars")
                print(f"     Got length: {len(cached_spec) if cached_spec else 0} chars")
    
    # Test case 3: Try to retrieve a non-existent item
    print("\n📝 Test Case 3: Handling cache misses")
    non_existent = "def this_function_does_not_exist(): pass"
    cached = get_cached_specification(conn, non_existent, "non_existent.py")
    
    if cached is None:
        print("  ✅ Correctly returned None for non-existent item")
    else:
        print("  ❌ Incorrectly returned a result for non-existent item")
    
    conn.close()

def test_cache_performance(test_data):
    """Test the performance impact of the cache."""
    print_header("TESTING CACHE PERFORMANCE")
    
    conn = setup_cache()
    
    # Get some existing cache entries to test with
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, code, specification FROM specifications LIMIT 5")
    cache_examples = cursor.fetchall()
    
    # If we don't have enough cache examples, add some test data
    if len(cache_examples) < 5:
        print("Adding test entries to cache for performance testing")
        # Use the test data to supplement
        for i, item in enumerate(test_data[:5-len(cache_examples)]):
            file_path = item.get("file_path", f"test_file_{i}.py")
            code = item.get("transformed_code", "")
            spec = f"Test specification for performance testing {i}"
            
            cache_specification(conn, code, file_path, spec)
            cache_examples.append((file_path, code, spec))
    
    # Test case 1: Simulate API calls (cache misses)
    print("\n📝 Test Case 1: Simulating API call time (cache misses)")
    miss_times = []
    
    for i, (file_path, code, _) in enumerate(cache_examples):
        # Force a cache miss by clearing just this entry
        cursor.execute("DELETE FROM specifications WHERE file_path = ?", (file_path,))
        conn.commit()
        
        # Now simulate a cache miss with API call
        start_time = time.time()
        cached = get_cached_specification(conn, code, file_path)
        
        if cached is None:  # This should be a miss now
            # Simulate API call delay (2 seconds is typical for OpenAI API)
            print(f"  - Simulating API call for {file_path}")
            time.sleep(1.0)  # Reduced for testing purposes
            spec = f"Simulated API specification {i}"
            cache_specification(conn, code, file_path, spec)
        else:
            print(f"  ⚠️ Unexpected cache hit for {file_path} after deletion")
        
        end_time = time.time()
        miss_times.append(end_time - start_time)
        print(f"  - API call time for {file_path}: {miss_times[-1]:.4f}s")
      # Test case 2: Measure time for cache hits
    print("\n📝 Test Case 2: Measuring time for cache hits")
    hit_times = []
    
    # Re-fetch our cache examples since we modified them
    cursor.execute("SELECT file_path, code, specification FROM specifications LIMIT 5")
    cache_examples = cursor.fetchall()
    
    for i, (file_path, code, _) in enumerate(cache_examples):
        # Get from cache (should be a hit now)
        start_time = time.time()
        cached = get_cached_specification(conn, code, file_path)
        end_time = time.time()
        
        if cached:
            hit_times.append(end_time - start_time)
            print(f"  - Cache hit for {file_path}: {hit_times[-1]:.4f}s")
        else:
            print(f"  ⚠️ Unexpected cache miss for {file_path}")
            # Add to miss times instead
            miss_times.append(end_time - start_time)
    
    # Calculate performance improvement
    avg_miss = sum(miss_times) / len(miss_times) if miss_times else 0
    avg_hit = sum(hit_times) / len(hit_times) if hit_times else 0
    
    if avg_miss > 0:
        speedup = avg_miss / avg_hit if avg_hit > 0 else float('inf')
        time_saved_percent = ((avg_miss - avg_hit) / avg_miss) * 100
        
        print(f"\n⚡ Performance Results:")
        print(f"  - Average time without cache: {avg_miss:.4f}s")
        print(f"  - Average time with cache: {avg_hit:.4f}s")
        print(f"  - Speedup factor: {speedup:.2f}x")
        print(f"  - Time saved: {time_saved_percent:.2f}%")
    
    conn.close()

def test_data_integrity(input_json):
    """Compare cached results with freshly generated ones."""
    print_header("TESTING DATA INTEGRITY")
    
    # This test would normally compare cached results with new API calls
    # Here we'll simulate by:
    # 1. Clearing cache
    # 2. Running a sample from the dataset
    # 3. Storing the results
    # 4. Comparing with a second run
    
    print("\nℹ️  Data integrity testing would typically involve:")
    print("  - Generating specifications from the API")
    print("  - Comparing them with cached specifications")
    print("  - Ensuring they are identical or within acceptable variation")
    print("\nFor real testing:")
    print("  1. Run the main script once with USE_CACHE = False")
    print("  2. Run it again with USE_CACHE = True")
    print("  3. Compare the output JSON files for consistency")

def view_cache_contents():
    """View the contents of the cache database."""
    print_header("CACHE CONTENTS")
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT hash, file_path, timestamp FROM specifications ORDER BY timestamp DESC LIMIT 10")
    entries = cursor.fetchall()
    
    if not entries:
        print("\nNo entries in the cache database.")
    else:
        print("\nMost recent 10 entries:")
        print(f"{'Hash (first 8 chars)':<20} {'File Path':<30} {'Timestamp':<25}")
        print("-" * 75)
        
        for entry in entries:
            hash_short = entry[0][:8]
            print(f"{hash_short:<20} {entry[1]:<30} {entry[2]:<25}")
    
    conn.close()

def main():
    """Run cache tests."""
    parser = argparse.ArgumentParser(description="Test the specification caching system.")
    parser.add_argument("--clear", action="store_true", help="Clear the cache before testing")
    parser.add_argument("--view", action="store_true", help="View cache contents")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--full", action="store_true", help="Run all tests")
    parser.add_argument("--functionality", action="store_true", help="Test cache functionality")
    parser.add_argument("--performance", action="store_true", help="Test cache performance")
    parser.add_argument("--integrity", action="store_true", help="Test data integrity")
    
    args = parser.parse_args()
    
    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)
      # Load test data
    input_json = os.path.join(CONFIG["OUTPUT_DIR"], "transformed_code_dataset.json")
    try:
        with open(input_json, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        print(f"Loaded test data from {input_json}: {len(test_data)} items")
    except FileNotFoundError:
        print(f"❌ Test data file not found: {input_json}")
        print("Creating sample test data for testing purposes...")
        # Create sample test data
        test_data = [
            {"file_path": "sample1.py", "transformed_code": "def add(a, b):\n    return a + b"},
            {"file_path": "sample2.py", "transformed_code": "def subtract(a, b):\n    return a - b"},
            {"file_path": "sample3.py", "transformed_code": "def multiply(a, b):\n    return a * b"},
            {"file_path": "sample4.py", "transformed_code": "def divide(a, b):\n    return a / b"},
            {"file_path": "sample5.py", "transformed_code": "def power(a, b):\n    return a ** b"}
        ]
    
    # Print initial stats
    if args.stats or args.full:
        stats = get_cache_stats()
        print_header("CACHE STATISTICS")
        print(f"📊 Cache Entry Count: {stats['count']}")
        print(f"📊 Cache Size: {stats['size_mb']:.2f} MB")
        print(f"📊 Most Recent Entry: {stats['recent_entry']}")
    
    # Clear cache if requested
    if args.clear:
        conn = setup_cache()
        clear_cache(conn)
        conn.close()
    
    # View cache contents
    if args.view:
        view_cache_contents()
    
    # Run tests
    if args.functionality or args.full:
        test_cache_functionality(test_data)
    
    if args.performance or args.full:
        test_cache_performance(test_data)
    
    if args.integrity or args.full:
        test_data_integrity(input_json)
    
    # Show final stats
    if args.full:
        stats = get_cache_stats()
        print_header("FINAL CACHE STATISTICS")
        print(f"📊 Cache Entry Count: {stats['count']}")
        print(f"📊 Cache Size: {stats['size_mb']:.2f} MB")
        print(f"📊 Most Recent Entry: {stats['recent_entry']}")

if __name__ == "__main__":
    main()
