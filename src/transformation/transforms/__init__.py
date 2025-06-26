"""
Initialization file for the transformations module.
Import all transformers here to make them available through the module.
"""

from ..base import BaseTransformer
# Core transformers
from .control_flow import ControlFlowSimplifier
from .variable_naming import VariableRenamer
from .expression import ExpressionDecomposer
from .loop_standard import LoopStandardizer
from .function_extract import FunctionExtractor

# Additional transformers
from .comments import DropCommentsTransformer
from .self import DropSelfTransformer
from .path import DropPathTransformer
from .returns import DropReturnTransformer
from .drop_vars import DropVarsTransformer
from .parentheses import ReplaceParenthesesTransformer
from .indentation import ForgetIndentTransformer
from .exceptions import RemoveExceptionsTransformer
from .print import RemovePrintTransformer
from .else_transform import RemoveElseTransformer

# Dictionary mapping transformation names to their classes
TRANSFORMERS = {
    # Core transformers (now selectable individually)
    "control_flow": ControlFlowSimplifier,
    "variable_naming": VariableRenamer,
    "expression": ExpressionDecomposer,
    "loop_standard": LoopStandardizer,
    "function_extract": FunctionExtractor,
    
    # Additional transformers
    "drop_comments": DropCommentsTransformer,
    "drop_self": DropSelfTransformer,
    "drop_path": DropPathTransformer,
    "drop_return": DropReturnTransformer,
    "drop_vars": DropVarsTransformer,
    "replace_parentheses": ReplaceParenthesesTransformer,
    "forget_indent": ForgetIndentTransformer,
    "remove_exceptions": RemoveExceptionsTransformer,
    "remove_print": RemovePrintTransformer,
    "remove_else": RemoveElseTransformer
}
