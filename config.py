#!/usr/bin/env python
"""
Configuration File

This file centralizes all configuration settings for the research pipeline.
"""
import os
from typing import Dict, Any

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ERROR_DIR = os.path.join(BASE_DIR, "errors")
TOKEN_DIR = os.path.join(BASE_DIR, "token")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "dafny_programs"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "transformed_programs"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "verification_reports"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "verification_reports", "individual"), exist_ok=True)

# Configuration for GitHub token collection
GITHUB_CONFIG = {
    "token_file": os.path.join(TOKEN_DIR, "token_git.txt"),
    "output_json": os.path.join(OUTPUT_DIR, "python_code_dataset.json"),
}

# Configuration for code cleanup
CLEANUP_CONFIG = {
    "input_json": os.path.join(OUTPUT_DIR, "python_code_dataset_with_metadata.json"),
    "output_json": os.path.join(OUTPUT_DIR, "cleaned_code_dataset_ast.json"),
    "error_log": os.path.join(ERROR_DIR, "cleanup_errors_ast.txt"),
}

# Configuration for code transformation
TRANSFORMATION_CONFIG = {
    "input_json": os.path.join(OUTPUT_DIR, "cleaned_code_dataset_ast.json"),
    "output_json": os.path.join(OUTPUT_DIR, "transformed_code_dataset.json"),
    "error_file": os.path.join(ERROR_DIR, "transformation_errors.txt"),
}

# Configuration for ChatGPT specification generation
CHATGPT_CONFIG = {
    "input_json": os.path.join(OUTPUT_DIR, "transformed_code_dataset.json"),
    "output_json": os.path.join(OUTPUT_DIR, "chatgpt_specifications.json"),
    "token_file": os.path.join(TOKEN_DIR, "token_gpt.txt"),
    "error_log": os.path.join(ERROR_DIR, "chatgpt_spec_errors.txt"),
    "delay": 3,  # seconds between API calls
    "temperature": 0.2,
}

# Configuration for Dafny verification
DAFNY_CONFIG = {
    "input_json": os.path.join(OUTPUT_DIR, "chatgpt_specifications.json"),
    "output_json": os.path.join(OUTPUT_DIR, "dafny_verification_results.json"),
    "dafny_programs_dir": os.path.join(OUTPUT_DIR, "dafny_programs"),
    "timeout": 60,  # seconds
}

# Configuration for report generation
REPORT_CONFIG = {
    "input_json": os.path.join(OUTPUT_DIR, "dafny_verification_results.json"),
    "output_dir": os.path.join(OUTPUT_DIR, "verification_reports"),
    "template_dir": os.path.join(BASE_DIR, "templates"),
}

# Aggregate all configurations
CONFIG = {
    "github": GITHUB_CONFIG,
    "cleanup": CLEANUP_CONFIG,
    "transform": TRANSFORMATION_CONFIG,
    "chatgpt": CHATGPT_CONFIG,
    "dafny": DAFNY_CONFIG,
    "report": REPORT_CONFIG,
    # Add base directories to config for easy access
    "BASE_DIR": BASE_DIR,
    "OUTPUT_DIR": OUTPUT_DIR,
    "ERROR_DIR": ERROR_DIR,
    "TOKEN_DIR": TOKEN_DIR,
}

# Additional settings
DEBUG = False
VERBOSE = True
