#!/usr/bin/env python3
"""
Example: Running agents with custom Bedrock settings
"""

import os
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['MODEL_ID'] = 'us.anthropic.claude-sonnet-4-20250514-v1:0'

# For manufacturing agents
from anomaly_root_cause_agent import anomaly_root_cause_agent
from maintenance_planner_agent import maintenance_planner_agent

# Example 1: Anomaly detection with local IoT data
result = anomaly_root_cause_agent(
    query="Analyze equipment for anomalies",
    asset_id="your-asset-id",
    context="Gearbox showing unusual vibration patterns"
)
print("Anomaly Analysis:")
print(result)

# Example 2: Create maintenance work order
incident = """
Critical incident detected:
- Equipment: Gearbox GB001
- Severity: critical
- Anomaly: Excessive vibration (8.5 m/s)
- Root Cause: Bearing wear
"""

work_order = maintenance_planner_agent(incident)
print("\nWork Order:")
print(work_order)
