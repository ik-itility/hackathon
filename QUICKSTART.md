# Quick Start Guide - Multi-Agent DRC System

## ⚡ 3-Step Quick Start

### Option A: Auto-Watch Mode (Recommended)

```bash
cd /workshop/hackathon

# 1. Install dependencies
uv sync

# 2. Start auto-watch (monitors folder for new files)
uv run agents/auto_watch_orchestrator.py

# 3. In another terminal, generate test files
uv run python generate_test_gds.py
```

### Option B: Manual Mode

```bash
cd /workshop/hackathon

# 1. Install dependencies
uv sync

# 2. Generate test files
uv run python generate_test_gds.py

# 3. Run the system
uv run agents/strands_orchestrator.py
```

## ✅ What Just Happened?

The multi-agent system:
1. **GDS Parser Agent** validated the GDS file structure
2. **DRC Checker Agent** ran design rule checks
3. **Report Generator Agent** created JSON and text reports

## 📊 View Results

```bash
# View text report
cat output/correct_circuit_drc_report.txt

# View JSON report
cat output/correct_circuit_drc_report.json
```

## 🧪 Test with Violations

```python
from agents.strands_orchestrator import process_gds_file

process_gds_file(
    gds_path='gds-files/laser_last_route_overlap.gds',
    rules_path='data/rules_config.yaml',
    output_dir='output'
)
```

## 📚 Full Documentation

- [HOW_TO_USE.md](HOW_TO_USE.md) - Complete usage guide
- [30_SECOND_EXPLANATION.md](30_SECOND_EXPLANATION.md) - System overview
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Architecture details
- [Multi_Agent_DRC_Architecture.drawio](Multi_Agent_DRC_Architecture.drawio) - Visual diagram

## 🔧 Troubleshooting

**No GDS files?**
```bash
uv run python generate_test_gds.py
```

**AWS credentials error?**
```bash
export AWS_REGION=us-west-2
aws configure
```

**Module not found?**
```bash
uv sync
```

## 🎯 What's Different from Legacy System?

| Feature | Legacy | Multi-Agent |
|---------|--------|-------------|
| Agents | 1 monolithic | 4 specialized |
| AI | None | Bedrock Nova Pro |
| Reasoning | Hardcoded | Adaptive |
| Extensible | No | Yes |

---

**Ready?** Run: `uv run agents/strands_orchestrator.py`
