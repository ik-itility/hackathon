/shared_workshop/my_agents/gds_files# Manufacturing AI Agents

Three specialized agents for manufacturing anomaly detection and maintenance planning.

## Agents

### 1. Anomaly Root Cause Agent
- Analyzes IoT SiteWise sensor data
- Detects anomalies using Knowledge Base
- Generates structured incident reports

### 2. Maintenance Planner Agent
- Processes incident reports
- Creates CMMS work orders
- Follows SOP guidelines

### 3. Orchestrator Agent
- Coordinates both agents
- Manages workflow execution
- Provides comprehensive summaries

## Usage

```bash
# Set environment variables
export KNOWLEDGE_BASE_ID="your_kb_id"
export IOT_SITEWISE_ASSET_ID="your_asset_id"

# Start MCP servers (from /workshop)
cd /workshop
uv run mcp_servers/servers/start_all_servers.py

# Run agents
cd /shared_workshop/my_agents
uv run anomaly_root_cause_agent.py
uv run maintenance_planner_agent.py
uv run orchestrator_agent.py
```
