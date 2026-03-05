# Photonics GDS DRC Agent System

Automated Design Rule Check (DRC) system for photonics GDS files using two specialized agents.

## Architecture

```
New GDS File → Agent 1 (File Monitor) → Agent 2 (DRC Agent) → Reports
```

### Agent 1: File Monitor
- **Purpose**: Watches folder for new GDS files
- **Trigger**: Automatically detects new `.gds` files
- **Action**: Triggers Agent 2 for each new file
- **File**: `agents/file_monitor_agent.py`

### Agent 2: DRC Agent
- **Purpose**: Runs DRC checks and generates reports
- **Input**: GDS file path from Agent 1
- **Process**: 
  1. Reads GDS file using KLayout
  2. Loads rules from `data/rules_config.yaml`
  3. Runs spacing checks (Rule 6: 0.30 µm)
  4. Generates JSON and TXT reports
- **Output**: Reports in `output/` folder
- **File**: `agents/drc_agent.py`

## Design Rules

From `data/rules.txt`:
- **Rule 6**: Minimum waveguide spacing = 0.30 µm
- **Layers checked**: 
  - Layer 1003/0 (waveguides)
  - Layer 10/0 (routing)

## Usage

### Start the Agent System

```bash
cd /workshop/hackathon
python3 agents/main_orchestrator.py
```

The system will:
1. Watch `/workshop/hackathon/gds-files/` for new GDS files
2. Automatically run DRC on any new file
3. Generate reports in `/workshop/hackathon/output/`

### Manual DRC Check

```bash
python3 agents/agent_tool.py gds-files/your_file.gds
```

## Output

For each GDS file, two reports are generated:

1. **Text Report** (`filename_drc_report.txt`):
   - Human-readable summary
   - Violation counts by layer
   - Sample violation locations

2. **JSON Report** (`filename_drc_report.json`):
   - Machine-readable format
   - Complete violation data
   - Timestamps

## Example Output

```
[FileMonitor] New file detected: laser_with_errors.gds
[DRCAgent] Processing: laser_with_errors.gds
[DRCAgent] Loaded: nazca (16 cells)
[DRCAgent] Running DRC checks...
[DRCAgent] ✗ FAIL - 8 violations
[DRCAgent]   Layer 1003/0: 8 violations
[DRCAgent] Reports saved:
[DRCAgent]   - output/laser_with_errors_drc_report.txt
[DRCAgent]   - output/laser_with_errors_drc_report.json
```

## Files

```
agents/
├── file_monitor_agent.py    # Agent 1: File monitoring
├── drc_agent.py              # Agent 2: DRC processing
├── main_orchestrator.py      # Orchestrator
├── gds_reader.py             # GDS file reader (KLayout)
├── drc_engine.py             # DRC rule engine
├── report.py                 # Report generator
└── agent_tool.py             # CLI tool

data/
├── rules.txt                 # Design rules documentation
└── rules_config.yaml         # Machine-readable rules

output/                       # Generated reports
```

## Requirements

- Python 3.12+
- klayout (pip install klayout)
- pyyaml (pip install pyyaml)
