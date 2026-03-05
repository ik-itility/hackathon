"""Agent 2: Code Validator - Validates code against rules"""
import re
import ast
from typing import Dict, List, Any

class CodeValidatorAgent:
    def __init__(self, rules_file: str = '/workshop/hackathon/data/rules.txt'):
        self.rules = self._load_rules(rules_file)
    
    def _load_rules(self, filepath: str) -> List[str]:
        """Load validation rules from file"""
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    def validate_code(self, code: str, filename: str) -> Dict[str, Any]:
        """Validate code against rules"""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            # Check for docstrings
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        errors.append(f"Function '{node.name}' missing docstring (line {node.lineno})")
                    
                    # Check type hints
                    if not node.returns:
                        errors.append(f"Function '{node.name}' missing return type hint (line {node.lineno})")
            
            # Check for short variable names
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and len(node.id) < 3 and node.id not in ['i', 'j', 'k', 'x', 'y', 'z']:
                    errors.append(f"Variable '{node.id}' name too short")
            
            # Check for hardcoded secrets
            if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
                errors.append("Hardcoded credentials detected")
        
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        
        return {
            'filename': filename,
            'valid': len(errors) == 0,
            'errors': errors,
            'trigger_fix': len(errors) > 0
        }

if __name__ == '__main__':
    sample_code = """
def calc(a, b):
    x = a + b
    return x
"""
    agent = CodeValidatorAgent()
    result = agent.validate_code(sample_code, 'sample.py')
    print(result)
