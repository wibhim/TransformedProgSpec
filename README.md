# Python to Dafny Formal Verification Pipeline

This project automates the process of transforming Python code into formal specifications using Large Language Models (specifically OpenAI's GPT models), and then verifies these specifications using the Dafny verification language.

## Project Overview

The pipeline consists of several steps:
1. **Data Collection**: Obtain Python code snippets from GitHub repositories
2. **Code Cleanup**: Remove docstrings, comments, and normalize code
3. **Code Transformation**: Simplify code while preserving variable names
4. **Specification Generation**: Generate formal Dafny specifications using GPT models
5. **Dafny Verification**: Verify the specifications using Dafny
6. **Report Generation**: Create reports of verification results

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

1. Create a token directory:
   ```
   mkdir token
   ```

2. Create token files:
   - Create `token\token_git.txt` with your GitHub API token
   - Create `token\token_gpt.txt` with your OpenAI API key

3. The `config.py` file contains all the configuration settings for the pipeline. Review and adjust as needed.

## Usage

The project uses a single entry point (`main.py`) that can run the entire pipeline or individual steps.

### Running the Complete Pipeline

```
python main.py
```

### Running Specific Steps

```
python main.py --steps step1,step2,step3
```

Available steps:
- `github`: Collect Python code from GitHub
- `cleanup`: Clean and normalize code
- `transform`: Transform code to simplify structure
- `spec`: Generate Dafny specifications using LLMs
- `verify`: Verify specifications with Dafny
- `report`: Generate verification reports

Example:
```
python main.py --steps cleanup,transform,spec
```

### Verbose Output

For more detailed output, use the `--verbose` flag:
```
python main.py --verbose
```

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

- **GitHub API Rate Limits**: If you encounter rate limiting issues, increase the delay between requests in the config.
- **OpenAI API Errors**: Check your API key and ensure it has sufficient quota.
- **Dafny Verification Failures**: Ensure Dafny is properly installed and in your system PATH.