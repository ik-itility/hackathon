from strands import Agent, tool
import xml.etree.ElementTree as ET
import re

@tool
def violation_analysis_agent(violations_xml: str, nazca_code: str) -> str:
    """Analyzes DRC violations and generates fix briefs.
    
    Args:
        violations_xml: Path to .lyrdb XML file or XML content
        nazca_code: Current Nazca Python source code
        
    Returns:
        Structured fix briefs with rule_id, cell_name, line_number, parameter, values
    """
    try:
        # Parse XML violations
        if violations_xml.endswith('.lyrdb') or violations_xml.endswith('.xml'):
            tree = ET.parse(violations_xml)
            root = tree.getroot()
        else:
            root = ET.fromstring(violations_xml)
        
        agent = Agent(
            system_prompt="""You are a DRC violation analysis expert for photonics IC design.

Analyze violations and generate fix briefs:
1. Classify by root cause (not just rule ID)
2. Map violations to Nazca code locations (str(), bend(), component calls)
3. Group related violations (same root cause)
4. Determine if auto-fixable or needs human review
5. Generate structured fix briefs

Output JSON format:
[{
  "rule_id": "WG.W1",
  "cell_name": "laser",
  "line_number": 15,
  "parameter": "length",
  "current_value": 45,
  "suggested_value": 50,
  "confidence": "high"
}]

Flag intentional design choices (coupled waveguides) for human review.""",
            tools=[]
        )
        
        # Extract violation data
        violations = []
        for item in root.findall('.//item'):
            violations.append({
                'category': item.find('category').text if item.find('category') is not None else '',
                'values': item.find('values').text if item.find('values') is not None else ''
            })
        
        query = f"""Analyze these DRC violations and map to Nazca code:

Violations: {violations}

Nazca Code:
{nazca_code}

Generate fix briefs."""
        
        return agent(query)
        
    except Exception as e:
        return f"Violation analysis error: {str(e)}"

if __name__ == "__main__":
    test_code = """
laser1 = dbr_laser(Lsoa=750).put(0)
laser2 = dbr_laser(Lsoa=1000).put(0, -200)
"""
    result = violation_analysis_agent("violations.lyrdb", test_code)
    print(result)
