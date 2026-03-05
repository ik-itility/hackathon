# Quick Start: Running Agents with AWS Bedrock Locally

Your agents already use AWS Bedrock with local files. Here's how:

## Architecture

```
Local Machine
├── Agents (Python) → AWS Bedrock API (Claude)
├── MCP Servers → Local JSON/MD files
└── IoT SiteWise MCP → AWS IoT SiteWise API
```

## Setup

### 1. Configure AWS Credentials

```bash
# Option A: AWS CLI
aws configure

# Option B: Environment variables
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_REGION="us-east-1"
```

### 2. Set Agent Environment Variables

```bash
export KNOWLEDGE_BASE_ID="your_kb_id"
export IOT_SITEWISE_ASSET_ID="your_asset_id"
```

### 3. Start Local MCP Servers

```bash
cd /workshop
uv run mcp_servers/servers/start_all_servers.py
```

This starts servers that read local files:
- CMMS: `/workshop/manufacturing-data/cmms/maintenance_data.json`
- ERP: `/workshop/manufacturing-data/erp/business_data.json`
- MES: `/workshop/manufacturing-data/mes/production_data.json`
- WPMS: `/workshop/manufacturing-data/wpms/workforce_data.json`
- SOP: `/workshop/manufacturing-data/sop/*.md`

### 4. Run Agents

```bash
cd /shared_workshop/my_agents

# Individual agents
uv run anomaly_root_cause_agent.py
uv run maintenance_planner_agent.py

# Orchestrator
uv run orchestrator_agent.py
```

## How It Works

1. **Agent runs locally** (Python process)
2. **Calls AWS Bedrock** (Claude model via boto3)
3. **Reads local files** (via MCP servers)
4. **Returns results** (printed to console)

## Cost

- AWS Bedrock charges per API call
- Local file access is free
- MCP servers run locally (no cost)

## Photonics Agents

```bash
cd /shared_workshop/my_agents/photonics_agents

python test_photonics_agents.py \
  /shared_workshop/hackathon/nazca-scripts/Laser-with-errors.py
```

Same setup - uses Bedrock API with local GDS files.
