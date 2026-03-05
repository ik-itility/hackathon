"""DRC Orchestrator Agent - Coordinates GDS parsing, DRC checking, and report generation"""
from strands import Agent
from strands.models import BedrockModel

ORCHESTRATOR_PROMPT = """You are the DRC workflow orchestrator for photonics design validation.

Your role is to coordinate three specialized tools:
1. parse_gds - Reads and validates GDS files
2. run_drc_checks - Runs design rule checks AND saves reports
3. generate_reports - Confirms reports were created successfully

When given a GDS file path, you must:
1. First, use parse_gds to validate the file
2. Then, use run_drc_checks with output_dir parameter - this will run checks AND save reports
3. Finally, use generate_reports to confirm the reports exist

Provide a clear summary of the results to the user."""

def create_orchestrator_agent(rules_path: str, output_dir: str):
    """Create the orchestrator agent with access to specialized agent tools"""
    
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Import tools from specialized agents
    from gds_parser_agent import parse_gds
    from drc_checker_agent import run_drc_checks
    from report_generator_agent import generate_reports
    
    # Create orchestrator model
    model = BedrockModel(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-west-2"
    )
    
    # Create orchestrator with all tools
    orchestrator = Agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[parse_gds, run_drc_checks, generate_reports]
    )
    
    # Store config for use in prompts
    orchestrator.rules_path = rules_path
    orchestrator.output_dir = output_dir
    
    return orchestrator

def process_gds_file(gds_path: str, rules_path: str, output_dir: str):
    """Process a GDS file through the multi-agent workflow"""
    
    print(f"\n{'='*70}")
    print("PHOTONICS DRC MULTI-AGENT SYSTEM (Strands SDK)")
    print(f"{'='*70}")
    print(f"Processing: {gds_path}")
    print(f"Rules: {rules_path}")
    print(f"Output: {output_dir}")
    print(f"{'='*70}\n")
    
    # Create orchestrator
    orchestrator = create_orchestrator_agent(rules_path, output_dir)
    
    # Execute workflow
    prompt = f"""Process this GDS file through the complete DRC workflow:
    
File: {gds_path}
Rules: {rules_path}
Output Directory: {output_dir}

Steps:
1. Parse the GDS file to validate it can be read
2. Run DRC checks using the rules configuration
3. Generate reports in both JSON and text formats

Provide a summary of the results."""
    
    result = orchestrator(prompt)
    
    print(f"\n{'='*70}")
    print("WORKFLOW COMPLETE")
    print(f"{'='*70}\n")
    
    return result

if __name__ == '__main__':
    result = process_gds_file(
        gds_path='/workshop/hackathon/gds-files/correct_circuit.gds',
        rules_path='/workshop/hackathon/data/rules_config.yaml',
        output_dir='/workshop/hackathon/output'
    )
    print(result)
