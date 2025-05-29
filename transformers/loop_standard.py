"""
Loop standardization for consistent loop patterns.
"""
import ast
from .common import BaseTransformer, parent_child_map

class LoopStandardizer(BaseTransformer):
    """Standardizes loops to a consistent format."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose
    
    def visit_Module(self, node):
        """Set up parent references for the whole tree."""
        self.parent_map = parent_child_map(node)
        return self.generic_visit(node)
    
    def visit_While(self, node):
        """Convert while loops to for loops when possible."""
        self.generic_visit(node)
        
        # Try to get the parent node
        parent = self.parent_map.get(node)
        if not parent or not isinstance(parent, ast.FunctionDef):
            return node
        
        # Find the index of this while loop in the parent's body
        try:
            idx = parent.body.index(node)
            if idx == 0:  # No previous statement
                return node
        except ValueError:
            return node
        
        # Check if the previous statement is a variable assignment
        prev = parent.body[idx-1]
        if not isinstance(prev, ast.Assign) or not len(prev.targets) == 1:
            return node
        
        # Check if the assignment is to a single variable
        if not isinstance(prev.targets[0], ast.Name):
            return node
        
        var_name = prev.targets[0].id
        
        # Check if while condition is a comparison involving this variable
        if not isinstance(node.test, ast.Compare):
            return node
        
        # Check if the loop variable is incremented inside the loop
        increment_found = False
        end_value = None
        
        # Look for pattern like "i < 10" or "i <= 10"
        if (isinstance(node.test.left, ast.Name) and node.test.left.id == var_name and
            len(node.test.ops) == 1 and isinstance(node.test.ops[0], (ast.Lt, ast.LtE)) and
            len(node.test.comparators) == 1 and isinstance(node.test.comparators[0], (ast.Constant, ast.Num))):
            end_value = node.test.comparators[0]
            
            # Look for "i += 1" or "i = i + 1" pattern at the end of the loop
            for stmt in node.body:
                if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                    if (isinstance(stmt.target, ast.Name) and 
                        stmt.target.id == var_name and 
                        isinstance(stmt.value, ast.Constant) and 
                        stmt.value.value == 1):
                        increment_found = True
                        break
                elif isinstance(stmt, ast.Assign):
                    if (isinstance(stmt.targets[0], ast.Name) and 
                        stmt.targets[0].id == var_name and 
                        isinstance(stmt.value, ast.BinOp) and 
                        isinstance(stmt.value.op, ast.Add) and 
                        isinstance(stmt.value.left, ast.Name) and 
                        stmt.value.left.id == var_name and 
                        isinstance(stmt.value.right, ast.Constant) and 
                        stmt.value.right.value == 1):
                        increment_found = True
                        break
        
        if increment_found and end_value:
            # Create a range object for the for loop
            range_call = ast.Call(
                func=ast.Name(id='range', ctx=ast.Load()),
                args=[
                    prev.value,  # Start value
                    end_value,   # End value
                    ast.Constant(value=1)  # Step
                ],
                keywords=[]
            )
            
            # Create the for loop
            for_node = ast.For(
                target=ast.Name(id=var_name, ctx=ast.Store()),
                iter=range_call,
                body=[stmt for stmt in node.body if not self._is_increment(stmt, var_name)],
                orelse=node.orelse,
                lineno=node.lineno
            )
            
            self.log_change(f"Converted while loop with counter to for loop using '{var_name}'")
            # Return the for loop without the initialization statement
            return for_node
        
        return node
    
    def _is_increment(self, stmt, var_name):
        """Check if a statement is incrementing the specified variable."""
        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
            return (isinstance(stmt.target, ast.Name) and 
                    stmt.target.id == var_name and 
                    isinstance(stmt.value, ast.Constant) and 
                    stmt.value.value == 1)
        elif isinstance(stmt, ast.Assign):
            return (isinstance(stmt.targets[0], ast.Name) and 
                    stmt.targets[0].id == var_name and 
                    isinstance(stmt.value, ast.BinOp) and 
                    isinstance(stmt.value.op, ast.Add) and 
                    isinstance(stmt.value.left, ast.Name) and 
                    stmt.value.left.id == var_name and 
                    isinstance(stmt.value.right, ast.Constant) and 
                    stmt.value.right.value == 1)
        return False