# 30-Second Explanation: Multi-Agent DRC System

## What We Built

We transformed a **single monolithic DRC agent** into a **multi-agent AI system** using AWS Strands SDK and Amazon Bedrock.

## The Problem
Original system: One agent doing everything - parsing GDS files, checking design rules, and generating reports. No AI reasoning, just hardcoded logic.

## The Solution
**Four specialized AI agents** working together:

1. **Orchestrator Agent** - Coordinates the workflow
2. **GDS Parser Agent** - Reads and validates photonics layout files
3. **DRC Checker Agent** - Validates designs against manufacturing rules
4. **Report Generator Agent** - Creates detailed violation reports

## How It Works
Each agent has its own **Amazon Bedrock Nova Pro LLM** for intelligent reasoning. They communicate through natural language and use specialized tools to perform their tasks.

## Key Benefits
- ✅ **Specialized expertise** - Each agent masters one domain
- ✅ **AI-powered reasoning** - Adapts to edge cases intelligently
- ✅ **Extensible** - Easy to add new agents (fix suggestions, optimization)
- ✅ **Cloud-native** - Ready for AWS deployment

## Technology Stack
- **Strands SDK** - Multi-agent orchestration
- **Amazon Bedrock** - Nova Pro LLM for each agent
- **KLayout** - Photonics GDS file processing
- **AWS** - Cloud infrastructure

## Real-World Impact
Instead of rigid rule checking, the system can now **understand context**, **explain decisions**, and **adapt to complex scenarios** - just like having a team of specialized engineers reviewing your chip designs.

---

**Time to read**: ~30 seconds
**Architecture**: Multi-agent AI system
**Domain**: Photonics semiconductor design validation
