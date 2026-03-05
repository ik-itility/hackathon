# S3 Code Validation System

Three-agent system for automated code validation and fixing.

## Architecture

```
S3 Upload → Agent 1 (Reader) → Agent 2 (Validator) → Agent 3 (Fixer) → Manual Approval
```

### Agents

1. **S3 File Reader Agent**: Triggered by S3 upload events, reads Python files
2. **Code Validator Agent**: Validates code against rules from `data/rules.txt`
3. **Code Fixer Agent**: Uses AWS Bedrock to fix code errors

### Workflow

1. Python file uploaded to S3 bucket
2. Agent 1 reads the file content
3. Agent 2 validates against rules
4. If errors found, Agent 3 generates fixes
5. Manual approval required before applying changes

## Setup

```bash
# Install dependencies
pip install boto3

# Configure AWS credentials
aws configure
```

## Usage

```bash
cd /workshop/hackathon/agents
python orchestrator.py
```

## Files

- `agents/s3_file_reader_agent.py` - Agent 1
- `agents/code_validator_agent.py` - Agent 2
- `agents/code_fixer_agent.py` - Agent 3
- `agents/orchestrator.py` - Workflow coordinator
- `data/rules.txt` - Validation rules
