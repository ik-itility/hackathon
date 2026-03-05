"""Agent 3: Code Fixer - Fixes code errors using AI"""
import boto3
import json
from typing import Dict, Any

class CodeFixerAgent:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    def fix_code(self, code: str, errors: list, filename: str) -> Dict[str, Any]:
        """Fix code errors using Bedrock"""
        prompt = f"""Fix the following Python code based on these errors:

Errors:
{chr(10).join(f"- {e}" for e in errors)}

Original Code:
```python
{code}
```

Provide ONLY the fixed code without explanations."""

        response = self.bedrock.invoke_model(
            modelId='us.anthropic.claude-sonnet-4-5-v2:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        fixed_code = result['content'][0]['text']
        
        # Extract code from markdown if present
        if '```python' in fixed_code:
            fixed_code = fixed_code.split('```python')[1].split('```')[0].strip()
        
        return {
            'filename': filename,
            'original_code': code,
            'fixed_code': fixed_code,
            'requires_approval': True
        }

if __name__ == '__main__':
    sample_code = "def calc(a, b):\n    return a + b"
    sample_errors = ["Function 'calc' missing docstring", "Missing type hints"]
    
    agent = CodeFixerAgent()
    result = agent.fix_code(sample_code, sample_errors, 'sample.py')
    print(json.dumps(result, indent=2))
