#!/usr/bin/env python
"""
Simple test for selective transformations
"""
import sys
import os
import ast
import astor

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import transformers directly
from src.transformation.transforms.comments import DropCommentsTransformer
from src.transformation.transforms.print import RemovePrintTransformer

# Sample code to transform
test_code = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

# Calculate factorial of 5
result = factorial(5)
print("Factorial of 5 is:", result)
"""

def test_selective_transforms():
    """Test applying transformers selectively"""
    
    print("Original code:")
    print(test_code)
    print("-" * 40)
    
    # Parse the AST
    tree = ast.parse(test_code)
    
    # Apply drop comments transformer
    print("\nApplying DropCommentsTransformer:")
    drop_comments = DropCommentsTransformer()
    tree_no_comments = drop_comments.visit(tree)
    ast.fix_missing_locations(tree_no_comments)
    code_no_comments = astor.to_source(tree_no_comments)
    print(code_no_comments)
    print("-" * 40)
    
    # Apply remove print transformer
    print("\nApplying RemovePrintTransformer:")
    remove_print = RemovePrintTransformer()
    tree_no_prints = remove_print.visit(ast.parse(test_code))  # Start with original
    ast.fix_missing_locations(tree_no_prints)
    code_no_prints = astor.to_source(tree_no_prints)
    print(code_no_prints)
    print("-" * 40)
    
    # Apply both transformers sequentially
    print("\nApplying both transformers:")
    tree_combined = ast.parse(test_code)
    tree_combined = drop_comments.visit(tree_combined)
    ast.fix_missing_locations(tree_combined)
    tree_combined = remove_print.visit(tree_combined)
    ast.fix_missing_locations(tree_combined)
    code_combined = astor.to_source(tree_combined)
    print(code_combined)
    
    print("\nTest completed. You should see the comments and print statements removed in the final version.")

if __name__ == "__main__":
    test_selective_transforms()
