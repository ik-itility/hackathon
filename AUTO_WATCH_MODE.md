# Auto-Watch Mode - Automatic GDS Processing

## 🎯 What is Auto-Watch Mode?

The system **automatically monitors** the `gds-files/` folder and processes any new `.gds` files that are created or copied into it.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /workshop/hackathon
uv sync  # Installs watchdog for file monitoring
```

### 2. Start Auto-Watch Mode
```bash
uv run agents/auto_watch_orchestrator.py
```

You'll see:
```
======================================================================
🤖 MULTI-AGENT DRC AUTO-WATCH SYSTEM
======================================================================
📁 Watching: /workshop/hackathon/gds-files
📋 Rules: /workshop/hackathon/data/rules_config.yaml
📊 Output: /workshop/hackathon/output
======================================================================

⏳ Waiting for new GDS files...
   (Drop a .gds file into the folder to trigger processing)
   (Press Ctrl+C to stop)
```

### 3. Trigger Processing

**Option A: Generate Test Files**
```bash
# In another terminal
cd /workshop/hackathon
uv run python generate_test_gds.py
```

**Option B: Copy Your Own Files**
```bash
# In another terminal
cp /path/to/your/design.gds gds-files/
```

**Option C: Create Files from Scripts**
```bash
# In another terminal
cd nazca-scripts
python3 your_circuit.py  # If it exports to gds-files/
```

### 4. Watch It Work!

When a new `.gds` file is detected:
```
======================================================================
🔔 NEW GDS FILE DETECTED: /workshop/hackathon/gds-files/my_design.gds
======================================================================

[Multi-agent processing starts automatically...]
[GDS Parser Agent validates...]
[DRC Checker Agent runs checks...]
[Report Generator Agent creates reports...]

======================================================================
WORKFLOW COMPLETE
======================================================================
```

### 5. Stop Monitoring
Press `Ctrl+C` to stop the auto-watch system.

## 📊 How It Works

```
┌─────────────────────────────────────┐
│  gds-files/ folder                  │
│  (being monitored)                  │
└──────────────┬──────────────────────┘
               │
               │ New .gds file created
               ↓
┌─────────────────────────────────────┐
│  Auto-Watch Orchestrator            │
│  (detects file creation)            │
└──────────────┬──────────────────────┘
               │
               │ Triggers processing
               ↓
┌─────────────────────────────────────┐
│  Multi-Agent DRC System             │
│  ├── GDS Parser Agent               │
│  ├── DRC Checker Agent              │
│  └── Report Generator Agent         │
└──────────────┬──────────────────────┘
               │
               │ Generates reports
               ↓
┌─────────────────────────────────────┐
│  output/ folder                     │
│  ├── design_drc_report.json         │
│  └── design_drc_report.txt          │
└─────────────────────────────────────┘
```

## 🎬 Demo Workflow

### Terminal 1: Start Auto-Watch
```bash
cd /workshop/hackathon
uv run agents/auto_watch_orchestrator.py
```

### Terminal 2: Generate Files
```bash
cd /workshop/hackathon

# Generate test file 1
uv run python -c "
from generate_test_gds import create_correct_circuit
create_correct_circuit()
"

# Wait for processing to complete...

# Generate test file 2
uv run python -c "
from generate_test_gds import create_violation_circuit
create_violation_circuit()
"
```

### Terminal 3: View Results
```bash
cd /workshop/hackathon

# Watch reports being created
watch -n 1 'ls -lt output/ | head -10'

# View latest report
cat output/*_drc_report.txt | tail -20
```

## 🔧 Configuration

### Change Watch Folder
Edit `agents/auto_watch_orchestrator.py`:
```python
start_watching(
    watch_folder='/your/custom/path',  # Change this
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)
```

### Change Rules or Output
```python
start_watching(
    watch_folder='/workshop/hackathon/gds-files',
    rules_path='/your/custom/rules.yaml',  # Change this
    output_dir='/your/custom/output'       # Change this
)
```

## 🆚 Comparison: Manual vs Auto-Watch

| Mode | Command | Use Case |
|------|---------|----------|
| **Manual** | `uv run agents/strands_orchestrator.py` | Process one specific file |
| **Auto-Watch** | `uv run agents/auto_watch_orchestrator.py` | Monitor folder, process all new files |

## 💡 Use Cases

### 1. CI/CD Integration
```bash
# Start auto-watch in background
nohup uv run agents/auto_watch_orchestrator.py &

# Your build process generates GDS files
make build  # Outputs to gds-files/

# DRC runs automatically
```

### 2. Design Iteration
```bash
# Start auto-watch
uv run agents/auto_watch_orchestrator.py

# Edit your design script
vim nazca-scripts/my_design.py

# Run script (exports to gds-files/)
python3 nazca-scripts/my_design.py

# DRC runs automatically, check results
cat output/my_design_drc_report.txt
```

### 3. Batch Processing
```bash
# Start auto-watch
uv run agents/auto_watch_orchestrator.py

# Copy multiple files
cp /designs/*.gds gds-files/

# All files processed automatically
```

## 🐛 Troubleshooting

### Files Not Being Detected
```bash
# Check watchdog is installed
uv run python -c "import watchdog; print('OK')"

# Check folder exists
ls -la gds-files/

# Check permissions
chmod 755 gds-files/
```

### Processing Errors
- Check AWS credentials are configured
- Verify GDS files are valid
- Check rules_config.yaml exists

### Stop Auto-Watch
Press `Ctrl+C` in the terminal running auto-watch

## 📚 Related Documentation

- [HOW_TO_USE.md](HOW_TO_USE.md) - Manual processing mode
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Architecture details

---

**Start monitoring now:** `uv run agents/auto_watch_orchestrator.py`
