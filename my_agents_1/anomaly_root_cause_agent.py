from strands import Agent, tool
from strands_tools import retrieve
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
import os
import sys

sys.path.insert(0, '/workshop')
from config import get_bedrock_model_for_agent

KB_ID = os.getenv("KNOWLEDGE_BASE_ID", "DU2HABSDO6")
ASSET_ID = os.getenv("IOT_SITEWISE_ASSET_ID")

_mcp_client = None
_agent_instance = None

def _get_mcp_client():
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(command="uvx", args=["awslabs.aws-iot-sitewise-mcp-server"])
        ))
    return _mcp_client

def _get_agent_instance():
    global _agent_instance
    if _agent_instance is None:
        mcp_client = _get_mcp_client()
        mcp_client.start()
        tools = mcp_client.list_tools_sync()
        
        _agent_instance = Agent(
            system_prompt="""You are an anomaly detection expert for manufacturing equipment.

Responsibilities:
1. Retrieve sensor data from IoT SiteWise (use us-west-2 region)
2. Analyze readings against asset specifications from knowledge base
3. Detect anomalies and identify root causes
4. Generate structured incident reports

Output format:
{
  "timestamp": "ISO-8601",
  "equipment": "name",
  "asset_id": "id",
  "severity": "critical|warning",
  "anomaly_detected": "description",
  "sensor_readings": {"metric": value},
  "root_causes": "analysis",
  "recommendations": "actions"
}

Flag missing data as SEVERE OPERATION_RISK.""",
            tools=[tools, retrieve],
            model=get_bedrock_model_for_agent("anomaly_root_cause")
        )
    return _agent_instance

@tool
def anomaly_root_cause_agent(query: str, asset_id: str = None, context: str = "") -> str:
    """Analyzes sensor data to detect anomalies and identify root causes.
    
    Args:
        query: Analysis request
        asset_id: IoT SiteWise asset ID
        context: Additional context
        
    Returns:
        Structured incident report with anomaly detection and recommendations
    """
    try:
        full_query = f"{query} for asset id: {asset_id}" if asset_id else query
        if context:
            full_query = f"{full_query}. Context: {context}"
        
        agent = _get_agent_instance()
        return str(agent(full_query))
    except Exception as e:
        return f"Anomaly detection error: {str(e)}"

if __name__ == "__main__":
    result = anomaly_root_cause_agent(
        query="Detect anomaly and analyze root cause if any",
        asset_id=ASSET_ID
    )
    print(result)
