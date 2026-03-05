"""Agent-callable DRC tool"""
import sys
sys.path.append('/workshop/hackathon/agents')

from gds_reader import GDSReader
from drc_engine import DRCEngine
from report import ReportFormatter

def run_drc(gds_path: str, rules_path: str = '/workshop/hackathon/data/rules_config.yaml', output_dir: str = '/workshop/hackathon/output') -> dict:
    """
    Agent-callable function that reads a GDS file and returns DRC violations.
    
    Args:
        gds_path: Path to GDS file
        rules_path: Path to rules YAML config
        output_dir: Directory to save reports
    
    Returns:
        Dictionary with violation summary
    """
    print(f"Reading GDS: {gds_path}")
    reader = GDSReader(gds_path)
    
    info = reader.get_info()
    print(f"  Top cell: {info['top_cell']}")
    print(f"  Cells: {info['num_cells']}")
    print(f"  DBU: {info['dbu']} µm")
    
    print(f"\nRunning DRC checks...")
    engine = DRCEngine(reader, rules_path)
    violations = engine.run_checks()
    
    print(f"\nGenerating reports...")
    json_path, txt_path = ReportFormatter.save_reports(violations, gds_path, output_dir)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {sum(v['count'] for v in violations)} total violations")
    print(f"{'='*60}")
    
    for v in violations:
        print(f"  [{v['severity']}] {v['rule']}: {v['count']} violations")
    
    print(f"\n✓ Reports saved:")
    print(f"  - {json_path}")
    print(f"  - {txt_path}")
    
    return ReportFormatter.to_json(violations, gds_path)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent_tool.py <gds_file>")
        sys.exit(1)
    
    result = run_drc(sys.argv[1])
