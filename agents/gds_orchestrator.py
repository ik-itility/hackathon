"""Orchestrator: GDS Photonics Mask Validation System

Processes all GDS files in the gds-files/ directory:
  1. Parses each .gds file to structured JSON (full mode — with polygon vertices)
  2. Runs DRC validation rules (R1, R3, R4, R5, R6, R12, R14) against the parsed data
  3. Reports validation results per file and a final summary
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gds_parser import (
    load_gds,
    extract_cell_hierarchy,
    extract_layers,
    extract_pins,
    extract_connectivity,
    assemble_output,
)
from drc_checker import run_drc, print_report


# ---------------------------------------------------------------------------
# Sub-Agent Wrappers
# ---------------------------------------------------------------------------

class GDSReaderAgent:
    """Agent 1: Reads and parses GDS files."""
    
    def parse_gds(self, gds_path: Path) -> dict:
        """Parse a single GDS file in full mode."""
        lib = load_gds(str(gds_path))
        hierarchy = extract_cell_hierarchy(lib)
        layers = extract_layers(lib)
        pins_data = extract_pins(lib)
        connectivity = extract_connectivity(lib, pins_data)
        return assemble_output(
            str(gds_path), lib, hierarchy, layers, pins_data, connectivity,
            summary_only=False,
        )


class GDSValidatorAgent:
    """Agent 2: Validates GDS against DRC rules."""
    
    def validate_gds(self, parsed_data: dict) -> dict:
        """Run DRC validation on parsed GDS data."""
        return run_drc(parsed_data)


class GDSFixerAgent:
    """Agent 3: Generates fix recommendations for violations."""
    
    def __init__(self):
        try:
            import boto3
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            self.available = True
        except Exception:
            self.available = False
    
    def generate_fixes(self, parsed_data: dict, violations: list, filename: str) -> dict:
        """Generate AI-powered fix recommendations."""
        if not self.available:
            return {
                'filename': filename,
                'fix_recommendations': 'Bedrock not available - manual fixes required',
                'requires_approval': True
            }
        
        prompt = f"""You are a photonics mask design expert. Fix the following GDSII design rule violations:

File: {filename}
Total Violations: {len(violations)}

Violations:
{chr(10).join(f"- [{v.get('rule', '?')}] {v.get('message', '')}" for v in violations[:10])}

Provide specific fixes for each violation including:
1. Which cell/polygon to modify
2. Recommended changes
3. Justification"""

        try:
            response = self.bedrock.invoke_model(
                modelId='us.anthropic.claude-sonnet-4-5-v2:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 3000,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            result = json.loads(response['body'].read())
            fix_recommendations = result['content'][0]['text']
        except Exception as e:
            fix_recommendations = f"Error generating fixes: {e}"
        
        return {
            'filename': filename,
            'fix_recommendations': fix_recommendations,
            'requires_approval': True
        }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class GDSOrchestrator:
    def __init__(
        self,
        gds_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ):
        base = Path(__file__).resolve().parent.parent
        self.gds_dir = Path(gds_dir) if gds_dir else base / "gds-files"
        self.output_dir = Path(output_dir) if output_dir else base / "gds-files" / "output"
        
        # Initialize sub-agents
        self.reader = GDSReaderAgent()
        self.validator = GDSValidatorAgent()
        self.fixer = GDSFixerAgent()

    # ----- single file -----

    def parse_gds_file(self, gds_path: Path) -> dict:
        """Parse a single GDS file using reader agent."""
        return self.reader.parse_gds(gds_path)

    # ----- batch -----

    def process_all(self) -> list[dict]:
        """Process every .gds file in gds_dir: parse → save JSON → DRC validate."""
        gds_files = sorted(self.gds_dir.glob("*.gds"))
        if not gds_files:
            print(f"No .gds files found in {self.gds_dir}")
            return []

        self.output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for gds_path in gds_files:
            result = self._process_single(gds_path)
            results.append(result)

        return results

    def _process_single(self, gds_path: Path) -> dict:
        """Parse, save JSON, run DRC, and print results for one file."""
        filename = gds_path.name
        print(f"\n{'='*60}")
        print(f"  Processing: {filename}")
        print(f"{'='*60}")

        # Step 1 – Parse using reader agent
        print("  [1/4] Reading GDS file ...")
        try:
            parsed = self.parse_gds_file(gds_path)
        except Exception as exc:
            msg = f"Failed to parse {filename}: {exc}"
            print(f"  ERROR: {msg}")
            return {"file": filename, "status": "error", "message": msg}

        meta = parsed["metadata"]
        print(f"        Cells: {meta['total_cells']}  |  "
              f"Layers: {meta['total_layers']}  |  "
              f"Pins: {meta['total_pins']}  |  "
              f"Connections: {meta['total_connections']}")

        # Step 2 – Validate using validator agent
        print("  [2/4] Validating design rules ...")
        drc_result = self.validator.validate_gds(parsed)
        print_report(drc_result)

        # Step 3 – Save JSON
        json_path = self.output_dir / (gds_path.stem + "_parsed.json")
        print(f"  [3/4] Saving JSON -> {json_path.name}")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, default=_json_fallback)

        # Step 4 – Generate fixes if needed
        fix_result = None
        total_violations = drc_result["total_violations"]
        if total_violations > 0:
            print("  [4/4] Generating fix recommendations ...")
            try:
                fix_result = self.fixer.generate_fixes(
                    parsed, drc_result['violations'], filename
                )
                print("        Fix recommendations generated (requires manual approval)")
            except Exception as exc:
                print(f"        WARNING: Could not generate fixes: {exc}")

        status = "valid" if total_violations == 0 else "invalid"
        return {
            "file": filename,
            "json_output": str(json_path),
            "status": status,
            "total_violations": total_violations,
            "by_rule": drc_result["by_rule"],
            "violations": drc_result["violations"],
            "metadata": meta,
            "fix_recommendations": fix_result['fix_recommendations'] if fix_result else None,
        }

    # ----- summary -----

    @staticmethod
    def print_summary(results: list[dict]):
        """Print a final summary table with detailed violation breakdown."""
        print(f"\n{'='*60}")
        print("  VALIDATION SUMMARY")
        print(f"{'='*60}")
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "valid")
        failed = sum(1 for r in results if r["status"] == "invalid")
        errored = sum(1 for r in results if r["status"] == "error")

        for r in results:
            icon = {"valid": "PASS", "invalid": "FAIL", "error": "ERR "}[r["status"]]
            n_violations = r.get("total_violations", 0)
            suffix = f"  ({n_violations} violation(s))" if n_violations else ""
            print(f"  [{icon}] {r['file']}{suffix}")

        print(f"\n  Total: {total}  |  Passed: {passed}  |  "
              f"Failed: {failed}  |  Errors: {errored}")
        print(f"{'='*60}")
        
        # Detailed violation breakdown
        if failed > 0:
            print(f"\n{'='*60}")
            print("  DETAILED VIOLATION BREAKDOWN")
            print(f"{'='*60}")
            for r in results:
                if r["status"] == "invalid":
                    by_rule = r.get("by_rule", {})
                    total_v = r.get("total_violations", 0)
                    print(f"\n  {r['file']}: {total_v} violations")
                    for rule, count in sorted(by_rule.items()):
                        print(f"    - {rule}: {count}")
            print(f"\n{'='*60}\n")
        else:
            print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_fallback(obj):
    """Fallback JSON serializer for numpy types."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="GDS Photonics Mask Validation Orchestrator")
    ap.add_argument(
        "--gds-dir",
        default=None,
        help="Directory containing .gds files (default: ../gds-files)",
    )
    ap.add_argument(
        "--output-dir",
        default=None,
        help="Directory for parsed JSON output (default: <gds-dir>/output)",
    )
    args = ap.parse_args()

    orchestrator = GDSOrchestrator(
        gds_dir=args.gds_dir,
        output_dir=args.output_dir,
    )
    results = orchestrator.process_all()
    orchestrator.print_summary(results)

    # Write combined results
    report_path = orchestrator.output_dir / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=_json_fallback)
    print(f"  Full report saved to: {report_path}")
