## Components

- **test_github_token.py**: Take some program with .py extension from github and save it as JSON file. Change GITHUB_TOKEN, TARGET_REPO, OUTPUT_JSON according your need.
- **cleanup.py**: Removes any docstring and comments inside the code.
- **transform_final.py**: Enhanced transformer that preserves variable names
- **chatgpt.py**: Generates formal specifications for transformed code using OpenAI's API. Need to create your own OpenAI's API and save it as .txt file. Generated result will be saved as JSON.
- **dafny.py**: Autimatically check the generated specification into Dafny. Result is saved in output/dafny_verification_results.json

The ouput file name and location can be renamed according to your needs.
