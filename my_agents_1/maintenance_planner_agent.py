from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

@tool
def maintenance_planner_agent(incident_report: str) -> str:
    """Processes incident reports and creates maintenance work orders.
    
    Args:
        incident_report: Detailed incident report from anomaly detection
        
    Returns:
        Work order details and maintenance recommendations
    """
    try:
        sop_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command="uv",
                args=["run", "python", "/workshop/mcp_servers/servers/sop_mcp_server.py", "--stdio"]
            )
        ))
        cmms_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command="uv",
                args=["run", "python", "/workshop/mcp_servers/servers/cmms_mcp_server.py", "--stdio"]
            )
        ))

        with sop_client, cmms_client:
            cmms_tools = cmms_client.list_tools_sync()
            sop_tools = sop_client.list_tools_sync()
            
            agent = Agent(
                name="Maintenance Planner",
                system_prompt="""You are a Senior Maintenance Operations Expert.

Responsibilities:
1. Receive incident reports from Anomaly Root Cause Agent
2. Create maintenance work orders using create_work_order tool
3. Assign priority: P1 (Critical - immediate), P2 (Warning - 24-48hrs)
4. Suggest maintenance steps per SOPs
5. Ensure documentation and traceability

Extract: severity, asset_id, actions, required parts.
Provide clear, actionable work order details.""",
                tools=[cmms_tools + sop_tools]
            )
            
            return agent(incident_report)
            
    except Exception as e:
        return f"Maintenance planner error: {str(e)}"

if __name__ == "__main__":
    test_incident = """
    Critical incident:
    - Severity: critical
    - Asset ID: GB001
    - Equipment: Gearbox Station
    - Anomaly: Bearing vibration exceeds limits (8 m/s)
    - Root Cause: Bearing failure due to lubrication issues
    - Recommendations: Emergency shutdown, replace bearing kit, replace oil filter
    """
    
    print(maintenance_planner_agent(test_incident))
