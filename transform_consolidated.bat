@echo off
REM Consolidated transformation script for Python to Dafny project
REM 
REM This batch file handles both single file transformation and batch processing of datasets.
REM
REM Usage examples:
REM   # Transform a single file with specific transformers
REM   transform.bat --single-file input.py --output-file output.py --transformers control_flow,remove_print
REM   
REM   # Transform a file with all available transformers
REM   transform.bat --single-file input.py --output-file output.py --all
REM   
REM   # List available transformers
REM   transform.bat --list
REM   
REM   # Run transformations on the entire dataset with specific transformers
REM   transform.bat --transformers control_flow,variable_naming,remove_print
REM   
REM   # Run all transformations on the dataset
REM   transform.bat --all

python transform_code.py %*
