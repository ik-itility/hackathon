# Multi-Agent DRC System with Strands SDK

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                            │
│                  (Workflow Coordination)                         │
│                  Amazon Bedrock Nova Pro                         │
└────────┬──────────────────┬──────────────────┬──────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  GDS Parser    │  │  DRC Checker   │  │    Report      │
│     Agent      │  │     Agent      │  │   Generator    │
│                │  │                │  │     Agent      │
│  Nova Pro LLM  │  │  Nova Pro LLM  │  │  Nova Pro LLM  │
└────────┬───────┘  └────────┬───────┘  └────────┬───────┘
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │parse_gds│        │run_drc  │        │generate │
    │  tool   │        │_checks  │        │_reports │
    │         │        │  tool   │        │  tool   │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                  │                  │
         ▼                  ▼                  ▼
    ┌──────────────────────────────────────────────┐
    │         Core DRC Components                   │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
    │  │   GDS    │  │   DRC    │  │  Report  │  │
    │  │  Reader  │  │  Engine  │  │Formatter │  │
    │  │ (KLayout)│  │ (Rules)  │  │(JSON/TXT)│  │
    │  └──────────┘  └──────────┘  └──────────┘  │
    └──────────────────────────────────────────────┘
```

## System Components

### 1. Orchestrator Agent (`strands_orchestrator.py`)
**Role**: Workflow coordinator
**LLM**: Amazon Bedrock Nova Pro
**Responsibilities**:
- Receives DRC requests
- Coordinates agent execution sequence
- Aggregates results
- Provides user-friendly summaries

### 2. GDS Parser Agent (`gds_parser_agent.py`)
**Role**: File validation specialist
**LLM**: Amazon Bedrock Nova Pro
**Tool**: `parse_gds(gds_path)`
**Responsibilities**:
- Read GDS files using KLayout
- Extract layout metadata
- Validate file structure
- Return cell and layer information

### 3. DRC Checker Agent (`drc_checker_agent.py`)
**Role**: Design rule validation specialist
**LLM**: Amazon Bedrock Nova Pro
**Tool**: `run_drc_checks(gds_path, rules_path)`
**Responsibilities**:
- Load design rules from YAML
- Execute spacing, width, and separation checks
- Identify violations with locations
- Classify violation severity

### 4. Report Generator Agent (`report_generator_agent.py`)
**Role**: Technical documentation specialist
**LLM**: Amazon Bedrock Nova Pro
**Tool**: `generate_reports(violations, gds_path, output_dir)`
**Responsibilities**:
- Format violations into JSON reports
- Create human-readable text reports
- Include violation locations and counts
- Save reports to output directory

## Workflow Sequence

```
User Request: "Check GDS file for violations"
         │
         ▼
┌────────────────────────────────────────────┐
│ 1. Orchestrator receives request           │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ 2. GDS Parser Agent validates file         │
│    - Reads GDS structure                   │
│    - Returns: cells, layers, metadata      │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ 3. DRC Checker Agent runs checks           │
│    - Applies design rules                  │
│    - Returns: violations list              │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ 4. Report Generator Agent creates reports  │
│    - Formats JSON report                   │
│    - Formats text report                   │
│    - Returns: file paths                   │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ 5. Orchestrator summarizes results         │
│    - PASS/FAIL status                      │
│    - Violation counts                      │
│    - Report locations                      │
└────────────────────────────────────────────┘
```

## Key Features

### 🤖 Multi-Agent Coordination
- Each agent has specialized domain expertise
- Agents communicate through natural language
- Orchestrator manages workflow dependencies

### 🧠 LLM-Powered Reasoning
- Amazon Bedrock Nova Pro for each agent
- Adaptive decision making
- Natural language explanations

### 🔧 Tool-Based Architecture
- Each agent exposes specific tools
- Tools wrap existing DRC components
- Clean separation of concerns

### 📊 Comprehensive Reporting
- JSON format for machine processing
- Text format for human review
- Violation locations with coordinates

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | Strands SDK 1.1.0+ |
| **LLM Provider** | Amazon Bedrock (Nova Pro) |
| **GDS Parser** | KLayout 0.29.0+ |
| **Rules Engine** | Custom (PyYAML) |
| **Runtime** | Python 3.12+ |
| **Package Manager** | uv |

## File Structure

```
agents/
├── strands_orchestrator.py      # Main orchestrator
├── gds_parser_agent.py           # GDS parsing agent
├── drc_checker_agent.py          # DRC checking agent
├── report_generator_agent.py    # Report generation agent
├── gds_reader.py                 # KLayout wrapper
├── drc_engine.py                 # Rule engine
├── report.py                     # Report formatter
└── drc_agent.py                  # Legacy monolithic agent

data/
├── rules_config.yaml             # Design rules
└── layer_config.json             # Layer definitions

output/
├── *_drc_report.json             # Generated JSON reports
└── *_drc_report.txt              # Generated text reports
```

## Usage

### Basic Usage

```python
from agents.strands_orchestrator import process_gds_file

result = process_gds_file(
    gds_path='/workshop/hackathon/gds-files/correct_circuit.gds',
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)
```

### Command Line

```bash
uv run agents/strands_orchestrator.py
```

### Custom Workflow

```python
from agents.strands_orchestrator import create_orchestrator_agent

orchestrator = create_orchestrator_agent(
    rules_path='/path/to/rules.yaml',
    output_dir='/path/to/output'
)

result = orchestrator("""
Process this GDS file: /path/to/design.gds
Run all DRC checks and generate reports.
""")
```

## Comparison: Old vs New

| Aspect | Monolithic (Old) | Multi-Agent (New) |
|--------|------------------|-------------------|
| **Architecture** | Single class | 4 specialized agents |
| **LLM Integration** | None | Bedrock Nova Pro |
| **Reasoning** | Hardcoded logic | Adaptive AI reasoning |
| **Extensibility** | Difficult | Easy (add agents) |
| **Coordination** | Sequential calls | Agent orchestration |
| **Debugging** | Simple | More complex |
| **Latency** | ~1-2 sec | ~3-5 sec |
| **Cost** | Free | ~$0.01-0.05/run |

## Benefits of Multi-Agent Approach

### ✅ Separation of Concerns
Each agent has a single, well-defined responsibility

### ✅ LLM Reasoning
Agents can understand context and make intelligent decisions

### ✅ Extensibility
Easy to add new agents (e.g., Fix Suggestion Agent)

### ✅ Scalability
Agents can run in parallel or distributed

### ✅ Maintainability
Changes to one agent don't affect others

### ✅ Cloud-Native
Ready for AWS deployment with AgentCore

## Future Enhancements

### Additional Agents
- **Violation Analyzer Agent**: Deep analysis of specific violations
- **Fix Suggestion Agent**: Recommend layout corrections
- **Historical Comparison Agent**: Compare with past designs
- **Optimization Agent**: Suggest design improvements

### MCP Server Integration
- Expose design rules via Model Context Protocol
- Share rules across multiple tools
- Enable external tool integration

### AWS Deployment
- Deploy to AWS Lambda with AgentCore
- Use Step Functions for orchestration
- Store results in S3/DynamoDB

## Getting Started

See [QUICKSTART_STRANDS.md](QUICKSTART_STRANDS.md) for setup instructions.

## Documentation

- [STRANDS_REFACTORING.md](STRANDS_REFACTORING.md) - Detailed refactoring guide
- [AGENT_SYSTEM.md](AGENT_SYSTEM.md) - Legacy system documentation
- [README.md](README.md) - Project overview

## License

MIT License - See LICENSE file for details
