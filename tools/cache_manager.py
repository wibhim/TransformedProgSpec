#!/usr/bin/env python3
"""
Cache Management Utility for Specification Generator

This script provides utilities to manage and inspect the specification cache,
allowing for safe progress monitoring and recovery.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.specification.generator import (
    setup_cache, 
    get_cache_stats, 
    build_output_from_cache, 
    check_cache_progress,
    SPEC_TYPE,
    INPUT_JSON,
    OUTPUT_JSON
)
import argparse

def show_progress():
    """Show current generation progress."""
    print("📊 GENERATION PROGRESS")
    print("=" * 50)
    
    try:
        progress = check_cache_progress()
        
        print(f"Total programs: {progress['total_programs']}")
        print(f"Completed: {progress['completed']}")
        print(f"Remaining: {progress['remaining']}")
        print(f"Progress: {progress['progress_percent']}%")
        
        cache_stats = progress['cache_stats']
        print(f"\nCache info:")
        print(f"  Table: {cache_stats['table']}")
        print(f"  Cached count: {cache_stats['cached_count']}")
        if cache_stats['first_cached']:
            print(f"  First cached: {cache_stats['first_cached']}")
        if cache_stats['last_cached']:
            print(f"  Last cached: {cache_stats['last_cached']}")
            
    except Exception as e:
        print(f"❌ Error checking progress: {e}")

def build_partial_output(output_file=None):
    """Build output file from current cache."""
    print("🔨 BUILDING OUTPUT FROM CACHE")
    print("=" * 50)
    
    try:
        result_file = build_output_from_cache(output_file)
        if result_file:
            print(f"✅ Successfully created: {result_file}")
        else:
            print("❌ No cached specifications to build from")
    except Exception as e:
        print(f"❌ Error building output: {e}")

def show_cache_stats():
    """Show detailed cache statistics."""
    print("💾 CACHE STATISTICS")
    print("=" * 50)
    
    try:
        conn = setup_cache()
        stats = get_cache_stats(conn, SPEC_TYPE)
        
        print(f"Specification type: {SPEC_TYPE}")
        print(f"Cache table: {stats['table']}")
        print(f"Cached specifications: {stats['cached_count']}")
        
        if stats['first_cached']:
            print(f"First cached: {stats['first_cached']}")
        if stats['last_cached']:
            print(f"Last cached: {stats['last_cached']}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting cache stats: {e}")

def estimate_remaining_cost():
    """Estimate cost for remaining programs."""
    print("💰 COST ESTIMATION")
    print("=" * 50)
    
    try:
        progress = check_cache_progress()
        remaining = progress['remaining']
        
        if remaining == 0:
            print("🎉 All programs completed!")
            return
        
        # Rough estimates based on typical token usage
        avg_input_tokens = 500  # Average Python program size
        avg_output_tokens = 800  # Average Dafny specification size
        
        # Using GPT-4.1 pricing
        input_cost_per_1k = 0.002
        output_cost_per_1k = 0.008
        
        estimated_cost = remaining * (
            (avg_input_tokens / 1000 * input_cost_per_1k) +
            (avg_output_tokens / 1000 * output_cost_per_1k)
        )
        
        print(f"Remaining programs: {remaining}")
        print(f"Estimated tokens per program: {avg_input_tokens + avg_output_tokens}")
        print(f"Estimated cost: ${estimated_cost:.2f}")
        print(f"Note: This is a rough estimate based on average token usage")
        
    except Exception as e:
        print(f"❌ Error estimating cost: {e}")

def main():
    """Main function for cache management."""
    parser = argparse.ArgumentParser(description="Cache Management Utility")
    parser.add_argument("command", choices=[
        "progress", "build", "stats", "cost"
    ], help="Command to execute")
    parser.add_argument("--output", help="Output file path for build command")
    
    args = parser.parse_args()
    
    if args.command == "progress":
        show_progress()
    elif args.command == "build":
        build_partial_output(args.output)
    elif args.command == "stats":
        show_cache_stats()
    elif args.command == "cost":
        estimate_remaining_cost()

if __name__ == "__main__":
    main()
