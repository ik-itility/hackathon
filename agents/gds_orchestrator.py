"""Orchestrator: GDS Photonics Mask Validation System"""
import json
from gds_file_reader_agent import GDSFileReaderAgent
from gds_validator_agent import GDSValidatorAgent
from gds_fixer_agent import GDSFixerAgent

class GDSOrchestrator:
    def __init__(self):
        self.reader = GDSFileReaderAgent()
        self.validator = GDSValidatorAgent()
        self.fixer = GDSFixerAgent()
    
    def process_workflow(self, s3_event: dict) -> dict:
        """Execute GDS validation workflow"""
        print("=== STEP 1: Reading GDS file from S3 ===")
        read_result = self.reader.process_s3_event(s3_event)
        print(f"Status: {read_result['status']}")
        print(f"Cells: {len(read_result.get('cells', []))}")
        
        if read_result['status'] != 'success':
            return read_result
        
        print("\n=== STEP 2: Validating photonics design rules ===")
        validation_result = self.validator.validate_gds(
            read_result, 
            read_result['key']
        )
        print(f"Valid: {validation_result['valid']}")
        print(f"Errors: {len(validation_result['errors'])}")
        
        if validation_result['valid']:
            print("\n✓ GDS passes all design rules!")
            return {'status': 'complete', 'action': 'none'}
        
        print("\n=== STEP 3: Generating fixes ===")
        for error in validation_result['errors']:
            print(f"  - {error}")
        
        fix_result = self.fixer.fix_gds(
            read_result,
            validation_result['errors'],
            read_result['key']
        )
        
        print("\n=== MANUAL APPROVAL REQUIRED ===")
        print(f"\nFix Recommendations:\n{fix_result['fix_recommendations']}")
        
        approval = input("\nApprove fixes? (yes/no): ").strip().lower()
        
        if approval == 'yes':
            print("\n✓ Fixes approved")
            return {'status': 'complete', 'action': 'fixed', 'result': fix_result}
        else:
            print("\n✗ Fixes rejected")
            return {'status': 'complete', 'action': 'rejected'}

if __name__ == '__main__':
    event = {
        'Records': [{
            's3': {
                'bucket': {'name': 'photonics-mask-bucket'},
                'object': {'key': 'uploads/waveguide.gds'}
            }
        }]
    }
    
    orchestrator = GDSOrchestrator()
    result = orchestrator.process_workflow(event)
    print(f"\n=== FINAL RESULT ===\n{json.dumps(result, indent=2)}")
