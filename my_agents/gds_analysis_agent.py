from strands import Agent, tool
import subprocess
import json
import os

@tool
def gds_analysis_agent(gds_file: str, drc_script: str = None) -> str:
    """Analyzes GDS files for design rule violations.
    
    Args:
        gds_file: Path to GDS file
        drc_script: Optional path to KLayout DRC script
        
    Returns:
        DRC violation report
    """
    try:
        if not os.path.exists(gds_file):
            return f"Error: GDS file not found: {gds_file}"
        
        # Run KLayout DRC check
        output_file = gds_file.replace('.gds', '_violations.lyrdb')
        
        cmd = [
            'klayout', '-b', '-r', drc_script or 'drc.drc',
            '-rd', f'input={gds_file}',
            '-rd', f'report={output_file}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"KLayout error: {result.stderr}"
        
        # Parse violations
        agent = Agent(
            system_prompt="""You are a DRC violation analysis expert.
            
Analyze the violation report and provide:
1. Total violation count by rule
2. Root cause classification
3. Suggested fixes with code locations
4. Priority ranking""",
            tools=[]
        )
        
        with open(output_file, 'r') as f:
            violations = f.read()
        
        return agent(f"Analyze these DRC violations:\n{violations}")
        
    except Exception as e:
        return f"GDS analysis error: {str(e)}"

if __name__ == "__main__":
    result = gds_analysis_agent("/shared_workshop/hackathon/nazca-scripts/laser_with_errors.gds")
    print(result)
