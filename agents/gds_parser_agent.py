"""GDS Parser Agent - Specialized agent for reading and validating GDS files"""
from strands import Agent, tool
from strands.models import BedrockModel
from gds_reader import GDSReader

PARSER_PROMPT = """You are a GDS file parser specialist for photonics design.
Your role is to read GDS files and extract layout information.
Use the parse_gds tool to read files and provide structured information."""

@tool
def parse_gds(gds_path: str) -> dict:
    """Parse a GDS file and extract layout information.
    
    Args:
        gds_path: Path to the GDS file
    """
    reader = GDSReader(gds_path)
    info = reader.get_info()
    return {
        'success': True,
        'gds_path': gds_path,
        'top_cell': info['top_cell'],
        'num_cells': info['num_cells'],
        'layers': info['layers'],
        'dbu': info['dbu']
    }

def create_gds_parser_agent():
    """Create and return the GDS Parser Agent"""
    model = BedrockModel(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-west-2"
    )
    
    return Agent(
        model=model,
        system_prompt=PARSER_PROMPT,
        tools=[parse_gds]
    )
