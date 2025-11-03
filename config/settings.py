#!/usr/bin/env python
"""
Configuration File

This file centralizes all configuration settings for the research pipeline.
"""
import os
from typing import Dict, Any

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Project root directory
DATA_DIR = os.path.join(BASE_DIR, "data")
ERROR_DIR = os.path.join(BASE_DIR, "errors")
TOKEN_DIR = os.path.join(BASE_DIR, "token")

# Sub-directories
REPO_DIR = os.path.join(DATA_DIR, "programs")
SPEC_DIR = os.path.join(DATA_DIR, "specification")
TRANSFORM_DIR = os.path.join(DATA_DIR, "transformed")
VERIFY_DIR = os.path.join(DATA_DIR, "verification")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(REPO_DIR, exist_ok=True)
os.makedirs(os.path.join(REPO_DIR, "original"), exist_ok=True)
os.makedirs(os.path.join(REPO_DIR, "python"), exist_ok=True)
os.makedirs(os.path.join(REPO_DIR, "datasets"), exist_ok=True)
os.makedirs(SPEC_DIR, exist_ok=True)
os.makedirs(TRANSFORM_DIR, exist_ok=True)
os.makedirs(VERIFY_DIR, exist_ok=True)
os.makedirs(os.path.join(VERIFY_DIR, "programs"), exist_ok=True)
os.makedirs(os.path.join(VERIFY_DIR, "reports"), exist_ok=True)
os.makedirs(os.path.join(VERIFY_DIR, "results"), exist_ok=True)
os.makedirs(os.path.join(VERIFY_DIR, "reports", "individual"), exist_ok=True)

# Configuration for GitHub token collection
GITHUB_CONFIG = {
    "token_file": os.path.join(TOKEN_DIR, "token_git.txt"),
    "output_json": os.path.join(REPO_DIR, "datasets", "python_code_dataset.json"),
    "target_repo": "Garvit244/Leetcode",  # Target repository to collect from
    "max_files": 10,  # Maximum number of files to collect
}

# Configuration for code cleanup
CLEANUP_CONFIG = {
    "input_json": os.path.join(REPO_DIR, "datasets", "python_code_dataset.json"),
    "output_json": os.path.join(REPO_DIR, "datasets", "cleaned_code_dataset_ast.json"),
    "error_log": os.path.join(ERROR_DIR, "cleanup_errors_ast.txt"),
}

# Configuration for code transformation
TRANSFORMATION_CONFIG = {
    "input_json": os.path.join(REPO_DIR, "datasets", "cleaned_code_dataset_ast.json"),
    "output_json": os.path.join(REPO_DIR, "datasets", "transformed_code_dataset.json"),
    "error_file": os.path.join(ERROR_DIR, "transformation_errors.txt"),
    # Default transformations to apply (empty list means apply all available)
    "transformations": [],
    # Whether to always include core transformers (control_flow, variable_naming, etc.)
    "include_core": True,
}

# Configuration for ChatGPT specification generation
CHATGPT_CONFIG = {
    "model": "gpt-4.1",  # Model to use for specification generation
    "input_json": "drop_parentheses_dataset.json",  # Full consolidated dataset
    "output_json": os.path.join(SPEC_DIR, "drop_parentheses_specifications.json"),
    "token_file": os.path.join(TOKEN_DIR, "token_gpt.txt"),
    "error_log": os.path.join(ERROR_DIR, "chatgpt_spec_errors.txt"),
    "delay": 5,  # Reduced delay for faster processing while staying within rate limits
    "temperature": 0.4,  # Temperature (ignored for models that don't support it like GPT-5)
    "use_cache": True,  # Enable cache for safe progress saving
    "use_enhanced_cache": True,  # Enable enhanced cache system with metadata
}

# Configuration for Dafny verification
DAFNY_CONFIG = {
    "input_json": os.path.join(SPEC_DIR, "chatgpt_specifications.json"),
    "output_json": os.path.join(VERIFY_DIR, "results", "dafny_verification_results.json"),
    "dafny_programs_dir": os.path.join(VERIFY_DIR, "programs"),
    "timeout": 60,  # seconds
}

# Configuration for report generation
REPORT_CONFIG = {
    "input_json": os.path.join(VERIFY_DIR, "results", "dafny_verification_results.json"),
    "output_dir": os.path.join(VERIFY_DIR, "reports"),
    "template_dir": os.path.join(BASE_DIR, "config", "templates"),
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
    "DATA_DIR": DATA_DIR,
    "REPO_DIR": REPO_DIR,
    "SPEC_DIR": SPEC_DIR,
    "TRANSFORM_DIR": TRANSFORM_DIR,
    "VERIFY_DIR": VERIFY_DIR,
    "ERROR_DIR": ERROR_DIR,
    "TOKEN_DIR": TOKEN_DIR,
}

# Additional settings
DEBUG = False
VERBOSE = True
