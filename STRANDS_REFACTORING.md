# DRC System Refactoring: Monolithic → Multi-Agent (Strands SDK)

## Architecture Comparison

### OLD: Monolithic Agent (drc_agent.py)
```
Single DRCAgent Class
├── GDSReader (embedded)
├── DRCEngine (embedded)
└── ReportFormatter (embedded)
```

**Limitations:**
- Single responsibility violation
- Hard to test individual components
- No agent coordination
- Sequential, blocking execution
- No LLM reasoning capabilities

### NEW: Multi-Agent System (Strands SDK)

```
Orchestrator Agent (coordinates workflow)
├── GDS Parser Agent (reads files)
├── DRC Checker Agent (runs checks)
└── Report Generator Agent (creates reports)
```

**Benefits:**
- Separation of concerns
- Each agent has specialized LLM reasoning
- Parallel execution potential
- Agent-to-agent communication
- Extensible architecture

## File Structure

### New Strands SDK Agents

| File | Purpose | Tools |
|------|---------|-------|
| `gds_parser_agent.py` | Parse GDS files | `parse_gds()` |
| `drc_checker_agent.py` | Run DRC checks | `run_drc_checks()` |
| `report_generator_agent.py` | Generate reports | `generate_reports()` |
| `strands_orchestrator.py` | Coordinate workflow | Uses all 3 agents |

### Legacy Files (Keep for reference)

| File | Purpose |
|------|---------|
| `drc_agent.py` | Original monolithic agent |
| `main_orchestrator.py` | Simple file monitor orchestrator |

## Usage Comparison

### OLD: Monolithic Approach
```python
from drc_agent import DRCAgent

agent = DRCAgent(
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)

result = agent.process_gds('/workshop/hackathon/gds-files/correct_circuit.gds')
```

### NEW: Multi-Agent Strands SDK
```python
from strands_orchestrator import process_gds_file

result = process_gds_file(
    gds_path='/workshop/hackathon/gds-files/correct_circuit.gds',
    rules_path='/workshop/hackathon/data/rules_config.yaml',
    output_dir='/workshop/hackathon/output'
)
```

## Running the System

### Option 1: New Multi-Agent System (Recommended)
```bash
cd /workshop/hackathon
uv run agents/strands_orchestrator.py
```

### Option 2: Legacy Monolithic System
```bash
cd /workshop/hackathon
python3 agents/drc_agent.py
```

## Key Differences

### 1. Agent Specialization

**OLD:**
- Single agent does everything
- No domain expertise separation

**NEW:**
- **GDS Parser Agent**: Expert in file formats and validation
- **DRC Checker Agent**: Expert in design rules and violations
- **Report Generator Agent**: Expert in technical documentation
- **Orchestrator Agent**: Expert in workflow coordination

### 2. LLM Integration

**OLD:**
- No LLM reasoning
- Hardcoded logic only

**NEW:**
- Each agent uses Amazon Bedrock Nova Pro
- Natural language understanding
- Adaptive reasoning for edge cases
- Can explain decisions

### 3. Tool Pattern

**OLD:**
```python
class DRCAgent:
    def process_gds(self, gds_path: str):
        # Direct function calls
        reader = GDSReader(gds_path)
        engine = DRCEngine(reader, self.rules_path)
        violations = engine.run_checks()
```

**NEW:**
```python
@tool
def run_drc_checks(gds_path: str, rules_path: str) -> dict:
    """Run DRC checks on a GDS file."""
    reader = GDSReader(gds_path)
    engine = DRCEngine(reader, rules_path)
    violations = engine.run_checks()
    return {'success': True, 'violations': violations}
```

### 4. Agent Communication

**OLD:**
- Direct function calls
- No coordination layer

**NEW:**
- Agents communicate through orchestrator
- Natural language coordination
- Can handle complex workflows

## Technology Stack

### Core Framework
- **Strands SDK**: Multi-agent orchestration
- **Amazon Bedrock**: LLM inference (Nova Pro)
- **AWS**: Cloud infrastructure

### Domain Tools (Unchanged)
- **KLayout**: GDS file parsing
- **PyYAML**: Rules configuration
- **Python 3.12+**: Runtime

## Future Enhancements

With the multi-agent architecture, you can easily add:

1. **Violation Analyzer Agent**: Deep-dive into specific violations
2. **Fix Suggestion Agent**: Recommend layout corrections
3. **Historical Analysis Agent**: Compare with past designs
4. **MCP Server**: Expose design rules as Model Context Protocol

## Migration Path

1. ✅ Keep legacy `drc_agent.py` for backward compatibility
2. ✅ New code uses `strands_orchestrator.py`
3. ✅ Both systems share core tools (GDSReader, DRCEngine, ReportFormatter)
4. 🔄 Gradually migrate file monitor to use Strands orchestrator
5. 🔄 Add MCP server for design rules
6. 🔄 Deploy to AWS using AgentCore

## Performance Considerations

### Latency
- **OLD**: ~1-2 seconds (pure Python)
- **NEW**: ~3-5 seconds (includes LLM calls)

### Scalability
- **OLD**: Single-threaded, sequential
- **NEW**: Can parallelize agent calls, cloud-native

### Cost
- **OLD**: Free (local compute only)
- **NEW**: ~$0.01-0.05 per DRC run (Bedrock API calls)

## Conclusion

The multi-agent Strands SDK approach provides:
- ✅ Better separation of concerns
- ✅ LLM-powered reasoning
- ✅ Extensible architecture
- ✅ Cloud-native deployment ready
- ✅ Agent coordination patterns

Trade-offs:
- ⚠️ Slightly higher latency
- ⚠️ AWS Bedrock API costs
- ⚠️ More complex debugging
