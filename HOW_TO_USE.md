# How to Use the Multi-Agent DRC System

## Prerequisites

1. **AWS Account** with Bedrock access
2. **Python 3.12+** installed
3. **uv** package manager installed

## Step 1: Setup Environment

```bash
cd /workshop/hackathon

# Install dependencies
uv sync

# Configure AWS credentials (if not already done)
export AWS_REGION=us-west-2
export AWS_PROFILE=your-profile  # Optional
```

## Step 2: Generate Test GDS Files

```bash
# Generate sample GDS files for testing
uv run python generate_test_gds.py
```

This creates:
- `gds-files/correct_circuit.gds` (no violations)
- `gds-files/laser_last_route_overlap.gds` (has violations)

## Step 3: Run the Multi-Agent System

### Option A: Default Test (Recommended for First Run)

```bash
uv run agents/strands_orchestrator.py
```

This processes `correct_circuit.gds` by default.

### Option B: Custom File via Python

```python
from agents.strands_orchestrator import process_gds_file

result = process_gds_file(
    gds_path='/workshop/hackathon/gds-files/laser_last_route_overlap.gds',
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)

print(result)
```

### Option C: Interactive Python Session

```bash
cd /workshop/hackathon
uv run python
```

```python
from agents.strands_orchestrator import process_gds_file

# Test file with violations
result = process_gds_file(
    gds_path='gds-files/laser_last_route_overlap.gds',
    rules_path='data/rules_config.yaml',
    output_dir='output'
)
```

## Step 4: View Results

### Check Console Output

You'll see:
```
======================================================================
PHOTONICS DRC MULTI-AGENT SYSTEM (Strands SDK)
======================================================================
Processing: /workshop/hackathon/gds-files/correct_circuit.gds
Rules: /workshop/hackathon/data/rules_config.yaml
Output: /workshop/hackathon/output
======================================================================

[Orchestrator coordinates agents...]
[GDS Parser Agent validates file...]
[DRC Checker Agent runs checks...]
[Report Generator Agent creates reports...]

======================================================================
WORKFLOW COMPLETE
======================================================================
```

### Check Generated Reports

```bash
ls -la output/

# View text report
cat output/correct_circuit_drc_report.txt

# View JSON report
cat output/correct_circuit_drc_report.json
```

## Step 5: Test with Different Files

### Test File with Violations

```bash
uv run python -c "
from agents.strands_orchestrator import process_gds_file
process_gds_file(
    'gds-files/laser_last_route_overlap.gds',
    'data/rules_config.yaml',
    'output'
)
"
```

### Add Your Own GDS Files

```bash
# Copy your GDS file
cp /path/to/your/design.gds gds-files/

# Process it
uv run python -c "
from agents.strands_orchestrator import process_gds_file
process_gds_file(
    'gds-files/your_design.gds',
    'data/rules_config.yaml',
    'output'
)
"
```

## Understanding the Output

### Text Report Format
```
============================================================
PHOTONICS GDS DRC REPORT
============================================================

File: /workshop/hackathon/gds-files/laser_last_route_overlap.gds
Date: 2024-03-05 14:50:00

Total Violations: 8

VIOLATIONS:
------------------------------------------------------------

[WARNING] WG.6 - Waveguide Spacing
  Description: Minimum spacing between waveguides
  Layer: 1003/0
  Count: 8
  Sample locations:
    - (123.456, 789.012) µm
    - (234.567, 890.123) µm
```

### JSON Report Format
```json
{
  "file": "/workshop/hackathon/gds-files/laser_last_route_overlap.gds",
  "timestamp": "2024-03-05T14:50:00",
  "total_violations": 8,
  "violations": [
    {
      "rule": "WG.6",
      "description": "Minimum spacing between waveguides",
      "layer": "1003/0",
      "count": 8,
      "severity": "WARNING",
      "locations": [...]
    }
  ]
}
```

## Troubleshooting

### Error: "Unable to locate credentials"
```bash
# Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-west-2
```

### Error: "Could not connect to Bedrock"
- Ensure Bedrock is enabled in your AWS account
- Check region is `us-west-2`
- Verify IAM permissions for Bedrock access

### Error: "ModuleNotFoundError: No module named 'strands'"
```bash
uv sync  # Reinstall dependencies
```

### Error: "ModuleNotFoundError: No module named 'klayout'"
```bash
uv add klayout  # Add KLayout if missing
```

## Comparing with Legacy System

### Run Old Monolithic Agent
```bash
python3 agents/drc_agent.py
```

### Compare Performance
- **Legacy**: ~1-2 seconds, no AI reasoning
- **Multi-Agent**: ~3-5 seconds, with AI reasoning and explanations

## Advanced Usage

### Customize Agent Prompts

Edit the agent files to customize behavior:
- `agents/gds_parser_agent.py` - Change PARSER_PROMPT
- `agents/drc_checker_agent.py` - Change CHECKER_PROMPT
- `agents/report_generator_agent.py` - Change REPORTER_PROMPT
- `agents/strands_orchestrator.py` - Change ORCHESTRATOR_PROMPT

### Modify Design Rules

Edit `data/rules_config.yaml`:
```yaml
rules:
  - name: "WG.6"
    check: "space"
    layer: [1003, 0]
    min_value_nm: 300  # Change this value
    description: "Minimum spacing between waveguides"
```

### Add New Agents

Create a new agent file following the pattern:
```python
from strands import Agent, tool
from strands.models import BedrockModel

@tool
def your_tool(param: str) -> dict:
    """Your tool description"""
    # Your logic here
    return {'success': True}

def create_your_agent():
    model = BedrockModel(
        model_id="us.amazon.nova-pro-v1:0",
        region_name="us-west-2"
    )
    return Agent(
        model=model,
        system_prompt="Your agent prompt",
        tools=[your_tool]
    )
```

## Next Steps

1. ✅ Test with your own GDS files
2. ✅ Customize design rules for your process
3. ✅ Add new specialized agents (fix suggestions, optimization)
4. ✅ Deploy to AWS Lambda with AgentCore
5. ✅ Integrate with CI/CD pipeline

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv sync` | Install dependencies |
| `uv run agents/strands_orchestrator.py` | Run default test |
| `python3 agents/drc_agent.py` | Run legacy system |
| `ls output/` | View generated reports |
| `cat output/*_report.txt` | Read text report |

## Documentation

- [30_SECOND_EXPLANATION.md](30_SECOND_EXPLANATION.md) - Quick overview
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Architecture details
- [STRANDS_REFACTORING.md](STRANDS_REFACTORING.md) - Old vs new comparison
- [Multi_Agent_DRC_Architecture.drawio](Multi_Agent_DRC_Architecture.drawio) - Visual diagram

---

**Ready to start?** Run: `uv run agents/strands_orchestrator.py`
