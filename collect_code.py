#!/usr/bin/env python
"""
Entry point for code collection functionality.
Collects Python code from GitHub repositories for transformation and verification.

Usage:
    python collect_code.py --target 200 --max-per-repo 20 --min-lines 15
"""
import sys
import os

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the collection functionality
from src.collection.collect import main as collect_main

if __name__ == "__main__":
    # Pass all arguments to the collection module
    sys.exit(collect_main())
