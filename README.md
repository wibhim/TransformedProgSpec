# Python to Dafny Formal Verification Pipeline

This project automates the process of transforming Python code into formal specifications using Large Language Models (specifically OpenAI's GPT models), and then verifies these specifications using the Dafny verification language.

## Project Overview

The pipeline consists of several steps:
1. **Data Collection**: Obtain Python code snippets from GitHub repositories
2. **Code Cleanup**: Remove docstrings, comments, and normalize code
3. **Code Transformation**: Simplify code while preserving variable names
4. **Specification Generation**: Generate formal Dafny specifications using GPT models
5. **Dafny Extraction**: Extract Dafny code from specifications and save as .dfy files
6. **Dafny Verification**: Verify the extracted Dafny code
7. **Report Generation**: Create reports of verification results

## Project Structure

```
Prototype/
├── config/                   # Configuration settings and templates
│   ├── settings.py           # Central configuration file
│   └── templates/            # Prompt templates for specification generation
│
├── data/                     # All data storage
│   ├── cache/                # Cache for API requests
│   ├── repositories/         # Repository data
│   │   ├── datasets/         # Processed datasets (JSON files)
│   │   ├── original/         # Original collected code (JSON format)
│   │   └── python/           # Python file versions
│   │
│   ├── specification/        # Generated specifications
│   ├── transformed/          # Transformed code
│   └── verification/         # Verification data
│       ├── programs/         # Dafny programs
│       ├── reports/          # Verification reports
│       └── results/          # Verification results
│
├── errors/                   # Error logs
├── scripts/                  # Utility scripts
├── src/                      # Source code
│   ├── collection/           # Code collection modules
│   ├── specification/        # Specification generation
│   ├── transformation/       # Code transformation
│   ├── utils/                # Utility modules
│   └── verification/         # Verification modules
│
├── tests/                    # Test suite
├── token/                    # API tokens (gitignored)
└── main.py                   # Pipeline entry point
```

## Setup Instructions

### 1. Prerequisites

- **Python 3.9+** 
- **Dafny** (must be installed and accessible from your PATH)
- **GitHub API Token** (for collecting code from GitHub)
- **OpenAI API Key** (for generating specifications)

### 2. Environment Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv env
   env\Scripts\activate
   ```
3. Install required packages:
   ```
   pip install openai pygithub tqdm astor typing-extensions requests
   ```
   
   Or use the provided requirements.txt file:
   ```
   pip install -r requirements.txt
   ```

### 3. Configuration

1. Ensure token directory exists:
   ```
   mkdir token
   ```

2. Create token files:
   - Create `token\token_git.txt` with your GitHub API token
   - Create `token\token_gpt.txt` with your OpenAI API key

3. The `config.py` file contains all the configuration settings for the pipeline:

   **Key Configuration Options:**
   
   - GitHub repository settings:
     ```python
     GITHUB_CONFIG = {
         "token_file": os.path.join(TOKEN_DIR, "token_git.txt"),
         "output_json": os.path.join(OUTPUT_DIR, "python_code_dataset.json"),
         "target_repo": "Garvit244/Leetcode",  # Change to your target repository
         "max_files": 5,  # Change to collect more files
     }
     ```
   
   - ChatGPT API settings:
     ```python
     CHATGPT_CONFIG = {
         # ...
         "delay": 3,  # Seconds between API calls
         "temperature": 0.2,  # Creativity parameter for GPT
     }
     ```
   
   - Dafny verification timeout:
     ```python
     DAFNY_CONFIG = {
         # ...
         "timeout": 60,  # Seconds before timeout
     }
     ```
   
   Review and adjust these settings as needed for your specific use case.

## Usage

The project provides multiple ways to interact with the pipeline:

### Option 1: Using the Complete Pipeline (main.py)

Use the main entry point to run the entire pipeline or specific steps:

```
python main.py
```

Or run specific steps:

```
python main.py --steps github,cleanup,transform,spec,extract,verify,report
```

Available steps:
- `github`: Collect Python code from GitHub
- `cleanup`: Clean and normalize code
- `transform`: Transform code to simplify structure
- `spec`: Generate Dafny specifications using LLMs
- `extract`: Extract Dafny code from specifications into .dfy files
- `verify`: Verify extracted Dafny code
- `report`: Generate verification reports

Example:
```
python main.py --steps cleanup,transform,spec
```

### Option 2: Using Individual Entry Points

The project also provides dedicated entry point scripts for each stage:

1. **Collect Code**: `collect_code.py`
   ```
   python collect_code.py --target 200 --max-per-repo 20 --min-lines 15
   ```

2. **Transform Code**: `transform_code.py`
   ```
   # Transform a single file
   python transform_code.py --single-file input.py --output-file output.py --transformers control_flow,variable_naming
   
   # List available transformers
   python transform_code.py --list
   ```

3. **Generate Specifications**: `generate_specs.py`
   ```
   python generate_specs.py --input transformed_code.json --output specs.json
   ```

4. **Verify Specifications**: `verify_specs.py`
   ```
   python verify_specs.py --input specs.json --output results.json
   ```

5. **Analyze Results**: `analyze_results.py`
   ```
   python analyze_results.py --specs specs.json --results verification_results.json
   ```

### Specifying GitHub Repository

You can now easily specify which GitHub repository to collect Python files from:

```
python main.py --steps github --repo "owner/repository" --max-files 20
```

This can be configured through:
1. Command-line arguments (shown above)
2. Directly editing `config.py`
3. Running the data collection script directly:
   ```
   python -m process.data_collect --repo "owner/repository" --max-files 10 --output "path/to/output.json"
   ```

### Verbose Output

For more detailed output, use the `--verbose` flag:
```
python main.py --verbose
```

### Full Command-Line Options

```
python main.py --help
```

This will display all available command-line options.

## Project Structure

- **main.py**: Entry point for running the pipeline
- **config.py**: Centralized configuration for all components
- **process/**: Core processing scripts
  - **data_collect.py**: Collects Python code from GitHub repositories
  - **cleanup.py**: Cleans and normalizes code
  - **transform_final.py**: Transforms code while preserving variable names
  - **chatgpt.py**: Generates formal specifications using OpenAI's API
  - **dafny_check.py**: Verifies the specifications with Dafny
  - **extract_dafny.py**: Extracts Dafny code from JSON results
  - **format_dafny_results.py**: Generates verification reports
  - **json_to_py.py**: Extracts Python code from JSON results
- **transformers/**: Specialized code transformation modules
  - **pipeline.py**: Coordinates the transformation process
  - **control_flow.py**: Simplifies control flow structures
  - **variable_naming.py**: Handles variable naming conventions
  - **expression_decomp.py**: Simplifies complex expressions
  - **loop_standard.py**: Standardizes loops
  - **function_extract.py**: Extracts functions from code

## Pipeline Data Flow

The data flows through the pipeline as follows:

1. **GitHub → `python_code_dataset.json`**
   - Raw Python code collected from GitHub

2. **Cleanup → `cleaned_code_dataset_ast.json`**
   - Code with comments and docstrings removed

3. **Transformation → `transformed_code_dataset.json`**
   - Simplified code with preserved variable names

4. **Specification → `chatgpt_specifications.json`**
   - Code paired with generated Dafny specifications

5. **Extraction → `output/dafny_programs/*.dfy`**
   - Dafny code extracted from specifications and saved as .dfy files

6. **Verification → `dafny_verification_results.json`**
   - Verification results from Dafny

7. **Reports → `verification_reports/`**
   - HTML and text reports on verification results
  - **format_dafny_results.py**: Generates readable reports
- **output/**: Output files and directories
  - **dafny_programs/**: Generated Dafny programs
  - **transformed_programs/**: Transformed Python code
  - **verification_reports/**: HTML and text reports
- **token/**: Directory for API tokens (not committed to repository)

## Output Files

The pipeline generates several output files:
- JSON datasets at each processing stage
- Transformed Python code files
- Dafny (.dfy) files with formal specifications
- HTML and text verification reports

## Customization

You can customize the pipeline by:
1. Modifying the configuration in `config.py`
2. Adjusting transformation rules in `process/transform_final.py`
3. Changing prompt templates in `process/chatgpt.py`

## Troubleshooting

- **GitHub API Rate Limits**: If you encounter rate limiting issues, increase the delay between requests in the config or use an authenticated token with higher limits.

- **OpenAI API Errors**: 
  - Check that your API key is correct in `token/token_gpt.txt`
  - Ensure your OpenAI account has sufficient quota
  - If you get timeout errors, increase the `DELAY` parameter in `config.py`
  
- **Token File Issues**:
  - Ensure your token directory exists and contains valid token files
  - Check that the files are named correctly: `token_git.txt` and `token_gpt.txt`
  - Verify that the token files contain only the token text with no extra spaces or characters
  
- **GitHub Repository Access Issues**:
  - Make sure the repository you're targeting is public or your token has access to it
  - Test with a simpler repository if you're encountering parsing problems
  - Try reducing the number of files with `--max-files 3` for testing

- **Dafny Extraction or Verification Failures**: 
  - Ensure Dafny is properly installed and in your system PATH
  - Make sure the extraction step runs before verification to create the .dfy files
  - Try increasing the timeout in `config.py` if verifications are timing out
  - Check the verification reports for specific error messages
  
- **Import Errors**:
  - If you're getting import errors when running scripts directly, try running them through the main entry point:
    ```
    python main.py --steps [step]
    ```

## Common Examples

### Running Just the Extraction Step
```
python main.py --steps extract
```

### Collecting from a Different Repository
```
python main.py --steps github --repo "tensorflow/models" --max-files 10
```

### Running Extraction and Verification Steps
```
python main.py --steps extract,verify --verbose
```

### Generating Reports After Verification
```
python main.py --steps report
```

### Running Code Transformation

You can run the code transformation step with different options:

#### Running All Transformations (Default)

For transforming a dataset:

```
python scripts/run_transformation.py --all
```

or

```
transform.bat --all
```

For transforming a single file:

```
python standalone_transform.py input.py output.py --all
```

or

```
transform_file.bat input.py output.py --all
```

#### Running Standard Structural Transformations

The following transformations are available for code structure simplification:
- control_flow (simplifies control flow)
- variable_naming (standardizes variable naming)
- expression (decomposes complex expressions)
- loop_standard (standardizes loop structures)
- function_extract (extracts nested functions)

For a dataset, you can select these transformers individually or as a group:

```
python scripts/run_transformation.py --transformers control_flow,variable_naming,expression,loop_standard,function_extract
```

or 

```
transform.bat --transformers control_flow,variable_naming,expression,loop_standard,function_extract
```

For a single file:

```
python standalone_transform.py input.py output.py --core-only
```

or

```
transform_file.bat input.py output.py --core-only
```

#### Running Specific Transformations

You can select specific transformations to run:

For a dataset:

```
python scripts/run_transformation.py --transformers drop_comments,remove_print
```

or

```
transform.bat --transformers drop_comments,remove_print
```

For a single file:

```
python standalone_transform.py input.py output.py --transformers drop_comments,remove_print
```

or

```
transform_file.bat input.py output.py --transformers drop_comments,remove_print
```

You can also use the simplified batch file for single file transformations:

```
transform_selective.bat input.py output.py drop_comments,remove_print
```

#### Selecting Specific Transformations

All transformers can be selected individually. For example, to run just specific transformers:

```
python scripts/run_transformation.py --transformers drop_comments,remove_print
```

For a single file:

```
python standalone_transform.py input.py output.py --no-core --transformers drop_comments,remove_print
```

or

```
transform_file.bat input.py output.py --no-core --transformers drop_comments,remove_print
```

#### Available Transformers

The following transformers are available:

Core transformers (applied by default):
- `control_flow`: Simplifies control flow structures
- `variable_naming`: Renames variables for clarity
- `expression`: Decomposes complex expressions
- `loop_standard`: Standardizes loop structures
- `function_extract`: Extracts embedded functions

Additional transformers:
- `drop_comments`: Removes code comments
- `drop_self`: Removes self references
- `drop_path`: Removes path operations
- `drop_return`: Removes explicit return statements
- `drop_vars`: Removes unused variables
- `replace_parentheses`: Replaces redundant parentheses
- `forget_indent`: Normalizes indentation
- `remove_exceptions`: Removes exception handling
- `remove_print`: Removes print statements
- `remove_else`: Removes else statements (converting to if-not structures)

#### Transforming a Single File

You can transform a single Python file instead of processing the entire dataset:

```
python scripts/run_transformation.py --single-file input.py --output-file output.py --transformers drop_comments,remove_print
```

or

```
transform_file.bat input.py output.py --transformers drop_comments,remove_print
```