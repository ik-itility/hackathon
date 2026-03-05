#!/usr/bin/env python3
"""Generate mock GDS files for testing without nazca dependency"""

import klayout.db as db
import os

def create_correct_circuit():
    """Create a GDS file with no violations"""
    layout = db.Layout()
    layout.dbu = 0.001  # 1nm database unit
    
    top = layout.create_cell("correct_circuit")
    
    # Layer 1003/0 - waveguides with proper spacing (> 300nm)
    layer_wg = layout.layer(1003, 0)
    
    # Create two waveguides with 500nm spacing (no violation)
    wg1 = db.Box(0, 0, 10000, 500)  # 10um x 0.5um
    wg2 = db.Box(0, 800, 10000, 1300)  # 10um x 0.5um, 300nm gap
    
    top.shapes(layer_wg).insert(wg1)
    top.shapes(layer_wg).insert(wg2)
    
    # Save
    output_path = "/workshop/hackathon/gds-files/correct_circuit.gds"
    layout.write(output_path)
    print(f"Created: {output_path}")
    return output_path

def create_violation_circuit():
    """Create a GDS file with spacing violations"""
    layout = db.Layout()
    layout.dbu = 0.001  # 1nm database unit
    
    top = layout.create_cell("laser_with_violations")
    
    # Layer 1003/0 - waveguides with violations
    layer_wg = layout.layer(1003, 0)
    
    # Create waveguides with < 300nm spacing (violations)
    wg1 = db.Box(0, 0, 10000, 500)
    wg2 = db.Box(0, 700, 10000, 1200)  # Only 200nm gap - VIOLATION
    wg3 = db.Box(0, 1400, 10000, 1900)  # Only 200nm gap - VIOLATION
    
    top.shapes(layer_wg).insert(wg1)
    top.shapes(layer_wg).insert(wg2)
    top.shapes(layer_wg).insert(wg3)
    
    # Save
    output_path = "/workshop/hackathon/gds-files/laser_last_route_overlap.gds"
    layout.write(output_path)
    print(f"Created: {output_path}")
    return output_path

if __name__ == '__main__':
    os.makedirs("/workshop/hackathon/gds-files", exist_ok=True)
    
    print("Generating test GDS files...")
    create_correct_circuit()
    create_violation_circuit()
    print("\nDone! GDS files created in gds-files/")
