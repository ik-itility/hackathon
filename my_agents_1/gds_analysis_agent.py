from strands import Agent
import subprocess
import os

def gds_analysis_agent(gds_file: str, drc_script: str = "/shared_workshop/my_agents/drc/photonics_drc.drc") -> str:
    """Run KLayout DRC directly on GDS file."""
    if not os.path.exists(gds_file):
        return f"Error: GDS file not found: {gds_file}"
    
    output = gds_file.replace('.gds', '_violations.txt')
    
    cmd = ['klayout', '-b', '-r', drc_script, '-rd', f'input={gds_file}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return f"KLayout error: {result.stderr}"
    
    violations = result.stdout + result.stderr
    
    if not violations.strip() or "No violations" in violations:
        return "✓ No DRC violations found"
    
    agent = Agent(
        system_prompt="""Analyze DRC violations and provide:
1. Violation count by rule
2. Root causes
3. Suggested fixes"""
    )
    
    return str(agent(f"Analyze violations:\n{violations}"))

if __name__ == "__main__":
    result = gds_analysis_agent("/shared_workshop/my_agents/gds_files/laser_with_errors_v2.gds")
    print(result)
