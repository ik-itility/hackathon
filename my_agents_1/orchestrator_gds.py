#!/usr/bin/env python3
"""
Orchestrator Agent - Monitors GDS files and runs DRC correction workflow
"""

import os
import time
import subprocess
from pathlib import Path
from strands import Agent
import ast

def violation_analysis_agent(violations_text: str, nazca_code: str) -> str:
    """Analyze DRC violations from KLayout output."""
    agent = Agent(
        system_prompt="""Analyze DRC violations and output ONLY JSON array, no explanations:
[{"rule_id": "RULE1", "line_number": 15, "parameter": "spacing", "current_value": 1.5, "suggested_value": 2.0}]"""
    )
    return str(agent(f"Violations:\n{violations_text}\n\nCode:\n{nazca_code}"))

def code_generation_agent(nazca_code: str, fix_brief: str) -> str:
    """Generate corrected Nazca code based on fix brief."""
    agent = Agent(
        system_prompt="""You are a code editor. Output ONLY the corrected Python code.
No markdown blocks, no explanations, no comments about changes.
Just the complete working Python code."""
    )
    result = str(agent(f"Fix:\n{fix_brief}\n\nCode:\n{nazca_code}"))
    
    # Strip markdown
    code = result
    if '```python' in code:
        code = code.split('```python', 1)[1].split('```', 1)[0]
    elif '```' in code:
        parts = code.split('```')
        if len(parts) >= 3:
            code = parts[1]
    
    code = code.strip()
    
    try:
        ast.parse(code)
        return code
    except SyntaxError:
        return nazca_code  # Return original if fix failed

class GDSOrchestrator:
    def __init__(self):
        self.gds_dir = Path("/shared_workshop/my_agents/gds_files")
        self.drc_script = Path("/shared_workshop/my_agents/drc/photonics_drc.drc")
        self.tmp_dir = Path("/shared_workshop/my_agents/tmp")
        self.source_dir = Path("/shared_workshop/my_agents/gds_source_py")
        self.tmp_dir.mkdir(exist_ok=True)
        self.source_dir.mkdir(exist_ok=True)
        self.processed = set()
        
    def run_drc(self, gds_file):
        """Run KLayout DRC directly on GDS file"""
        report_file = str(self.tmp_dir / f"{gds_file.stem}_violations.lyrdb")
        
        cmd = ['klayout', '-b', '-r', str(self.drc_script), 
               '-rd', f'input={gds_file}',
               '-rd', f'report={report_file}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return None, None
        
        violations = result.stdout + result.stderr
        return violations if violations.strip() else None, report_file if violations.strip() else None
    
    def generate_python_from_gds(self, gds_file):
        """Generate Python source code from GDS using AI"""
        agent = Agent(
            system_prompt="""Output ONLY Nazca Python code, no markdown, no explanations.
Generate code that recreates the GDS layout."""
        )
        
        # Get GDS layer info
        inspect_script = self.tmp_dir / "inspect.drc"
        with open(inspect_script, 'w') as f:
            f.write("""source($input)
(0..200).each do |l|
  (0..10).each do |d|
    layer = input(l, d)
    puts "Layer #{l}/#{d}" unless layer.is_empty?
  end
end""")
        
        result = subprocess.run(
            ['klayout', '-b', '-r', str(inspect_script), '-rd', f'input={gds_file}'],
            capture_output=True, text=True
        )
        
        layers = [line.strip() for line in result.stdout.split('\n') if 'Layer' in line]
        
        query = f"""Generate Nazca code for {gds_file.name}\nLayers: {', '.join(layers)}\nUse nd.Polygon() and .put() with y-spacing."""
        
        code = str(agent(query))
        
        # Strip markdown if present
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()
        
        return code
    
    def find_nazca_source(self, gds_file):
        """Find or generate Nazca Python source"""
        source_file = self.source_dir / f"{gds_file.stem}.py"
        if source_file.exists():
            return str(source_file)
        
        code = self.generate_python_from_gds(gds_file)
        
        with open(source_file, 'w') as f:
            f.write(code)
        
        return str(source_file)
    
    def process_gds(self, gds_file):
        """Process a single GDS file"""
        print(f"\n{gds_file.name}:")
        
        violations, report_file = self.run_drc(gds_file)
        
        if not violations:
            print("  0 violations")
            return
        
        # Parse and display violations
        violation_lines = [line for line in violations.split('\n') if 'violations' in line]
        total = sum(int(line.split(' - ')[1].split()[0]) for line in violation_lines if ' - ' in line)
        print(f"  {total} violations")
        
        for line in violation_lines:
            if ' - ' in line:
                rule_desc = line.split(': ', 1)[1] if ': ' in line else line
                print(f"    • {rule_desc}")
        
        if report_file:
            print(f"  → {report_file}")
    
    def watch(self):
        """Watch for new GDS files"""
        print("GDS DRC Monitor")
        print(f"Folder: {self.gds_dir}\n")
        
        try:
            while True:
                gds_files = list(self.gds_dir.glob('*.gds'))
                
                for gds_file in gds_files:
                    if gds_file not in self.processed:
                        self.processed.add(gds_file)
                        self.process_gds(gds_file)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\nStopped")

if __name__ == "__main__":
    orchestrator = GDSOrchestrator()
    orchestrator.watch()
