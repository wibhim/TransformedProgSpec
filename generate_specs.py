#!/usr/bin/env python
"""
Entry point for specification generation functionality.
Generates formal specifications from transformed Python code using LLMs.

Usage:
    # Generate specs from a specific dataset file
    python generate_specs.py --input dataset.json --output specs.json
    
    # Generate specs with custom prompts
    python generate_specs.py --input dataset.json --output specs.json --system-prompt prompts/my_system.txt --user-prompt prompts/my_user.txt
    
    # Generate specs using directory (input directory with JSON files)
    python generate_specs.py --input-dir data/datasets/ --output-dir data/specifications/
    
    # Override transformation type
    python generate_specs.py --input dataset.json --transformation-type remove_indent
"""
import sys
import os
import argparse
import json

# Add project directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import settings
try:
    from config.settings import CONFIG
    OUTPUT_DIR = CONFIG.get("OUTPUT_DIR", "output")
except (ImportError, KeyError):
    OUTPUT_DIR = "output"

# Import specification generator module
import src.specification.generator as spec_gen

def generate_specifications_from_file(input_file: str, output_file: str, model: str = "gpt-4", 
                                     transformation_type_override: str = None, limit: int = None, verbose: bool = False):
    """Generate specifications by temporarily modifying the generator's input."""
    
    # If transformation type override is provided, modify the input data
    if transformation_type_override:
        import json
        import tempfile
        
        # Load the input data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Override transformation_type for all items
        if isinstance(data, list):
            for item in data:
                item['transformation_type'] = transformation_type_override
        
        # Create a temporary file with the modified data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            json.dump(data, tmp_file, indent=2)
            temp_input_file = tmp_file.name
        
        if verbose:
            print(f"Override transformation_type to: {transformation_type_override}")
            print(f"Using temporary input file: {temp_input_file}")
    else:
        temp_input_file = input_file
    
    # Temporarily modify the generator's INPUT_JSON
    original_input = spec_gen.INPUT_JSON
    original_output = spec_gen.OUTPUT_JSON
    
    try:
        # Update the generator's input and output
        spec_gen.INPUT_JSON = temp_input_file
        spec_gen.OUTPUT_JSON = output_file
        
        # Note: MAX_REQUESTS is now handled dynamically in the generator
        if limit is not None:
            if verbose:
                print(f"Limiting to {limit} programs")
        
        if verbose:
            print(f"Using input: {temp_input_file}")
            print(f"Using output: {output_file}")
        
        # Call the generator function
        success = spec_gen.generate_specifications(limit=limit)
        
        return success
        
    except Exception as e:
        print(f"Error during specification generation: {e}")
        return False
    
    finally:
        # Restore original values
        spec_gen.INPUT_JSON = original_input
        spec_gen.OUTPUT_JSON = original_output
        # Note: MAX_REQUESTS is now handled dynamically, no need to restore
        
        # Clean up temporary file if created
        if transformation_type_override and temp_input_file != input_file:
            import os
            try:
                os.unlink(temp_input_file)
                if verbose:
                    print(f"Cleaned up temporary file: {temp_input_file}")
            except:
                pass  # Ignore cleanup errors

def setup_custom_prompts(args):
    """Set up custom prompt environment variables if provided."""
    if args.system_prompt:
        os.environ["SYSTEM_PROMPT_TEMPLATE"] = args.system_prompt
        print(f"📝 Using custom system prompt: {args.system_prompt}")
    
    if args.user_prompt:
        os.environ["USER_PROMPT_TEMPLATE"] = args.user_prompt
        print(f"📝 Using custom user prompt: {args.user_prompt}")

def handle_file_mode(args):
    """Handle single file input/output mode."""
    # Set up custom prompts
    setup_custom_prompts(args)
    
    # Set defaults if not provided
    if not args.input:
        args.input = os.path.join(OUTPUT_DIR, "transformed_code_dataset.json")
    
    if not args.output:
        # Generate a more specific output filename
        input_base = os.path.splitext(os.path.basename(args.input))[0]
        if args.transformation_type:
            output_filename = f"{input_base}_{args.transformation_type}_specifications.json"
        else:
            output_filename = f"{input_base}_specifications.json"
        args.output = os.path.join(OUTPUT_DIR, output_filename)
    
    # Debug: Print arguments
    if args.verbose:
        print(f"File Mode Arguments:")
        print(f"  input: {args.input}")
        print(f"  output: {args.output}")
        print(f"  model: {args.model}")
        print(f"  transformation_type: {args.transformation_type}")
    
    # Verify input file exists
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        return 1
    
    # Load the transformed code dataset
    if args.verbose:
        print(f"Loading dataset from: {args.input}")
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Handle different dataset structures (now includes verified-only JSON with 'results')
        if isinstance(raw_data, dict) and 'data' in raw_data:
            transformed_dataset = raw_data['data']
        elif isinstance(raw_data, dict) and 'programs' in raw_data:
            transformed_dataset = raw_data['programs']
        elif isinstance(raw_data, dict) and 'results' in raw_data:
            transformed_dataset = raw_data['results']
        elif isinstance(raw_data, list):
            transformed_dataset = raw_data
        else:
            # Don't block here—fallback to generator which has broader support
            transformed_dataset = []
            print(f"⚠️ Unexpected dataset structure ({type(raw_data)}). Proceeding anyway; core generator handles more shapes.")
            
        print(f"📊 Loaded {len(transformed_dataset)} items from dataset")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading input file: {e}")
        return 1
    
    # Generate specifications  
    if args.verbose:
        print(f"Generating specifications using {args.model}...")
    
    success = generate_specifications_from_file(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        transformation_type_override=args.transformation_type,
        limit=args.limit,
        verbose=args.verbose
    )
    
    if success:
        print(f"✅ Specification generation complete. Results saved to {args.output}")
        return 0
    else:
        print("❌ Specification generation failed!")
        return 1

def handle_directory_mode(args):
    """Handle directory input/output mode."""
    # Set up custom prompts
    setup_custom_prompts(args)
    
    # Verify input directory exists
    if not os.path.exists(args.input_dir):
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1
    
    # Set default output directory if not provided
    if not args.output_dir:
        args.output_dir = os.path.join(OUTPUT_DIR, "specifications")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.verbose:
        print(f"Directory Mode Arguments:")
        print(f"  input_dir: {args.input_dir}")
        print(f"  output_dir: {args.output_dir}")
        print(f"  model: {args.model}")
        print(f"  transformation_type: {args.transformation_type}")
    
    # Find all JSON files in input directory
    json_files = []
    for root, dirs, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        print(f"❌ No JSON files found in: {args.input_dir}")
        return 1
    
    print(f"📂 Found {len(json_files)} JSON files to process")
    
    # Process each file
    success_count = 0
    total_files = len(json_files)
    
    for i, input_file in enumerate(json_files, 1):
        print(f"\n[{i}/{total_files}] Processing: {os.path.basename(input_file)}")
        
        # Generate output filename
        input_base = os.path.splitext(os.path.basename(input_file))[0]
        if args.transformation_type:
            output_filename = f"{input_base}_{args.transformation_type}_specifications.json"
        else:
            output_filename = f"{input_base}_specifications.json"
        output_file = os.path.join(args.output_dir, output_filename)
        
        # Generate specifications for this file
        try:
            success = generate_specifications_from_file(
                input_file=input_file,
                output_file=output_file,
                model=args.model,
                transformation_type_override=args.transformation_type,
                limit=args.limit,
                verbose=args.verbose
            )
            
            if success:
                success_count += 1
                print(f"  ✅ Generated: {output_filename}")
            else:
                print(f"  ❌ Failed: {os.path.basename(input_file)}")
                
        except Exception as e:
            print(f"  ❌ Error processing {os.path.basename(input_file)}: {e}")
    
    # Summary
    print(f"\n📊 Directory Processing Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {total_files - success_count}")
    print(f"  Output directory: {args.output_dir}")
    
    return 0 if success_count > 0 else 1

def main():
    """Main entry point for specification generation"""
    parser = argparse.ArgumentParser(
        description="Generate formal specifications from transformed Python code"
    )
    
    # Input/Output options - file or directory mode
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", "-i", 
                        help="Input JSON file containing transformed code")
    input_group.add_argument("--input-dir", 
                        help="Input directory containing JSON dataset files")
    
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output", "-o", 
                        help="Output JSON file for specifications")
    output_group.add_argument("--output-dir", 
                        help="Output directory for specification files")
    
    # Prompt customization
    parser.add_argument("--system-prompt", 
                        help="Path to custom system prompt file")
    parser.add_argument("--user-prompt", 
                        help="Path to custom user prompt file")
    
    # Model and generation options
    parser.add_argument("--model", "-m", default="gpt-4",
                        help="Model to use for specification generation")
    
    parser.add_argument("--limit", "-l", type=int, 
                        help="Maximum number of programs to process (e.g., 50 to process only first 50 programs)")
    
    parser.add_argument("--transformation-type", "-t", 
                        help="Override transformation type in the data (e.g., 'remove_indent', 'drop_parentheses')")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    
    # Legacy positional argument support
    parser.add_argument("input_file", nargs="?", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Handle legacy usage (backward compatibility)
    if args.input_file and not args.input:
        args.input = args.input_file
    
    # Determine operation mode
    is_directory_mode = args.input_dir is not None
    
    if is_directory_mode:
        return handle_directory_mode(args)
    else:
        return handle_file_mode(args)

if __name__ == "__main__":
    sys.exit(main())
