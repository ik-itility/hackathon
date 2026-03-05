# Photonics IC Design Agents

Three specialized agents for automated DRC violation fixing in photonics IC design.

## Architecture

Based on the Nazca → KLayout DRC Agentic Process:

```
Nazca Python → GDS Export → KLayout DRC → Violation Analysis → Code Generation → Loop
```

## Agents

### 1. Violation Analysis Agent
- Parses .lyrdb XML violation reports
- Classifies violations by root cause
- Maps violations to Nazca code locations
- Groups related violations
- Generates structured fix briefs
- Flags cases needing human review

### 2. Code Generation Agent
- Receives fix briefs + Nazca code
- Applies surgical code edits
- Preserves unaffected geometry
- Validates Python syntax
- Returns corrected code

### 3. Orchestrator Agent
- Manages the DRC loop
- Exports GDS via Nazca
- Runs KLayout DRC checks
- Coordinates violation analysis and code generation
- Tracks iteration count and convergence
- Escalates stuck cases to humans

## Usage

```python
from photonics_agents.orchestrator_agent import DRCOrchestrator

orchestrator = DRCOrchestrator(max_iterations=10)
orchestrator.process(
    nazca_file="laser_with_errors.py",
    drc_script="foundry_drc.drc"
)
```

## Requirements

- KLayout (with DRC support)
- Nazca Python framework
- Foundry DRC rule deck

## Process Flow

1. **Export GDS**: Nazca script → .gds file
2. **Run DRC**: KLayout checks → .lyrdb violations
3. **Analyze**: Parse violations → fix briefs
4. **Generate**: Apply fixes → corrected code
5. **Iterate**: Repeat until clean or max iterations
6. **Escalate**: Human review if stuck

## Fix Brief Format

```json
[{
  "rule_id": "WG.W1",
  "cell_name": "laser",
  "line_number": 15,
  "parameter": "length",
  "current_value": 45,
  "suggested_value": 50,
  "confidence": "high"
}]
```

## Features

- **Root Cause Analysis**: Groups violations by underlying issue
- **Surgical Editing**: Only modifies specified parameters
- **Geometry Preservation**: Protects unaffected design elements
- **Convergence Detection**: Tracks violation deltas
- **Human Escalation**: Flags complex cases
- **Syntax Validation**: Ensures valid Python output
