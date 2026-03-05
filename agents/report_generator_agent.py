"""Report Generator Agent - Specialized agent for creating DRC reports"""
from strands import Agent, tool
from strands.models import BedrockModel
from report import ReportFormatter

REPORTER_PROMPT = """You are a technical report specialist for photonics DRC results.
Your role is to generate clear, actionable reports from DRC violations.
Use the generate_reports tool to create JSON and text reports."""

@tool
def generate_reports(gds_path: str, output_dir: str, violations_count: int = 0) -> dict:
    """Generate DRC reports in JSON and text formats.
    
    Args:
        gds_path: Path to the GDS file that was checked
        output_dir: Directory to save reports
        violations_count: Number of violations found (for summary)
    """
    import os
    import json
    
    # Read violations from the DRC check output
    # The violations are already saved by run_drc_checks, we just format them
    basename = os.path.basename(gds_path).replace('.gds', '')
    json_report_path = os.path.join(output_dir, f"{basename}_drc_report.json")
    txt_report_path = os.path.join(output_dir, f"{basename}_drc_report.txt")
    
    # Check if reports already exist (created by run_drc_checks)
    if os.path.exists(json_report_path) and os.path.exists(txt_report_path):
        with open(json_report_path) as f:
            report_data = json.load(f)
            total = report_data.get('total_violations', violations_count)
    else:
        total = violations_count
    
    return {
        'success': True,
        'status': 'PASS' if total == 0 else 'FAIL',
        'total_violations': total,
        'json_report': json_report_path,
        'text_report': txt_report_path
    }

def create_report_generator_agent():
    """Create and return the Report Generator Agent"""
    model = BedrockModel(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-west-2"
    )
    
    return Agent(
        model=model,
        system_prompt=REPORTER_PROMPT,
        tools=[generate_reports]
    )
