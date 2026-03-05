"""DRC Checker Agent - Specialized agent for running design rule checks"""
from strands import Agent, tool
from strands.models import BedrockModel
from gds_reader import GDSReader
from drc_engine import DRCEngine

CHECKER_PROMPT = """You are a design rule checking specialist for photonics layouts.
Your role is to validate GDS designs against manufacturing rules.
Use the run_drc_checks tool to identify violations."""

@tool
def run_drc_checks(gds_path: str, rules_path: str, output_dir: str) -> dict:
    """Run DRC checks on a GDS file and save reports.
    
    Args:
        gds_path: Path to the GDS file
        rules_path: Path to the rules configuration YAML
        output_dir: Directory to save reports
    """
    from report import ReportFormatter
    import os
    
    reader = GDSReader(gds_path)
    engine = DRCEngine(reader, rules_path)
    violations = engine.run_checks()
    
    total = sum(v['count'] for v in violations)
    
    # Save reports immediately
    os.makedirs(output_dir, exist_ok=True)
    json_path, txt_path = ReportFormatter.save_reports(
        violations, gds_path, output_dir
    )
    
    return {
        'success': True,
        'gds_path': gds_path,
        'status': 'PASS' if total == 0 else 'FAIL',
        'total_violations': total,
        'violations_summary': [{
            'rule': v['rule'],
            'count': v['count'],
            'severity': v['severity']
        } for v in violations],
        'json_report': json_path,
        'text_report': txt_path
    }

def create_drc_checker_agent():
    """Create and return the DRC Checker Agent"""
    model = BedrockModel(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-west-2"
    )
    
    return Agent(
        model=model,
        system_prompt=CHECKER_PROMPT,
        tools=[run_drc_checks]
    )
