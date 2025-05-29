"""
Function extraction for repeated code patterns.
"""
import ast
import hashlib
from .common import BaseTransformer, get_all_variable_names

class FunctionExtractor(BaseTransformer):
    """Extracts repeated code blocks into separate functions."""
    
    def __init__(self, verbose=False, min_block_size=3):
        super().__init__()
        self.blocks = {}  # Maps hash of code blocks to their extracted function details
        self.min_block_size = min_block_size  # Minimum number of statements to extract
        self.extracted_funcs = []  # List of extracted function definitions
        self.verbose = verbose
    
    def visit_Module(self, node):
        """Process the entire module to find extractable blocks."""
        # First visit all nodes to prepare them
        self.generic_visit(node)
        
        # Then scan for extractable blocks across all functions
        for func_node in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
            blocks = self._find_extractable_blocks(func_node.body)
            if blocks:
                self._extract_blocks(blocks, func_node)
        
        # Finally, add the extracted functions to the module
        node.body = self.extracted_funcs + node.body
        return node
    
    def _find_extractable_blocks(self, body):
        """Identify code blocks that appear multiple times."""
        blocks = {}
        
        # Skip if body is too small
        if len(body) < self.min_block_size:
            return {}
            
        # Look for blocks of consecutive statements
        for i in range(len(body)):
            for size in range(self.min_block_size, min(8, len(body) - i + 1)):
                block = body[i:i+size]
                
                # Skip blocks with return statements or complex control flow
                if any(isinstance(stmt, (ast.Return, ast.Break, ast.Continue)) for stmt in block):
                    continue
                
                # Skip blocks with function or class definitions
                if any(isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) for stmt in block):
                    continue
                
                # Hash the block to check for duplicates
                block_hash = self._hash_block(block)
                
                if block_hash in blocks:
                    blocks[block_hash]["occurrences"].append((i, i+size))
                else:
                    blocks[block_hash] = {
                        "block": block,
                        "occurrences": [(i, i+size)]
                    }
        
        # Filter out blocks that don't appear multiple times
        return {k: v for k, v in blocks.items() if len(v["occurrences"]) > 1}
    
    def _hash_block(self, block):
        """Create a hash representing the structure of a code block."""
        hasher = hashlib.md5()
        for stmt in block:
            # Use the AST dump as a representation, ignoring line numbers
            dump = ast.dump(stmt, annotate_fields=False)
            hasher.update(dump.encode())
        return hasher.hexdigest()
    
    def _extract_blocks(self, blocks, parent_func):
        """Extract identified blocks into separate functions."""
        for block_hash, data in blocks.items():
            if block_hash in self.blocks:
                continue  # Already extracted
            
            block = data["block"]
            
            # Determine inputs and outputs of the block
            used_vars = set()
            defined_vars = set()
            
            for stmt in block:
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Name):
                        if isinstance(node.ctx, ast.Load):
                            used_vars.add(node.id)
                        elif isinstance(node.ctx, ast.Store):
                            defined_vars.add(node.id)
            
            # Input parameters are variables used but not defined in the block
            inputs = sorted(list(used_vars - defined_vars))
            
            # Output parameters are variables defined and then used in the block
            outputs = sorted(list(defined_vars & used_vars))
            
            # Create a function name based on parent function
            base_name = f"extracted_from_{parent_func.name}"
            func_name = f"{base_name}_{len(self.blocks) + 1}"
            
            # Create the function definition
            func_def = ast.FunctionDef(
                name=func_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=var, annotation=None) for var in inputs],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                    vararg=None,
                    kwarg=None,
                ),
                body=block + [ast.Return(
                    value=ast.Tuple(
                        elts=[ast.Name(id=var, ctx=ast.Load()) for var in outputs],
                        ctx=ast.Load()
                    )
                )] if outputs else block,
                decorator_list=[],
                returns=None
            )
            
            # Store the extracted function details
            self.blocks[block_hash] = {
                "function": func_def,
                "name": func_name,
                "inputs": inputs,
                "outputs": outputs
            }
            
            self.log_change(f"Extracted function '{func_name}' with {len(inputs)} inputs and {len(outputs)} outputs")
            
            # Add the function to be inserted into the module
            self.extracted_funcs.append(func_def)