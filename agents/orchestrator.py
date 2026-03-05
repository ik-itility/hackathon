"""Orchestrator: Coordinates the three agents with manual approval"""
import json
from s3_file_reader_agent import S3FileReaderAgent
from code_validator_agent import CodeValidatorAgent
from code_fixer_agent import CodeFixerAgent

class Orchestrator:
    def __init__(self):
        self.reader = S3FileReaderAgent()
        self.validator = CodeValidatorAgent()
        self.fixer = CodeFixerAgent()
    
    def process_workflow(self, s3_event: dict) -> dict:
        """Execute the three-agent workflow"""
        print("=== STEP 1: Reading file from S3 ===")
        read_result = self.reader.process_s3_event(s3_event)
        print(json.dumps(read_result, indent=2))
        
        if read_result['status'] != 'success':
            return read_result
        
        print("\n=== STEP 2: Validating code ===")
        validation_result = self.validator.validate_code(
            read_result['code'], 
            read_result['key']
        )
        print(json.dumps(validation_result, indent=2))
        
        if validation_result['valid']:
            print("\n✓ Code is valid!")
            return {'status': 'complete', 'action': 'none'}
        
        print("\n=== STEP 3: Fixing code ===")
        fix_result = self.fixer.fix_code(
            read_result['code'],
            validation_result['errors'],
            read_result['key']
        )
        
        print("\n=== MANUAL APPROVAL REQUIRED ===")
        print(f"\nOriginal Code:\n{fix_result['original_code']}")
        print(f"\nFixed Code:\n{fix_result['fixed_code']}")
        
        approval = input("\nApprove changes? (yes/no): ").strip().lower()
        
        if approval == 'yes':
            print("\n✓ Changes approved and applied")
            return {'status': 'complete', 'action': 'fixed', 'result': fix_result}
        else:
            print("\n✗ Changes rejected")
            return {'status': 'complete', 'action': 'rejected'}

if __name__ == '__main__':
    # Simulate S3 event
    event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'my-code-bucket'},
                'object': {'key': 'uploads/test.py'}
            }
        }]
    }
    
    orchestrator = Orchestrator()
    result = orchestrator.process_workflow(event)
    print(f"\n=== FINAL RESULT ===\n{json.dumps(result, indent=2)}")
