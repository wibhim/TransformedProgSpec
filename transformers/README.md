# Transformers Package Documentation

This package provides tools for transforming Python code to improve formal specification generation. It contains several modules that each handle specific transformation tasks.

## Modules Overview

- **pipeline.py**: Orchestrates the transformation process
- **control_flow.py**: Simplifies control flow structures
- **variable_naming.py**: Standardizes variable naming conventions
- **expression_decomp.py**: Decomposes complex expressions into simpler ones
- **loop_standard.py**: Standardizes loop structures
- **function_extract.py**: Extracts inline code into separate functions

## Usage

The main entry point for transformations is the `transform_code` function from the package root:

```python
from transformers import transform_code

transformed_code = transform_code(original_code)
```

For dataset processing, use the `process_dataset` function.

## Transformation Process

The transformation pipeline applies the following transformations in sequence:

1. Control flow simplification
2. Variable renaming standardization
3. Expression decomposition
4. Loop structure standardization
5. Function extraction

Each step prepares the code for better formal specification generation.
