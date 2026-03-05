# GDS Orchestrator - Automated DRC Correction

Monitors `/shared_workshop/my_agents/gds_files/` and automatically runs DRC checks and corrections.

## Workflow

```
New GDS file detected
    ↓
Run DRC check (rules from drc/rules.txt)
    ↓
Violations found?
    ↓ YES
Find Nazca source code
    ↓
Violation Analysis Agent → Fix brief
    ↓
Code Generation Agent → Corrected code
    ↓
Save *_corrected.py file
```

## Setup

```bash
# 1. Ensure directories exist
mkdir -p /shared_workshop/my_agents/gds_files
mkdir -p /shared_workshop/my_agents/drc

# 2. Rules are already in drc/rules.txt
# 3. DRC script generated: drc/photonics_drc.drc
```

## Usage

### Start Orchestrator

```bash
cd /shared_workshop/my_agents
python orchestrator_gds.py
```

The orchestrator will watch for new `.gds` files.

### Add GDS File

```bash
# Copy or move GDS file to monitored folder
cp your_design.gds /shared_workshop/my_agents/gds_files/

# Or generate from Nazca
cd /shared_workshop/my_agents/gds_files
python your_nazca_script.py  # Must export GDS here
```

### What Happens

1. **Detection**: Orchestrator detects new GDS file
2. **DRC Check**: Runs KLayout with rules from `drc/rules.txt`
3. **If Clean**: Reports success
4. **If Violations**:
   - Finds corresponding `.py` source file
   - Analyzes violations
   - Generates corrected code
   - Saves as `*_corrected.py`

## Example

```bash
# Terminal 1: Start orchestrator
python orchestrator_gds.py

# Terminal 2: Add file
cp /shared_workshop/hackathon/nazca-scripts/Laser-with-errors.py \
   /shared_workshop/my_agents/gds_files/
cd /shared_workshop/my_agents/gds_files
python Laser-with-errors.py

# Orchestrator will:
# - Detect laser_with_errors.gds
# - Run DRC
# - Generate Laser-with-errors_corrected.py
```

## DRC Rules

Rules from `/shared_workshop/my_agents/drc/rules.txt`:

- Minimum spacing: 0.20 µm
- Minimum feature size: 0.10 µm
- Waveguide width: 0.45 - 2.0 µm
- Waveguide spacing: 0.30 µm
- Minimum bend radius: 10 µm

## Requirements

- KLayout (with DRC support)
- Nazca Python framework
- AWS Bedrock credentials (for AI agents)
