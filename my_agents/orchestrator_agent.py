from strands import Agent
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from anomaly_root_cause_agent import anomaly_root_cause_agent
from maintenance_planner_agent import maintenance_planner_agent

ASSET_ID = os.getenv("IOT_SITEWISE_ASSET_ID")

orchestrator = Agent(
    name="Orchestrator",
    system_prompt="""You are a Manufacturing Operations Supervisor coordinating anomaly detection and maintenance planning.

Workflow:
1. Call anomaly_root_cause_agent to detect anomalies for the asset
2. If anomaly detected, pass results to maintenance_planner_agent to create work order
3. Provide complete summary of analysis and outcomes

Ensure both agents complete their tasks.""",
    tools=[anomaly_root_cause_agent, maintenance_planner_agent]
)

if __name__ == "__main__":
    result = orchestrator(f"""
    Coordinate workflow:
    1. Analyze asset {ASSET_ID} for anomalies and root causes
    2. If anomalies found, create maintenance work order
    
    Provide complete summary.
    """)
    
    print("\n" + "="*80)
    print("ORCHESTRATOR RESULT")
    print("="*80)
    print(result)
