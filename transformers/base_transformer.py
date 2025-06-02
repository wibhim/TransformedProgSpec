"""
Base transformer class for code transformations.
"""
import ast
from abc import ABC, abstractmethod
from typing import Any

class BaseTransformer(ABC):
    """Base class for all code transformers."""
    
    @abstractmethod
    def transform(self, code: str) -> str:
        """
        Transform the input code.
        
        Args:
            code: The original Python code string
            
        Returns:
            str: The transformed code
        """
        pass
    
    def parse_code(self, code: str) -> ast.AST:
        """
        Parse code string into AST.
        
        Args:
            code: The code string to parse
            
        Returns:
            The AST representation of the code
        """
        return ast.parse(code)
    
    def to_code(self, node: ast.AST) -> str:
        """
        Convert AST back to code string.
        
        Args:
            node: The AST to convert
            
        Returns:
            String representation of the AST
        """
        return ast.unparse(node)
