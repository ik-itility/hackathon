from strands import Agent, tool
import ast
import json

@tool
def code_generation_agent(nazca_code: str, fix_brief: str) -> str:
    """Generates corrected Nazca Python code based on fix briefs.
    
    Args:
        nazca_code: Current Nazca Python source code
        fix_brief: Structured fix instructions from violation analysis
        
    Returns:
        Corrected Nazca Python code
    """
    try:
        agent = Agent(
            system_prompt="""You are a Nazca Python code generation expert.

Apply fixes surgically:
1. Only modify specified parameters in fix brief
2. Preserve all unaffected geometry
3. Maintain code structure and style
4. Validate Python syntax
5. Do NOT export GDS (orchestrator handles that)

Rules:
- Minimal diffs only
- No refactoring
- No comments unless critical
- Preserve variable names and formatting

Return complete corrected code.""",
            tools=[]
        )
        
        query = f"""Apply these fixes to the Nazca code:

Fix Brief:
{fix_brief}

Current Code:
{nazca_code}

Generate corrected code."""
        
        result = agent(query)
        
        # Validate syntax
        try:
            ast.parse(str(result))
        except SyntaxError as e:
            return f"Syntax error in generated code: {e}"
        
        return result
        
    except Exception as e:
        return f"Code generation error: {str(e)}"

if __name__ == "__main__":
    test_code = """
laser1 = dbr_laser(Lsoa=750).put(0)
laser2 = dbr_laser(Lsoa=1000).put(0, -200)
"""
    test_brief = '[{"rule_id": "SPACING", "line_number": 2, "parameter": "y_offset", "current_value": -200, "suggested_value": -300}]'
    result = code_generation_agent(test_code, test_brief)
    print(result)
