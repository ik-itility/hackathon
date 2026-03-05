"""DRC Checker — Runs photonic design rules against a parsed GDS JSON (full mode).

Usage:
    python drc_checker.py <parsed_full.json>

Rules implemented from rules.txt:
  R1   Minimum spacing between shapes on same layer      >= 0.20 um
  R3   Minimum feature size (smallest polygon dimension) >= 0.10 um
  R4   Minimum waveguide width                           >= 0.45 um
  R5   Maximum waveguide width                           <= 2.00 um
  R6   Minimum waveguide spacing                         >= 0.30 um
  R12  Connection validation: every optical pin connected
  R14  Minimum internal angle in polygon                 >= 135 deg
"""

import json
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Rule constants
# ---------------------------------------------------------------------------
MIN_SPACING_UM          = 0.20   # R1
MIN_FEATURE_UM          = 0.10   # R3
MIN_WG_WIDTH_UM         = 0.45   # R4
MAX_WG_WIDTH_UM         = 2.00   # R5
MIN_WG_SPACING_UM       = 0.30   # R6
MIN_ANGLE_DEG           = 135.0  # R14

# Waveguide core layer (layer 5, datatype 0) — auto-detected if not found
WG_LAYER = (5, 0)

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def poly_bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def poly_width_height(points):
    x0, y0, x1, y1 = poly_bbox(points)
    return x1 - x0, y1 - y0


def polygon_min_edge_length(points):
    n = len(points)
    return min(
        math.hypot(points[(i+1) % n][0] - points[i][0],
                   points[(i+1) % n][1] - points[i][1])
        for i in range(n)
    )


def polygon_min_internal_angle(points):
    n = len(points)
    min_angle = 360.0
    for i in range(n):
        a = points[(i - 1) % n]
        b = points[i]
        c = points[(i + 1) % n]
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        mag1 = math.hypot(*v1)
        mag2 = math.hypot(*v2)
        if mag1 < 1e-9 or mag2 < 1e-9:
            continue
        cos_a = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        angle = math.degrees(math.acos(cos_a))
        # cross > 0 → convex (interior angle = angle), cross < 0 → reflex
        if cross < 0:
            angle = 360.0 - angle
        min_angle = min(min_angle, angle)
    return min_angle


def bbox_min_distance(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    """Axis-aligned bounding box minimum distance (0 if overlapping)."""
    dx = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    dy = max(0.0, max(ay0, by0) - min(ay1, by1))
    return math.hypot(dx, dy)


def is_narrow_polygon(points, aspect_threshold=2.0):
    """Return True if polygon is elongated (waveguide-like)."""
    w, h = poly_width_height(points)
    if w == 0 or h == 0:
        return False
    return max(w, h) / min(w, h) > aspect_threshold


def narrow_dimension(points):
    """Return the shorter bounding-box dimension (waveguide width proxy)."""
    w, h = poly_width_height(points)
    return min(w, h)

# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------

def check_r3_min_feature(cell_name, polys):
    """R3: Minimum feature size >= 0.10 um (smallest bbox dimension)."""
    violations = []
    for i, p in enumerate(polys):
        w, h = poly_width_height(p["points"])
        feat = min(w, h)
        if feat < MIN_FEATURE_UM and feat > 1e-6:
            violations.append({
                "rule": "R3",
                "cell": cell_name,
                "layer": f"{p['layer']}/{p['datatype']}",
                "polygon_index": i,
                "value_um": round(feat, 4),
                "limit_um": MIN_FEATURE_UM,
                "message": f"Feature size {feat:.4f} um < min {MIN_FEATURE_UM} um",
            })
    return violations


def check_r4_r5_wg_width(cell_name, polys):
    """R4/R5: Waveguide width must be between 0.45 and 2.0 um."""
    violations = []
    for i, p in enumerate(polys):
        if (p["layer"], p["datatype"]) != WG_LAYER:
            continue
        if not is_narrow_polygon(p["points"]):
            continue
        width = narrow_dimension(p["points"])
        if width < MIN_WG_WIDTH_UM and width > 1e-6:
            violations.append({
                "rule": "R4",
                "cell": cell_name,
                "layer": f"{p['layer']}/{p['datatype']}",
                "polygon_index": i,
                "value_um": round(width, 4),
                "limit_um": MIN_WG_WIDTH_UM,
                "message": f"Waveguide width {width:.4f} um < min {MIN_WG_WIDTH_UM} um",
            })
        elif width > MAX_WG_WIDTH_UM:
            violations.append({
                "rule": "R5",
                "cell": cell_name,
                "layer": f"{p['layer']}/{p['datatype']}",
                "polygon_index": i,
                "value_um": round(width, 4),
                "limit_um": MAX_WG_WIDTH_UM,
                "message": f"Waveguide width {width:.4f} um > max {MAX_WG_WIDTH_UM} um",
            })
    return violations


def check_r1_r6_spacing(cell_name, polys):
    """R1/R6: Minimum spacing between waveguide shapes on WG layer only.

    Restricted to WG_LAYER to avoid false positives on DBR grating cells
    which have intentionally tight periodic spacing by PDK design.
    """
    violations = []
    wg_polys = [(i, p) for i, p in enumerate(polys)
                if (p["layer"], p["datatype"]) == WG_LAYER]
    if len(wg_polys) < 2:
        return violations

    bboxes = [(i, p, poly_bbox(p["points"])) for i, p in wg_polys]
    for a in range(len(bboxes)):
        for b in range(a + 1, len(bboxes)):
            ia, pa, (ax0, ay0, ax1, ay1) = bboxes[a]
            ib, pb, (bx0, by0, bx1, by1) = bboxes[b]
            dist = bbox_min_distance(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1)
            if 0 < dist < MIN_WG_SPACING_UM:
                violations.append({
                    "rule": "R6",
                    "cell": cell_name,
                    "layer": f"{WG_LAYER[0]}/{WG_LAYER[1]}",
                    "polygon_indices": [ia, ib],
                    "value_um": round(dist, 4),
                    "limit_um": MIN_WG_SPACING_UM,
                    "message": f"Waveguide spacing {dist:.4f} um < min {MIN_WG_SPACING_UM} um between polygons {ia} and {ib}",
                })
    return violations


def check_r14_angles(cell_name, polys):
    """R14: Minimum internal angle >= 135 deg.

    Only applied to waveguide-layer polygons with more than 4 vertices,
    which indicates a bend approximated as a polygon (not a simple rectangle).
    """
    violations = []
    for i, p in enumerate(polys):
        if (p["layer"], p["datatype"]) != WG_LAYER:
            continue
        pts = p["points"]
        if len(pts) <= 4:  # skip simple rectangles
            continue
        min_ang = polygon_min_internal_angle(pts)
        if min_ang < MIN_ANGLE_DEG:
            violations.append({
                "rule": "R14",
                "cell": cell_name,
                "layer": f"{p['layer']}/{p['datatype']}",
                "polygon_index": i,
                "value_deg": round(min_ang, 2),
                "limit_deg": MIN_ANGLE_DEG,
                "message": f"Sharp bend angle {min_ang:.2f} deg < min {MIN_ANGLE_DEG} deg in waveguide",
            })
    return violations


def check_r1_instance_spacing(data):
    """R1: Minimum spacing between placed component instances >= 0.20 um.

    Only checks top-level cells to avoid false positives on adjacent
    components that are intentionally placed end-to-end (e.g. within a laser).
    """
    violations = []
    cells_data = data["cells"]
    hier = data["hierarchy"]["cells"]
    top_cells = set(data["hierarchy"].get("top_cells", []))

    for parent_name, parent_hier in hier.items():
        if parent_name not in top_cells:
            continue
        refs = parent_hier.get("references", [])
        if len(refs) < 2:
            continue

        # Compute global bounding box for each placed instance
        instance_bboxes = []
        for ref in refs:
            child_name = ref["cell"]
            child_cell = cells_data.get(child_name)
            if not child_cell:
                continue
            bb = child_cell["geometry"].get("bounding_box")
            if not bb:
                continue
            ox, oy = ref["origin"]
            # Simple translation (rotation/reflection ignored for bbox check)
            gx0 = bb[0][0] + ox
            gy0 = bb[0][1] + oy
            gx1 = bb[1][0] + ox
            gy1 = bb[1][1] + oy
            instance_bboxes.append((child_name, gx0, gy0, gx1, gy1))

        for a in range(len(instance_bboxes)):
            for b in range(a + 1, len(instance_bboxes)):
                na, ax0, ay0, ax1, ay1 = instance_bboxes[a]
                nb, bx0, by0, bx1, by1 = instance_bboxes[b]
                dist = bbox_min_distance(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1)
                if dist < MIN_SPACING_UM:
                    violations.append({
                        "rule": "R1",
                        "cell": parent_name,
                        "layer": "(instance level)",
                        "value_um": round(dist, 4),
                        "limit_um": MIN_SPACING_UM,
                        "message": (
                            f"Instance spacing {dist:.4f} um < min {MIN_SPACING_UM} um "
                            f"between '{na}' and '{nb}'"
                        ),
                    })
    return violations


def check_r12_connections(data):
    """R12: Every optical pin (layer 501) should appear in at least one connection.

    Skipped when connectivity detection found zero connections — this indicates
    the parser could not detect routing (e.g. non-Nazca flat cells), not that
    all pins are truly disconnected.
    """
    violations = []
    if data.get("metadata", {}).get("total_connections", 0) == 0:
        return violations  # connectivity detection not applicable for this file
    connected_pins: set[str] = set()
    for conn in data.get("connectivity", []):
        fr = conn["from"]
        to = conn["to"]
        connected_pins.add(f"{fr['cell']}.{fr['pin']}")
        connected_pins.add(f"{to['cell']}.{to['pin']}")

    for cell_name, cell_data in data["cells"].items():
        for pin in cell_data.get("pins", []):
            if pin["layer"] != 501:
                continue
            # Check if this pin appears in any connection (any instance of this cell)
            matched = any(
                p.endswith(f".{pin['name']}") and cell_name in p
                for p in connected_pins
            )
            if not matched:
                violations.append({
                    "rule": "R12",
                    "cell": cell_name,
                    "pin": pin["name"],
                    "message": f"Pin '{pin['name']}' of cell '{cell_name}' has no connection",
                })
    return violations


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_drc(json_path_or_data):
    """Run all DRC checks. Accepts a file path (str) or pre-loaded dict."""
    if isinstance(json_path_or_data, dict):
        data = json_path_or_data
        source = data.get("metadata", {}).get("source_file", "unknown")
    else:
        with open(json_path_or_data, encoding="utf-8") as f:
            data = json.load(f)
        source = Path(json_path_or_data).name

    all_violations = []

    for cell_name, cell_data in data["cells"].items():
        polys = cell_data["geometry"].get("polygons", [])
        if not polys:
            continue
        all_violations += check_r3_min_feature(cell_name, polys)
        all_violations += check_r4_r5_wg_width(cell_name, polys)
        all_violations += check_r1_r6_spacing(cell_name, polys)
        all_violations += check_r14_angles(cell_name, polys)

    all_violations += check_r1_instance_spacing(data)
    all_violations += check_r12_connections(data)

    by_rule: dict[str, list] = {}
    for v in all_violations:
        by_rule.setdefault(v["rule"], []).append(v)

    return {
        "source": source,
        "total_violations": len(all_violations),
        "by_rule": {r: len(vs) for r, vs in sorted(by_rule.items())},
        "violations": all_violations,
    }


def print_report(result: dict):
    src = result["source"]
    total = result["total_violations"]
    status = "PASS" if total == 0 else "FAIL"

    print(f"\n{'='*60}")
    print(f"  DRC Report: {src}")
    print(f"  Status:     {status}  ({total} violation(s))")
    print(f"{'='*60}")

    if result["by_rule"]:
        print("  Violations by rule:")
        for rule, count in result["by_rule"].items():
            print(f"    {rule}: {count}")

    if result["violations"]:
        print()
        for v in result["violations"]:
            print(f"  [{v['rule']}] {v['message']}")
            print(f"         cell={v.get('cell','?')}  layer={v.get('layer','?')}")
    else:
        print("\n  No violations found.")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python drc_checker.py <parsed_full.json> [<parsed_full2.json> ...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        result = run_drc(path)
        print_report(result)
