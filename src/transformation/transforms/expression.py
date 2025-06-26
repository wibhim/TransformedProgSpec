"""
Expression decomposition for simplifying complex expressions.
"""
import ast
from ..base import BaseTransformer

class ExpressionDecomposer(BaseTransformer):
    """Decomposes complex expressions into simpler ones with meaningful names."""
    
    def __init__(self, verbose=False):
        super().__init__()
        self.counter = 0
        self.decomposed = set()  # Track already decomposed expressions
        self.verbose = verbose
    
    def get_name_for_expr(self, expr):
        """Generates a meaningful name based on expression type."""
        if isinstance(expr, ast.BinOp):
            if isinstance(expr.op, ast.Add):
                return "sum_value"
            elif isinstance(expr.op, ast.Sub):
                return "diff_value"
            elif isinstance(expr.op, ast.Mult):
                return "product"
            elif isinstance(expr.op, ast.Div):
                return "quotient"
            elif isinstance(expr.op, ast.Mod):
                return "remainder"
            
            # For length calculations like (end - start + 1)
            if (isinstance(expr.op, ast.Add) and 
                isinstance(expr.left, ast.BinOp) and 
                isinstance(expr.left.op, ast.Sub) and
                isinstance(expr.right, ast.Constant) and 
                expr.right.value == 1):
                return "length"
        
        # For array indexing and slicing
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.value, ast.Name):
                return f"{expr.value.id}_item"
            return "item"
            
        # For function calls
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                return f"{expr.func.id}_result"
            return "result"
            
        # Default case
        self.counter += 1
        return f"temp_{self.counter}"
    
    def should_decompose(self, expr):
        """Determines if an expression is complex enough to decompose."""
        # Decompose binary operations with at least one complex operand
        if isinstance(expr, ast.BinOp):
            # Count operand complexity
            complexity = 0
            for subexpr in [expr.left, expr.right]:
                if isinstance(subexpr, (ast.BinOp, ast.Call, ast.Subscript)):
                    complexity += 1
                elif isinstance(subexpr, ast.Compare) and len(subexpr.ops) > 1:
                    complexity += 1
            return complexity > 0
            
        # Decompose complex calls with complex arguments
        if isinstance(expr, ast.Call):
            for arg in expr.args:
                if isinstance(arg, (ast.BinOp, ast.Call, ast.Subscript)):
                    return True
                    
        # Decompose complex subscripts
        if isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.BinOp):
            return True
            
        return False
    
    def visit_Assign(self, node):
        """Decompose complex expressions in assignments."""
        self.generic_visit(node)
        
        # Check if the value is a complex expression that should be decomposed
        if self.should_decompose(node.value) and id(node.value) not in self.decomposed:
            self.decomposed.add(id(node.value))
            
            # Create a new variable name based on the expression
            new_name = self.get_name_for_expr(node.value)
            
            # Create an assignment for the decomposed expression
            new_assign = ast.Assign(
                targets=[ast.Name(id=new_name, ctx=ast.Store())],
                value=node.value,
                lineno=node.lineno
            )
            
            # Replace the original expression with the new variable
            node.value = ast.Name(id=new_name, ctx=ast.Load())
            
            self.log_change(f"Decomposed complex expression into variable '{new_name}'")
            return [new_assign, node]
        
        return node
    
    def visit_Call(self, node):
        """Decompose complex expressions in function call arguments."""
        self.generic_visit(node)
        
        new_nodes = []
        for i, arg in enumerate(node.args):
            if self.should_decompose(arg) and id(arg) not in self.decomposed:
                self.decomposed.add(id(arg))
                
                # Create a new variable name based on the expression
                new_name = self.get_name_for_expr(arg)
                
                # Create an assignment for the decomposed expression
                new_assign = ast.Assign(
                    targets=[ast.Name(id=new_name, ctx=ast.Store())],
                    value=arg,
                    lineno=node.lineno
                )
                new_nodes.append(new_assign)
                
                # Replace the argument with the new variable
                node.args[i] = ast.Name(id=new_name, ctx=ast.Load())
                self.log_change(f"Decomposed complex argument into variable '{new_name}'")
        
        if new_nodes:
            new_nodes.append(node)
            return new_nodes
        
        return node