#!/usr/bin/env python
"""
Entry point for incremental code collection with deduplication.
Supports batch collection of Python programs while preventing duplicates.

Usage:
    # Collect a batch of 500 programs (default)
    python collect_incremental.py
    
    # Collect specific batch size
    python collect_incremental.py --batch-size 200
    
    # Show collection statistics
    python collect_incremental.py --stats
    
    # Plan next batch without executing
    python collect_incremental.py --plan-only
    
    # Target specific repositories
    python collect_incremental.py --repos "django/django" "scikit-learn/scikit-learn"
    
    # Test mode (collect just a few files)
    python collect_incremental.py --test-mode
"""
import sys
import os

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the deduplicated collection functionality
from src.collection.collect_deduplicated import main as collect_main

if __name__ == "__main__":
    # Pass all arguments to the deduplicated collection module
    sys.exit(collect_main())
