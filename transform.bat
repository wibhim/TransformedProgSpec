@echo off
REM Run transformation with specific options
REM Usage:
REM   transform.bat [--all|--core-only|--no-core|--transformers name1,name2] [--verbose] [--list]

python transform_code.py %*
