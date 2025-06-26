"""
Template Manager for Specification Generation

This module provides functionality for loading, managing, and applying
templates for specification generation prompts.
"""

import os
from config.settings import CONFIG

class TemplateManager:
    """
    Manages templates for specification generation prompts.
    
    Handles loading templates from files, selecting appropriate templates
    based on criteria, and rendering templates with context variables.
    """
    
    def __init__(self, templates_dir=None):
        """
        Initialize the template manager.
        
        Args:
            templates_dir (str, optional): Directory containing template files.
                Defaults to the templates directory in config.
        """
        if templates_dir is None:
            self.templates_dir = os.path.join(CONFIG["BASE_DIR"], "config", "templates")
        else:
            self.templates_dir = templates_dir
            
        self.templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load all template files from the templates directory."""
        if not os.path.exists(self.templates_dir):
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
            
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".txt"):
                template_name = os.path.splitext(filename)[0]  # Remove .txt extension
                self.load_template(template_name)
    
    def load_template(self, name):
        """
        Load a template by name from the templates directory.
        
        Args:
            name (str): Name of the template file (without .txt extension)
            
        Returns:
            bool: True if template was loaded successfully, False otherwise
        """
        template_path = os.path.join(self.templates_dir, f"{name}.txt")
        
        if not os.path.exists(template_path):
            print(f"⚠️ Template file not found: {template_path}")
            return False
            
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
                
            self.templates[name] = template_content
            return True
            
        except Exception as e:
            print(f"❌ Error loading template {name}: {e}")
            return False
    
    def get_template(self, name):
        """
        Get a template by name.
        
        Args:
            name (str): Name of the template
            
        Returns:
            str: Template content, or None if not found
        """
        return self.templates.get(name)
    
    def render_template(self, name, context=None):
        """
        Render a template with context variables.
        
        Args:
            name (str): Name of the template
            context (dict, optional): Dictionary of variables to substitute
            
        Returns:
            str: The rendered template, or None if template not found
        """
        template = self.get_template(name)
        
        if template is None:
            return None
            
        if context is None:
            return template
            
        # Simple string substitution
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            template = template.replace(placeholder, str(value))
            
        return template
    
    def list_available_templates(self):
        """
        List all available templates.
        
        Returns:
            list: List of template names
        """
        return list(self.templates.keys())