"""Agent 2: DRC Agent - Reads rules and generates reports"""
import sys
sys.path.append('/workshop/hackathon/agents')
from gds_reader import GDSReader
from drc_engine import DRCEngine
from report import ReportFormatter

class DRCAgent:
    def __init__(self, rules_path: str, output_dir: str):
        self.rules_path = rules_path
        self.output_dir = output_dir
    
    def process_gds(self, gds_path: str):
        """Process GDS file: read, check rules, generate report"""
        print(f"\n[DRCAgent] Processing: {gds_path}")
        
        # Read GDS
        reader = GDSReader(gds_path)
        info = reader.get_info()
        print(f"[DRCAgent] Loaded: {info['top_cell']} ({info['num_cells']} cells)")
        
        # Run DRC
        print(f"[DRCAgent] Running DRC checks...")
        engine = DRCEngine(reader, self.rules_path)
        violations = engine.run_checks()
        
        total = sum(v['count'] for v in violations)
        
        # Generate reports
        json_path, txt_path = ReportFormatter.save_reports(
            violations, gds_path, self.output_dir
        )
        
        # Print result
        if total == 0:
            print(f"[DRCAgent] ✓ PASS - No violations")
        else:
            print(f"[DRCAgent] ✗ FAIL - {total} violations")
            for v in violations:
                print(f"[DRCAgent]   Layer {v['layer']}: {v['count']} violations")
        
        print(f"[DRCAgent] Reports saved:")
        print(f"[DRCAgent]   - {txt_path}")
        print(f"[DRCAgent]   - {json_path}")
        
        return {
            'file': gds_path,
            'status': 'PASS' if total == 0 else 'FAIL',
            'violations': total,
            'reports': [txt_path, json_path]
        }

if __name__ == '__main__':
    agent = DRCAgent(
        rules_path='/workshop/hackathon/data/rules_config.yaml',
        output_dir='/workshop/hackathon/output'
    )
    
    result = agent.process_gds('/workshop/hackathon/gds-files/correct_circuit.gds')
    print(f"\nResult: {result}")
