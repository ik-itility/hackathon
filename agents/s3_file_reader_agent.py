"""Agent 1: S3 File Reader - Triggered by S3 upload events"""
import boto3
import json
from typing import Dict, Any

class S3FileReaderAgent:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def process_s3_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process S3 event and read Python file"""
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        if not key.endswith('.py'):
            return {'status': 'skipped', 'reason': 'Not a Python file'}
        
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        code_content = response['Body'].read().decode('utf-8')
        
        return {
            'status': 'success',
            'bucket': bucket,
            'key': key,
            'code': code_content,
            'trigger_validation': True
        }

if __name__ == '__main__':
    # Simulate S3 event
    sample_event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'my-code-bucket'},
                'object': {'key': 'uploads/sample.py'}
            }
        }]
    }
    
    agent = S3FileReaderAgent()
    result = agent.process_s3_event(sample_event)
    print(json.dumps(result, indent=2))
