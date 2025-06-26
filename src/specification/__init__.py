"""
Specification Generation Module

This module handles the generation of formal specifications for Python code,
using various methods including ChatGPT API calls.

The specification module contains:
- Generator: The core component for generating specifications
- Templates: Management of specification prompt templates
"""

from .generator import generate_specifications, get_cached_specification, cache_specification
from .templates import TemplateManager

__all__ = [
    'generate_specifications',
    'get_cached_specification', 
    'cache_specification',
    'TemplateManager'
]