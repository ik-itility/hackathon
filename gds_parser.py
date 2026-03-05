"""GDS Parser CLI — Extracts structured data from GDSII files for agent consumption.

Usage:
    python gds_parser.py <input.gds> [-o output.json] [--summary-only]
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import gdstk
import numpy as np


# ---------------------------------------------------------------------------
# Core Parsing
# ---------------------------------------------------------------------------

def load_gds(filepath: str) -> gdstk.Library:
    """Load a GDSII file and return the gdstk Library."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"GDS file not found: {filepath}")
    if not path.suffix.lower() in (".gds", ".gdsii", ".gds2"):
        raise ValueError(f"Not a GDS file (unexpected extension): {filepath}")
    return gdstk.read_gds(str(path))


def extract_cell_hierarchy(lib: gdstk.Library) -> dict:
    """Extract the full cell hierarchy: top cells, per-cell references and children."""
    top_cells = [c.name for c in lib.top_level()]

    cells = {}
    for cell in lib.cells:
        refs = []
        children = set()
        for ref in cell.references:
            ref_cell_name = ref.cell.name if hasattr(ref.cell, "name") else str(ref.cell)
            children.add(ref_cell_name)

            ref_info = {
                "cell": ref_cell_name,
                "origin": _pt(ref.origin),
                "rotation": round(ref.rotation, 6) if ref.rotation else 0.0,
                "magnification": ref.magnification if ref.magnification else 1.0,
                "x_reflection": bool(ref.x_reflection),
            }

            if ref.repetition is not None:
                rep = ref.repetition
                ref_info["repetition"] = {
                    "columns": getattr(rep, "columns", None),
                    "rows": getattr(rep, "rows", None),
                }
            refs.append(ref_info)

        cells[cell.name] = {
            "references": refs,
            "children": sorted(children),
        }

    return {"top_cells": top_cells, "cells": cells}


def extract_layers(lib: gdstk.Library) -> list[dict]:
    """Collect all unique (layer, datatype) pairs with shape counts across the library."""
    layer_counts: dict[tuple[int, int], int] = {}

    for cell in lib.cells:
        for poly in cell.polygons:
            key = (poly.layer, poly.datatype)
            layer_counts[key] = layer_counts.get(key, 0) + 1
        for path in cell.paths:
            for layer_val, dtype_val in zip(path.layers, path.datatypes):
                key = (layer_val, dtype_val)
                layer_counts[key] = layer_counts.get(key, 0) + 1

    return sorted(
        [{"layer": k[0], "datatype": k[1], "shape_count": v} for k, v in layer_counts.items()],
        key=lambda x: (x["layer"], x["datatype"]),
    )


# ---------------------------------------------------------------------------
# Geometry & Labels
# ---------------------------------------------------------------------------

def extract_geometry(cell: gdstk.Cell, summary_only: bool = True) -> dict:
    """Extract geometry from a single cell.

    summary_only=True  -> per-layer stats (counts, areas, bounding box) -- compact.
    summary_only=False -> full polygon vertices included -- can be large.
    """
    bb = cell.bounding_box()
    result: dict = {
        "bounding_box": [_pt(bb[0]), _pt(bb[1])] if bb is not None else None,
    }

    if summary_only:
        layer_stats: dict[tuple[int, int], dict] = {}
        for poly in cell.polygons:
            key = (poly.layer, poly.datatype)
            stats = layer_stats.setdefault(key, {"polygon_count": 0, "total_area": 0.0})
            stats["polygon_count"] += 1
            stats["total_area"] += poly.area()

        for path in cell.paths:
            polys = path.to_polygons()
            for p in polys:
                key = (path.layers[0], path.datatypes[0])
                stats = layer_stats.setdefault(key, {"polygon_count": 0, "total_area": 0.0})
                stats["polygon_count"] += 1
                stats["total_area"] += p.area()

        result["layer_stats"] = {
            f"{k[0]}/{k[1]}": {
                "polygon_count": v["polygon_count"],
                "total_area_um2": round(v["total_area"], 4),
            }
            for k, v in sorted(layer_stats.items())
        }

        paths_summary = []
        for path in cell.paths:
            spine = path.spine()
            if len(spine) >= 2:
                paths_summary.append({
                    "layers": list(path.layers),
                    "widths": _width_list(path),
                    "start": _pt(spine[0]),
                    "end": _pt(spine[-1]),
                    "length_um": round(_path_length(spine), 4),
                })
        if paths_summary:
            result["paths_summary"] = paths_summary
    else:
        polygons = []
        for poly in cell.polygons:
            polygons.append({
                "layer": poly.layer,
                "datatype": poly.datatype,
                "points": poly.points.tolist(),
                "area_um2": round(poly.area(), 4),
            })
        result["polygons"] = polygons

        paths = []
        for path in cell.paths:
            spine = path.spine()
            paths.append({
                "layers": list(path.layers),
                "widths": _width_list(path),
                "spine": spine.tolist() if hasattr(spine, "tolist") else [_pt(p) for p in spine],
                "length_um": round(_path_length(spine), 4),
            })
        result["paths"] = paths

    return result


def extract_labels(cell: gdstk.Cell) -> list[dict]:
    """Extract text labels from a cell (direct children only)."""
    labels = []
    for lbl in cell.labels:
        labels.append({
            "text": lbl.text,
            "origin": _pt(lbl.origin),
            "layer": lbl.layer,
            "texttype": lbl.texttype,
            "rotation": round(lbl.rotation, 6) if lbl.rotation else 0.0,
        })
    return labels


# ---------------------------------------------------------------------------
# Pin/Port Extraction
# ---------------------------------------------------------------------------

_PIN_PATTERN = re.compile(r"^[a-z]{1,3}\d{1,2}$")


def _detect_pin_layers(lib: gdstk.Library) -> set[int]:
    """Auto-detect which layer(s) carry pin labels."""
    layer_pin_counts: dict[int, int] = {}
    layer_total_counts: dict[int, int] = {}

    for cell in lib.cells:
        for lbl in cell.labels:
            layer_total_counts[lbl.layer] = layer_total_counts.get(lbl.layer, 0) + 1
            if _PIN_PATTERN.match(lbl.text):
                layer_pin_counts[lbl.layer] = layer_pin_counts.get(lbl.layer, 0) + 1

    pin_layers = set()
    for layer, pin_count in layer_pin_counts.items():
        total = layer_total_counts.get(layer, 0)
        if total >= 2 and pin_count / total > 0.5:
            pin_layers.add(layer)

    return pin_layers


def extract_pins(lib: gdstk.Library) -> dict:
    """Extract pin/port locations from the library."""
    pin_layers = _detect_pin_layers(lib)
    all_pins: dict[str, list[dict]] = {}

    for cell in lib.cells:
        cell_pins = []
        for lbl in cell.labels:
            if lbl.layer in pin_layers and _PIN_PATTERN.match(lbl.text):
                cell_pins.append({
                    "name": lbl.text,
                    "position": _pt(lbl.origin),
                    "layer": lbl.layer,
                    "rotation": round(lbl.rotation, 6) if lbl.rotation else 0.0,
                })
        if cell_pins:
            all_pins[cell.name] = cell_pins

    return {"pin_layers": sorted(pin_layers), "pins_by_cell": all_pins}


# ---------------------------------------------------------------------------
# Pin-Level Connectivity
# ---------------------------------------------------------------------------

def extract_connectivity(
    lib: gdstk.Library,
    pins_data: dict,
    tolerance_um: float = 3.0,
    waveguide_layers: set[tuple[int, int]] | None = None,
) -> list[dict]:
    """Determine pin-level connectivity by matching waveguide polygon endpoints to pins.

    Analyzes each *interconnection cell* (cells with both direct waveguide polygons
    AND child cell references) separately, so component-internal polygons don't
    interfere with routing polygon analysis.
    """
    connections = []

    for cell in lib.cells:
        if not cell.references or not cell.polygons:
            continue

        # Collect pin positions from child instances, transformed to this cell's coords
        child_pins = _collect_child_pins(cell, pins_data)
        if not child_pins:
            continue

        # Detect waveguide layers from this cell's direct polygons
        wg_layers = waveguide_layers or _detect_waveguide_layers(cell)
        if not wg_layers:
            continue

        # Compute endpoints of direct waveguide polygons
        poly_endpoints: list[tuple[tuple[float, float], tuple[float, float], int]] = []
        for idx, poly in enumerate(cell.polygons):
            if (poly.layer, poly.datatype) not in wg_layers:
                continue
            ends = _polygon_narrow_ends(poly)
            if ends is not None:
                poly_endpoints.append((ends[0], ends[1], idx))

        if not poly_endpoints:
            continue

        # Chain adjacent polygon segments
        chains = _build_polygon_chains(poly_endpoints, tolerance_um)

        # Match chain terminals to child pins
        for chain in chains:
            start_pt, end_pt = chain[0], chain[1]
            from_pin = _find_nearest_pin(start_pt, child_pins, tolerance_um)
            to_pin = _find_nearest_pin(end_pt, child_pins, tolerance_um)

            if from_pin and to_pin and from_pin != to_pin:
                connections.append({
                    "in_cell": cell.name,
                    "from": {"cell": from_pin[0], "pin": from_pin[1]},
                    "to": {"cell": to_pin[0], "pin": to_pin[1]},
                })

        # Also check GDSII paths (if any)
        for path in cell.paths:
            spine = path.spine()
            if len(spine) < 2:
                continue
            from_pin = _find_nearest_pin(spine[0], child_pins, tolerance_um)
            to_pin = _find_nearest_pin(spine[-1], child_pins, tolerance_um)
            if from_pin and to_pin and from_pin != to_pin:
                connections.append({
                    "in_cell": cell.name,
                    "from": {"cell": from_pin[0], "pin": from_pin[1]},
                    "to": {"cell": to_pin[0], "pin": to_pin[1]},
                })

    # Deduplicate
    seen = set()
    unique = []
    for c in connections:
        key = (c["in_cell"], c["from"]["cell"], c["from"]["pin"],
               c["to"]["cell"], c["to"]["pin"])
        rev_key = (c["in_cell"], c["to"]["cell"], c["to"]["pin"],
                   c["from"]["cell"], c["from"]["pin"])
        if key not in seen and rev_key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _collect_child_pins(
    cell: gdstk.Cell,
    pins_data: dict,
) -> list[tuple[float, float, str, str]]:
    """Collect pin positions from child cell instances, transformed to parent coords.

    Uses instance-qualified names (e.g., 'mmi2x2_dp#0') to distinguish
    multiple instances of the same cell.
    """
    result: list[tuple[float, float, str, str]] = []
    instance_count: dict[str, int] = {}

    for ref in cell.references:
        ref_cell = ref.cell
        ref_cell_name = ref_cell.name if hasattr(ref_cell, "name") else str(ref_cell)

        idx = instance_count.get(ref_cell_name, 0)
        instance_count[ref_cell_name] = idx + 1
        instance_id = f"{ref_cell_name}#{idx}"

        ox, oy = ref.origin if ref.origin is not None else (0.0, 0.0)
        rot = ref.rotation if ref.rotation else 0.0
        mag = ref.magnification if ref.magnification else 1.0
        xref = bool(ref.x_reflection)

        _add_pins_recursive(ref_cell, pins_data, ox, oy, rot, mag, xref, instance_id, result)

    return result


def _add_pins_recursive(
    cell, pins_data: dict,
    offset_x: float, offset_y: float,
    rotation: float, magnification: float, x_reflection: bool,
    instance_id: str, result: list,
):
    """Add pins from cell (and its children) with cumulative transformation."""
    cell_name = cell.name if hasattr(cell, "name") else str(cell)
    cell_pins = pins_data.get("pins_by_cell", {}).get(cell_name, [])

    for pin in cell_pins:
        px, py = pin["position"]
        ax, ay = _transform_point(px, py, offset_x, offset_y, rotation, magnification, x_reflection)
        result.append((ax, ay, instance_id, pin["name"]))

    for ref in cell.references:
        sub_cell = ref.cell
        sox, soy = ref.origin if ref.origin is not None else (0.0, 0.0)
        srot = ref.rotation if ref.rotation else 0.0
        smag = ref.magnification if ref.magnification else 1.0
        sxref = bool(ref.x_reflection)

        # Compose: sub-cell origin transformed into parent space
        tx, ty = _transform_point(sox, soy, offset_x, offset_y, rotation, magnification, x_reflection)
        combined_rot = rotation + (-srot if x_reflection else srot)
        combined_mag = magnification * smag
        combined_xref = x_reflection ^ sxref

        _add_pins_recursive(
            sub_cell, pins_data, tx, ty,
            combined_rot, combined_mag, combined_xref,
            instance_id, result,
        )


def _transform_point(
    px: float, py: float,
    offset_x: float, offset_y: float,
    rotation: float, magnification: float, x_reflection: bool,
) -> tuple[float, float]:
    """Apply GDS transformation: reflect -> rotate -> scale -> translate."""
    if x_reflection:
        py = -py
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    ax = magnification * (cos_r * px - sin_r * py) + offset_x
    ay = magnification * (sin_r * px + cos_r * py) + offset_y
    return ax, ay


def _detect_waveguide_layers(cell: gdstk.Cell) -> set[tuple[int, int]]:
    """Auto-detect waveguide layers from a cell's direct polygons."""
    wg_candidates: dict[tuple[int, int], int] = {}
    for poly in cell.polygons:
        bb = poly.bounding_box()
        if bb is None:
            continue
        w = bb[1][0] - bb[0][0]
        h = bb[1][1] - bb[0][1]
        if w == 0 or h == 0:
            continue
        aspect = max(w, h) / min(w, h)
        if aspect > 2.0:
            key = (poly.layer, poly.datatype)
            wg_candidates[key] = wg_candidates.get(key, 0) + 1

    candidates = {k for k, v in wg_candidates.items() if v >= 2 and k[1] == 0}
    if candidates:
        return candidates
    return {k for k, v in wg_candidates.items() if v >= 2}


def _polygon_narrow_ends(
    poly: gdstk.Polygon,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Compute the midpoints of the two 'narrow ends' of a waveguide polygon."""
    pts = poly.points
    if len(pts) < 4:
        return None

    bb = poly.bounding_box()
    if bb is None:
        return None
    w = bb[1][0] - bb[0][0]
    h = bb[1][1] - bb[0][1]
    if w == 0 and h == 0:
        return None

    if w >= h:
        x_min, x_max = bb[0][0], bb[1][0]
        margin = max(0.5, w * 0.05)
        left_pts = pts[pts[:, 0] < x_min + margin]
        right_pts = pts[pts[:, 0] > x_max - margin]
    else:
        y_min, y_max = bb[0][1], bb[1][1]
        margin = max(0.5, h * 0.05)
        left_pts = pts[pts[:, 1] < y_min + margin]
        right_pts = pts[pts[:, 1] > y_max - margin]

    if len(left_pts) == 0 or len(right_pts) == 0:
        return None

    end_a = (float(left_pts[:, 0].mean()), float(left_pts[:, 1].mean()))
    end_b = (float(right_pts[:, 0].mean()), float(right_pts[:, 1].mean()))
    return end_a, end_b


def _build_polygon_chains(
    poly_endpoints: list[tuple[tuple[float, float], tuple[float, float], int]],
    tolerance: float,
) -> list[tuple[tuple[float, float], tuple[float, float], float]]:
    """Chain polygon segments by matching shared endpoints.

    Returns list of (start_point, end_point, 0.0) for each chain.
    """
    if not poly_endpoints:
        return []

    n = len(poly_endpoints)
    adj: dict[tuple[int, int], list[tuple[int, int]]] = {
        (i, e): [] for i in range(n) for e in range(2)
    }

    for i in range(n):
        for j in range(i + 1, n):
            for ei in range(2):
                for ej in range(2):
                    pt_i = poly_endpoints[i][ei]
                    pt_j = poly_endpoints[j][ej]
                    if math.hypot(pt_i[0] - pt_j[0], pt_i[1] - pt_j[1]) < tolerance:
                        adj[(i, ei)].append((j, ej))
                        adj[(j, ej)].append((i, ei))

    visited_polys: set[int] = set()
    chains = []

    for i in range(n):
        if i in visited_polys:
            continue

        component: list[int] = []
        stack = [i]
        while stack:
            p = stack.pop()
            if p in visited_polys:
                continue
            visited_polys.add(p)
            component.append(p)
            for e in range(2):
                for neighbor_p, _ in adj[(p, e)]:
                    if neighbor_p not in visited_polys:
                        stack.append(neighbor_p)

        terminals: list[tuple[float, float]] = []
        for p in component:
            for e in range(2):
                if not adj[(p, e)]:
                    terminals.append(poly_endpoints[p][e])

        if len(terminals) >= 2:
            chains.append((terminals[0], terminals[1], 0.0))
        elif len(terminals) == 1:
            chains.append((terminals[0], terminals[0], 0.0))

    return chains


def _find_nearest_pin(
    point, pins: list[tuple[float, float, str, str]], tolerance: float,
) -> tuple[str, str] | None:
    """Find the nearest pin within tolerance. Returns (instance_id, pin_name) or None."""
    best_dist = tolerance
    best = None
    px, py = float(point[0]), float(point[1])
    for x, y, cell_name, pin_name in pins:
        dist = math.hypot(px - x, py - y)
        if dist < best_dist:
            best_dist = dist
            best = (cell_name, pin_name)
    return best


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pt(point) -> list[float]:
    """Convert a point (tuple/array) to a JSON-friendly [x, y] list."""
    if point is None:
        return [0.0, 0.0]
    if hasattr(point, "tolist"):
        return [round(v, 6) for v in point.tolist()]
    return [round(float(point[0]), 6), round(float(point[1]), 6)]


def _path_length(spine) -> float:
    """Compute the total length along a path spine."""
    total = 0.0
    pts = spine if isinstance(spine, list) else spine.tolist() if hasattr(spine, "tolist") else list(spine)
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dy = pts[i][1] - pts[i - 1][1]
        total += math.hypot(dx, dy)
    return total


def _width_list(path) -> list[float]:
    """Extract widths from a path, handling scalar or array forms."""
    try:
        widths = path.widths
        if hasattr(widths, "tolist"):
            return widths.tolist()
        if isinstance(widths, (list, tuple)):
            return list(widths)
        return [float(widths)]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Assembly & CLI
# ---------------------------------------------------------------------------

def assemble_output(
    filepath: str,
    lib: gdstk.Library,
    hierarchy: dict,
    layers: list[dict],
    pins_data: dict,
    connectivity: list[dict],
    summary_only: bool,
) -> dict:
    """Combine all parsed data into the final JSON structure."""
    cells_data = {}
    for cell in lib.cells:
        cells_data[cell.name] = {
            "geometry": extract_geometry(cell, summary_only=summary_only),
            "labels": extract_labels(cell),
            "pins": pins_data.get("pins_by_cell", {}).get(cell.name, []),
        }

    return {
        "metadata": {
            "source_file": Path(filepath).name,
            "unit_um": lib.unit * 1e6 if lib.unit < 1e-3 else lib.unit,
            "precision": lib.precision,
            "total_cells": len(lib.cells),
            "total_layers": len(layers),
            "total_pins": sum(len(v) for v in pins_data.get("pins_by_cell", {}).values()),
            "total_connections": len(connectivity),
            "summary_only": summary_only,
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        },
        "hierarchy": hierarchy,
        "layers": layers,
        "cells": cells_data,
        "connectivity": connectivity,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse a GDSII file and output structured JSON for agent consumption.",
    )
    parser.add_argument("input", help="Path to the input .gds file")
    parser.add_argument("-o", "--output", help="Output JSON path (default: <input>_parsed.json)")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        default=True,
        help="Output compact summary without raw polygon vertices (default: True)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include full polygon vertices in output (overrides --summary-only)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=3.0,
        help="Pin-to-path matching tolerance in microns (default: 3.0)",
    )
    args = parser.parse_args()

    summary_only = not args.full

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(input_path.stem + "_parsed.json")

    try:
        lib = load_gds(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading GDS file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded: {input_path.name}  ({len(lib.cells)} cells)")

    hierarchy = extract_cell_hierarchy(lib)
    layers = extract_layers(lib)
    pins_data = extract_pins(lib)
    connectivity = extract_connectivity(lib, pins_data, tolerance_um=args.tolerance)

    output = assemble_output(
        args.input, lib, hierarchy, layers, pins_data, connectivity, summary_only
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=_json_fallback)

    meta = output["metadata"]
    print(f"Output: {output_path}")
    print(f"  Cells:       {meta['total_cells']}")
    print(f"  Layers:      {meta['total_layers']}")
    print(f"  Pins:        {meta['total_pins']}")
    print(f"  Connections: {meta['total_connections']}")
    print(f"  Mode:        {'summary' if summary_only else 'full'}")


def _json_fallback(obj):
    """Fallback serializer for numpy types."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


if __name__ == "__main__":
    main()
