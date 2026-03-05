# Quick Start: Multi-Agent DRC System

## Prerequisites

```bash
cd /workshop/hackathon
uv sync  # Install dependencies including strands-agents
```

## Environment Setup

Set AWS credentials for Bedrock access:

```bash
export AWS_REGION=us-west-2
export AWS_PROFILE=your-profile  # Optional
```

## Run the Multi-Agent System

### Single File Processing

```bash
uv run agents/strands_orchestrator.py
```

This will process `/workshop/hackathon/gds-files/correct_circuit.gds` by default.

### Custom File Processing

```python
from agents.strands_orchestrator import process_gds_file

result = process_gds_file(
    gds_path='/workshop/hackathon/gds-files/laser_last_route_overlap.gds',
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)
```

## What Happens

1. **Orchestrator Agent** receives the request
2. **GDS Parser Agent** validates and reads the GDS file
3. **DRC Checker Agent** runs design rule checks
4. **Report Generator Agent** creates JSON and text reports
5. **Orchestrator Agent** summarizes results

## Expected Output

```
======================================================================
PHOTONICS DRC MULTI-AGENT SYSTEM (Strands SDK)
======================================================================
Processing: /workshop/hackathon/gds-files/correct_circuit.gds
Rules: /workshop/hackathon/data/rules_config.yaml
Output: /workshop/hackathon/output
======================================================================

[Agent coordination happens here with LLM reasoning]

======================================================================
WORKFLOW COMPLETE
======================================================================
```

## Verify Results

Check the output directory:

```bash
ls -la /workshop/hackathon/output/
```

You should see:
- `correct_circuit_drc_report.json`
- `correct_circuit_drc_report.txt`

## Troubleshooting

### AWS Credentials Error
```
Error: Unable to locate credentials
```
**Solution**: Configure AWS credentials
```bash
aws configure
```

### Bedrock Access Error
```
Error: Could not connect to Bedrock
```
**Solution**: Ensure Bedrock is enabled in us-west-2 region

### Import Error
```
ModuleNotFoundError: No module named 'strands'
```
**Solution**: Install dependencies
```bash
uv sync
```

## Compare with Legacy System

Run the old monolithic agent:
```bash
python3 agents/drc_agent.py
```

Compare execution time and output quality!

## Next Steps

1. Review [STRANDS_REFACTORING.md](STRANDS_REFACTORING.md) for architecture details
2. Explore individual agents in `agents/` directory
3. Customize agent prompts for your use case
4. Add new specialized agents (e.g., fix suggestion agent)
