"""
Template Engine - Handles dynamic variable replacement (GMass-style placeholders)
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from jinja2 import Template, TemplateError

logger = logging.getLogger(__name__)


class TemplateProcessor:
    """Processes email templates with dynamic variable replacement"""
    
    # Support both {Variable} and {{Variable}} syntax
    VARIABLE_PATTERN = re.compile(r'\{\{?(\w+)\}?\}')
    
    def __init__(self, default_variables: Optional[Dict[str, Any]] = None):
        """
        Initialize template processor
        
        Args:
            default_variables: Default variables available to all templates
        """
        self.default_variables = default_variables or {}
    
    def extract_variables(self, template: str) -> set:
        """Extract all variable names from a template"""
        variables = set()
        for match in self.VARIABLE_PATTERN.finditer(template):
            variables.add(match.group(1))
        return variables
    
    def render(self, template: str, variables: Dict[str, Any], 
               use_jinja: bool = True) -> str:
        """
        Render a template with provided variables
        
        Args:
            template: Template string with placeholders like {FirstName}, {City}
            variables: Dictionary of variable values
            use_jinja: Whether to use Jinja2 for advanced templating (default: True)
        
        Returns:
            Rendered template string
        """
        # Merge default variables with provided variables
        all_variables = {**self.default_variables, **variables}
        
        if use_jinja:
            try:
                # Convert {Variable} syntax to {{Variable}} for Jinja2
                jinja_template = self._convert_to_jinja(template)
                jinja_obj = Template(jinja_template)
                return jinja_obj.render(**all_variables)
            except TemplateError as e:
                logger.warning(f"Jinja2 rendering failed, falling back to simple replacement: {str(e)}")
                # Fall back to simple replacement
                return self._simple_replace(template, all_variables)
        else:
            return self._simple_replace(template, all_variables)
    
    def _convert_to_jinja(self, template: str) -> str:
        """Convert {Variable} syntax to {{Variable}} for Jinja2"""
        # Replace {Variable} with {{Variable}}
        def replace_var(match):
            var_name = match.group(1)
            return f"{{{{{var_name}}}}}"
        
        return self.VARIABLE_PATTERN.sub(replace_var, template)
    
    def _simple_replace(self, template: str, variables: Dict[str, Any]) -> str:
        """Simple variable replacement without Jinja2"""
        result = template
        
        # Replace {Variable} and {{Variable}} with actual values
        def replace_var(match):
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))  # Keep original if not found
            return str(value) if value is not None else ""
        
        result = self.VARIABLE_PATTERN.sub(replace_var, result)
        return result
    
    def validate_template(self, template: str, required_variables: Optional[set] = None) -> Tuple[bool, List[str]]:
        """
        Validate that a template has all required variables
        
        Returns:
            (is_valid, missing_variables)
        """
        template_vars = self.extract_variables(template)
        
        if required_variables is None:
            return True, []
        
        missing = required_variables - template_vars
        return len(missing) == 0, list(missing)
    
    def get_rendered_subject(self, subject_template: str, variables: Dict[str, Any]) -> str:
        """Render email subject with variables"""
        return self.render(subject_template, variables)
    
    def get_rendered_body(self, body_template: str, variables: Dict[str, Any]) -> str:
        """Render email body with variables"""
        return self.render(body_template, variables)
    
    def get_rendered_html(self, html_template: str, variables: Dict[str, Any]) -> str:
        """Render HTML email body with variables"""
        return self.render(html_template, variables)

