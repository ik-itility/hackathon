#!/usr/bin/env python3
"""
Orchestrator Agent - Monitors GDS files and runs DRC correction workflow
"""

import os
import sys
import time
import subprocess
from pathlib import Path

sys.path.insert(0, '/shared_workshop/my_agents/photonics_agents')
from violation_analysis_agent import violation_analysis_agent
from code_generation_agent import code_generation_agent

class GDSOrchestrator:
    def __init__(self):
        self.gds_dir = Path("/shared_workshop/my_agents/gds_files")
        self.drc_script = Path("/shared_workshop/my_agents/drc/photonics_drc.drc")
        self.tmp_dir = Path("/shared_workshop/my_agents/tmp")
        self.tmp_dir.mkdir(exist_ok=True)
        self.processed = set()
        
    def run_drc(self, gds_file):
        """Run KLayout DRC check"""
        output = str(self.tmp_dir / f"{gds_file.stem}_violations.lyrdb")
        
        cmd = [
            'klayout', '-b', '-r', str(self.drc_script),
            '-rd', f'input={gds_file}',
            '-rd', f'report={output}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ DRC failed: {result.stderr}")
            return None
        
        # KLayout only creates report if violations found
        # If no file exists, run AI analysis on GDS directly
        if os.path.exists(output):
            return output
        
        # No violations file - use AI to analyze GDS structure
        print("No DRC violations file created - analyzing GDS with AI...")
        return "AI_ANALYSIS"
    
    def find_nazca_source(self, gds_file):
        """Find corresponding Nazca Python file"""
        # First check same directory with same name
        py_file = str(gds_file).replace('.gds', '.py')
        if os.path.exists(py_file):
            return py_file
        
        # Check in hackathon/nazca-scripts directory
        nazca_scripts = Path("/shared_workshop/hackathon/nazca-scripts")
        if nazca_scripts.exists():
            py_files = list(nazca_scripts.glob(f"{gds_file.stem}*.py"))
            if py_files:
                return str(py_files[0])
        
        # Search parent directories
        for parent in gds_file.parents:
            py_files = list(parent.glob(f"{gds_file.stem}*.py"))
            if py_files:
                return str(py_files[0])
        
        return None
    
    def process_gds(self, gds_file):
        """Process a single GDS file"""
        print(f"\n{'='*80}")
        print(f"Processing: {gds_file.name}")
        print(f"{'='*80}")
        
        # Run DRC
        print("Running DRC check...")
        violations = self.run_drc(gds_file)
        
        if violations == "AI_ANALYSIS":
            print("✓ DRC passed - running AI analysis...")
            
            # Read Nazca source if available
            nazca_file = self.find_nazca_source(gds_file)
            if not nazca_file:
                print("⚠ No source file found")
                return
            
            nazca_code = ""
            with open(nazca_file, 'r') as f:
                nazca_code = f.read()
            
            # Use Strands Agent directly for analysis
            from strands import Agent
            import json
            
            agent = Agent(
                system_prompt="""Analyze Nazca code for violations. Output ONLY JSON:
{"violations": [{"line": N, "issue": "description", "fix": "suggestion"}]}""",
                tools=[]
            )
            
            analysis = agent(f"Analyze for spacing/overlap violations:\n{nazca_code}")
            
            # Extract violations summary
            try:
                result = json.loads(str(analysis))
                violations = result.get('violations', [])
                print(f"\n✗ Found {len(violations)} violation(s):")
                for v in violations:
                    print(f"  Line {v.get('line')}: {v.get('issue')}")
            except:
                print(f"\n✗ Violations detected (see details below)")
            
            # Generate corrected code
            from photonics_agents.code_generation_agent import code_generation_agent
            corrected = code_generation_agent(nazca_code, str(analysis))
            
            corrected_file = str(self.tmp_dir / f"{Path(nazca_file).stem}_corrected.py")
            with open(corrected_file, 'w') as f:
                f.write(str(corrected))
            
            print(f"✓ Corrected: {corrected_file}")
            return
        
        if not violations:
            print("✓ No violations")
            return
        
        print(f"✗ Violations: {violations}")
        
        # Find source code
        nazca_file = self.find_nazca_source(gds_file)
        if not nazca_file:
            print("⚠ No source file")
            return
        
        # Read source code
        with open(nazca_file, 'r') as f:
            nazca_code = f.read()
        
        # Analyze violations
        print("Analyzing...")
        fix_brief = violation_analysis_agent(violations, nazca_code)
        
        # Generate corrected code
        corrected_code = code_generation_agent(nazca_code, str(fix_brief))
        
        # Save corrected code
        corrected_file = str(self.tmp_dir / f"{Path(nazca_file).stem}_corrected.py")
        with open(corrected_file, 'w') as f:
            f.write(str(corrected_code))
        
        print(f"✓ Corrected: {corrected_file}")
    
    def watch(self):
        """Watch for new GDS files"""
        print("="*80)
        print("GDS Orchestrator - Watching for files")
        print("="*80)
        print(f"Monitoring: {self.gds_dir}")
        print(f"DRC Rules: {self.drc_script}")
        print("Press Ctrl+C to stop")
        print("="*80)
        
        try:
            while True:
                gds_files = list(self.gds_dir.glob('*.gds'))
                
                for gds_file in gds_files:
                    if gds_file not in self.processed:
                        self.processed.add(gds_file)
                        self.process_gds(gds_file)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nStopping orchestrator...")

if __name__ == "__main__":
    orchestrator = GDSOrchestrator()
    orchestrator.watch()
