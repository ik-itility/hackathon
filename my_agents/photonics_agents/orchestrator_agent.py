from strands import Agent
import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from violation_analysis_agent import violation_analysis_agent
from code_generation_agent import code_generation_agent

class DRCOrchestrator:
    """Orchestrates the DRC violation fixing loop."""
    
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.iteration = 0
        self.violation_history = []
        
        self.agent = Agent(
            name="DRC Orchestrator",
            system_prompt="""You are a DRC process orchestrator for photonics IC design.

Workflow:
1. Export GDS from Nazca code
2. Run KLayout DRC check
3. If violations: call violation_analysis_agent
4. Call code_generation_agent with fix brief
5. Validate and repeat
6. If stuck (no progress): escalate to human

Track violation deltas to detect convergence.""",
            tools=[violation_analysis_agent, code_generation_agent]
        )
    
    def run_drc(self, gds_file: str, drc_script: str) -> tuple:
        """Run KLayout DRC check."""
        output = gds_file.replace('.gds', '_violations.lyrdb')
        
        cmd = [
            'klayout', '-b', '-r', drc_script,
            '-rd', f'input={gds_file}',
            '-rd', f'report={output}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return False, result.stderr
        
        # Check if violations exist
        if os.path.exists(output) and os.path.getsize(output) > 0:
            return True, output
        return True, None
    
    def export_gds(self, nazca_file: str) -> str:
        """Execute Nazca script to export GDS."""
        result = subprocess.run(['python', nazca_file], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Nazca export failed: {result.stderr}")
        
        # Assume GDS file has same name
        gds_file = nazca_file.replace('.py', '.gds')
        if not os.path.exists(gds_file):
            raise Exception(f"GDS file not created: {gds_file}")
        
        return gds_file
    
    def process(self, nazca_file: str, drc_script: str):
        """Main orchestration loop."""
        print(f"Starting DRC orchestration for {nazca_file}")
        
        with open(nazca_file, 'r') as f:
            nazca_code = f.read()
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n=== Iteration {self.iteration} ===")
            
            # Export GDS
            try:
                gds_file = self.export_gds(nazca_file)
                print(f"✓ Exported: {gds_file}")
            except Exception as e:
                print(f"✗ Export failed: {e}")
                return
            
            # Run DRC
            success, result = self.run_drc(gds_file, drc_script)
            if not success:
                print(f"✗ DRC failed: {result}")
                return
            
            if result is None:
                print("✓ DRC PASSED - No violations!")
                return
            
            print(f"✗ Violations found: {result}")
            
            # Analyze violations
            fix_brief = violation_analysis_agent(result, nazca_code)
            print(f"Fix brief generated")
            
            # Generate corrected code
            corrected_code = code_generation_agent(nazca_code, str(fix_brief))
            
            # Write corrected code
            with open(nazca_file, 'w') as f:
                f.write(str(corrected_code))
            
            nazca_code = str(corrected_code)
            print(f"✓ Code updated")
        
        print(f"\n⚠ Max iterations reached. Escalating to human review.")

if __name__ == "__main__":
    orchestrator = DRCOrchestrator(max_iterations=5)
    orchestrator.process(
        nazca_file="/shared_workshop/hackathon/nazca-scripts/Laser-with-errors.py",
        drc_script="drc.drc"
    )
