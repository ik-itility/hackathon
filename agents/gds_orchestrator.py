"""Orchestrator: GDS Photonics Mask Validation System

Processes all GDS files in the gds-files/ directory:
  1. Parses each .gds file to structured JSON using gds_parser
  2. Validates each parsed result against photonics design rules
  3. Reports validation results and optionally generates AI fix recommendations
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import gds_parser
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gds_parser import (
    load_gds,
    extract_cell_hierarchy,
    extract_layers,
    extract_pins,
    extract_connectivity,
    extract_geometry,
    assemble_output,
)

# ---------------------------------------------------------------------------
# Design-rule defaults (from data/rules.txt)
# ---------------------------------------------------------------------------
DEFAULT_RULES = {
    "min_spacing": 0.20,           # µm
    "min_feature_size": 0.10,      # µm
    "min_waveguide_width": 0.45,   # µm
    "max_waveguide_width": 2.0,    # µm
    "min_waveguide_spacing": 0.30, # µm
    "min_ring_radius": 5.0,        # µm
    "min_bend_radius": 10.0,       # µm
    "min_angle": 135.0,            # degrees
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_parsed_gds(parsed: dict, rules: dict | None = None) -> dict:
    """Validate parsed GDS JSON against photonics design rules.

    Works with the output structure produced by gds_parser.assemble_output().
    """
    rules = rules or DEFAULT_RULES
    errors: list[str] = []

    for cell_name, cell_data in parsed.get("cells", {}).items():
        geom = cell_data.get("geometry", {})

        # --- layer-level feature-size check ---
        for layer_key, stats in geom.get("layer_stats", {}).items():
            area = stats.get("total_area_um2", 0)
            if area > 0 and area < rules["min_feature_size"] ** 2:
                errors.append(
                    f"Cell '{cell_name}' layer {layer_key}: "
                    f"total area {area:.4f} µm² below min feature size"
                )

        # --- path / waveguide checks ---
        for path in geom.get("paths_summary", []):
            for width in path.get("widths", []):
                if width < rules["min_waveguide_width"]:
                    errors.append(
                        f"Cell '{cell_name}': waveguide width {width:.3f} µm "
                        f"< min {rules['min_waveguide_width']} µm"
                    )
                if width > rules["max_waveguide_width"]:
                    errors.append(
                        f"Cell '{cell_name}': waveguide width {width:.3f} µm "
                        f"> max {rules['max_waveguide_width']} µm"
                    )

    return {"valid": len(errors) == 0, "errors": errors}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class GDSOrchestrator:
    def __init__(
        self,
        gds_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        rules: dict | None = None,
    ):
        base = Path(__file__).resolve().parent.parent
        self.gds_dir = Path(gds_dir) if gds_dir else base / "gds-files"
        self.output_dir = Path(output_dir) if output_dir else base / "gds-files" / "output"
        self.rules = rules or DEFAULT_RULES

    # ----- single file -----

    def parse_gds_file(self, gds_path: Path, summary_only: bool = True) -> dict:
        """Parse a single GDS file and return structured JSON."""
        lib = load_gds(str(gds_path))
        hierarchy = extract_cell_hierarchy(lib)
        layers = extract_layers(lib)
        pins_data = extract_pins(lib)
        connectivity = extract_connectivity(lib, pins_data)
        return assemble_output(
            str(gds_path), lib, hierarchy, layers, pins_data, connectivity, summary_only
        )

    def validate_parsed(self, parsed: dict) -> dict:
        """Validate a parsed GDS JSON dict against design rules."""
        return validate_parsed_gds(parsed, self.rules)

    # ----- batch -----

    def process_all(self, summary_only: bool = True) -> list[dict]:
        """Process every .gds file in gds_dir: parse → save JSON → validate."""
        gds_files = sorted(self.gds_dir.glob("*.gds"))
        if not gds_files:
            print(f"No .gds files found in {self.gds_dir}")
            return []

        self.output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for gds_path in gds_files:
            result = self._process_single(gds_path, summary_only)
            results.append(result)

        return results

    def _process_single(self, gds_path: Path, summary_only: bool) -> dict:
        """Parse, save JSON, validate, and print results for one file."""
        filename = gds_path.name
        print(f"\n{'='*60}")
        print(f"  Processing: {filename}")
        print(f"{'='*60}")

        # Step 1 – Parse
        print("  [1/3] Parsing GDS to JSON ...")
        try:
            parsed = self.parse_gds_file(gds_path, summary_only)
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

        # Step 3 – Validate
        print("  [3/3] Running validation rules ...")
        validation = self.validate_parsed(parsed)

        if validation["valid"]:
            print("        PASSED - all design rules satisfied")
        else:
            print(f"        FAILED - {len(validation['errors'])} violation(s):")
            for err in validation["errors"]:
                print(f"          - {err}")

        return {
            "file": filename,
            "json_output": str(json_path),
            "status": "valid" if validation["valid"] else "invalid",
            "errors": validation["errors"],
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
            err_count = len(r.get("errors", []))
            suffix = f"  ({err_count} violation(s))" if err_count else ""
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
    ap.add_argument(
        "--full",
        action="store_true",
        help="Include full polygon vertices in JSON (default: summary only)",
    )
    args = ap.parse_args()

    orchestrator = GDSOrchestrator(
        gds_dir=args.gds_dir,
        output_dir=args.output_dir,
    )
    results = orchestrator.process_all(summary_only=not args.full)
    orchestrator.print_summary(results)

    # Write combined results
    report_path = orchestrator.output_dir / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=_json_fallback)
    print(f"  Full report saved to: {report_path}")
