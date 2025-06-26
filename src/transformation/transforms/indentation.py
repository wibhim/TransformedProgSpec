"""
Transformer that removes or messes up indentation.
Note: This transformation is done post-AST as indentation is a formatting concern.
"""

import re
from ..base import BaseTransformer

class ForgetIndentTransformer(BaseTransformer):
    """Transformer that removes or messes up indentation."""
    
    def __init__(self, mode='remove'):
        """Initialize with the mode of indentation transformation.
        
        Args:
            mode: Either 'remove' to remove all indentation or 'flat' for a single level.
        """
        super().__init__()
        self.transformation_name = "forget_indent"
        self.mode = mode
    
    def transform(self, code_string):
        """Override the transform method for direct string manipulation.
        
        Args:
            code_string: Original Python code as a string
            
        Returns:
            Transformed code with modified indentation
        """
        try:
            lines = code_string.split('\n')
            result_lines = []
            
            for line in lines:
                if line.strip() == '':
                    # Keep empty lines as they are
                    result_lines.append(line)
                    continue
                    
                # Remove leading spaces to get rid of indentation
                if self.mode == 'remove':
                    result_lines.append(line.lstrip())
                elif self.mode == 'flat':
                    # Add a single level of indentation (4 spaces)
                    # if the line was indented originally
                    if line[0].isspace():
                        result_lines.append('    ' + line.lstrip())
                    else:
                        result_lines.append(line)
            
            return '\n'.join(result_lines)
        except Exception as e:
            print(f"Error in {self.transformation_name} transformation: {str(e)}")
            return code_string
    
    def describe(self):
        if self.mode == 'remove':
            return "Removes all indentation from the code"
        else:
            return "Flattens indentation to a single level"
