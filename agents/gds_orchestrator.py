"""Orchestrator: GDS Photonics Mask Validation System

Processes all GDS files in the gds-files/ directory:
  1. Parses each .gds file to structured JSON (full mode — with polygon vertices)
  2. Runs DRC validation rules (R1, R3, R4, R5, R6, R12, R14) against the parsed data
  3. Reports validation results per file and a final summary
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import gds_parser and drc_checker
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

    # ----- single file -----

    def parse_gds_file(self, gds_path: Path) -> dict:
        """Parse a single GDS file in full mode (with polygon vertices)."""
        lib = load_gds(str(gds_path))
        hierarchy = extract_cell_hierarchy(lib)
        layers = extract_layers(lib)
        pins_data = extract_pins(lib)
        connectivity = extract_connectivity(lib, pins_data)
        # Always use full mode (summary_only=False) so DRC can inspect polygons
        return assemble_output(
            str(gds_path), lib, hierarchy, layers, pins_data, connectivity,
            summary_only=False,
        )

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

        # Step 1 – Parse (full mode)
        print("  [1/3] Parsing GDS to JSON (full mode) ...")
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

        # Step 2 – Save JSON
        json_path = self.output_dir / (gds_path.stem + "_parsed.json")
        print(f"  [2/3] Saving JSON -> {json_path.name}")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, default=_json_fallback)

        # Step 3 – DRC validation
        print("  [3/3] Running DRC validation rules ...")
        drc_result = run_drc(parsed)
        print_report(drc_result)

        total_violations = drc_result["total_violations"]
        status = "valid" if total_violations == 0 else "invalid"

        return {
            "file": filename,
            "json_output": str(json_path),
            "status": status,
            "total_violations": total_violations,
            "by_rule": drc_result["by_rule"],
            "violations": drc_result["violations"],
            "metadata": meta,
        }

    # ----- summary -----

    @staticmethod
    def print_summary(results: list[dict]):
        """Print a final summary table."""
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
        print(f"{'='*60}\n")


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
