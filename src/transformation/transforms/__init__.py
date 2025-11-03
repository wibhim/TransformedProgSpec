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
from .replace_parentheses import ReplaceParenthesesTransformer
from .indentation import ForgetIndentTransformer
from .exceptions import RemoveExceptionsTransformer
from .print import RemovePrintTransformer
from .else_transform import RemoveElseTransformer
from .docstrings import RemoveDocstringsTransformer
from .log_statement import LogStatementTransformer
from .loop_exchange import LoopExchangeTransformer
from .permute_statement import PermuteStatementTransformer
from .reorder_condition import ReorderConditionTransformer
from .try_catch_insertion import TryCatchInsertionTransformer
from .dead_code_insertion import DeadCodeInsertionTransformer
from .boolean_exchange import BooleanExchangeTransformer
from .switch_to_if import SwitchToIfTransformer
from .if_normalize import IfNormalizeTransformer
from .if_invert import IfInvertConditionTransformer

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
    "remove_indent": ForgetIndentTransformer,  # Alias for forget_indent
    "remove_exceptions": RemoveExceptionsTransformer,
    "remove_print": RemovePrintTransformer,
    "remove_else": RemoveElseTransformer,
    "remove_docstrings": RemoveDocstringsTransformer
    ,
    # Newly added transformations
    "log_statement": LogStatementTransformer,
    "loop_exchange": LoopExchangeTransformer,
    "permute_statement": PermuteStatementTransformer,
    "reorder_condition": ReorderConditionTransformer,
    "try_catch_insertion": TryCatchInsertionTransformer,
    "dead_code_insertion": DeadCodeInsertionTransformer,
    "boolean_exchange": BooleanExchangeTransformer,
    "switch_to_if": SwitchToIfTransformer,
    "if_normalize": IfNormalizeTransformer,
    # If-condition inversion (branch swap)
    "if_invert_condition": IfInvertConditionTransformer,
    # Short alias
    "if_invert": IfInvertConditionTransformer,
}

# String-only transformers applied after AST transforms and final unparse.
# These must not be reparsed and may produce invalid Python.
STRING_TRANSFORMERS = {
    "replace_parentheses",
    "remove_indent",
    "forget_indent",
}
