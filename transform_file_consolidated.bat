@echo off
REM Simple transformation script for a single file
REM 
REM Usage examples:
REM   transform_file.bat input.py output.py control_flow,remove_print
REM   transform_file.bat input.py output.py all
REM   
REM The third parameter can be either:
REM   - A comma-separated list of transformers
REM   - The word "all" to apply all transformers

if "%1"=="" (
    echo Error: Input file path is required.
    echo Usage: transform_file.bat ^<input_file^> ^<output_file^> ^<transformers^>^|all [--verbose]
    exit /b 1
)

if "%2"=="" (
    echo Error: Output file path is required.
    echo Usage: transform_file.bat ^<input_file^> ^<output_file^> ^<transformers^>^|all [--verbose]
    exit /b 1
)

if "%3"=="" (
    echo Error: Transformations list or "all" is required.
    echo Usage: transform_file.bat ^<input_file^> ^<output_file^> ^<transformers^>^|all [--verbose]
    exit /b 1
)

set VERBOSE=
if "%4"=="--verbose" set VERBOSE=--verbose

if "%3"=="all" (
    python transform_code.py --single-file "%1" --output-file "%2" --all %VERBOSE%
) else (
    python transform_code.py --single-file "%1" --output-file "%2" --transformers "%3" %VERBOSE%
)
