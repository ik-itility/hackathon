#!/usr/bin/env python3
"""Simple test script for Multi-Agent DRC System"""

import sys
import os

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from strands_orchestrator import process_gds_file

def main():
    print("\n" + "="*70)
    print("MULTI-AGENT DRC SYSTEM - TEST SCRIPT")
    print("="*70)
    
    # Test files
    test_files = [
        {
            'name': 'Correct Circuit (No Violations)',
            'path': 'gds-files/correct_circuit.gds'
        },
        {
            'name': 'Laser with Violations',
            'path': 'gds-files/laser_last_route_overlap.gds'
        }
    ]
    
    print("\nAvailable test files:")
    for i, test in enumerate(test_files, 1):
        print(f"  {i}. {test['name']}")
    
    # Get user choice
    choice = input("\nSelect file to test (1-2, or press Enter for file 1): ").strip()
    
    if not choice:
        choice = "1"
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(test_files):
            print("Invalid choice. Using file 1.")
            idx = 0
    except ValueError:
        print("Invalid input. Using file 1.")
        idx = 0
    
    selected = test_files[idx]
    
    print(f"\n{'='*70}")
    print(f"Testing: {selected['name']}")
    print(f"{'='*70}\n")
    
    # Process the file
    result = process_gds_file(
        gds_path=selected['path'],
        rules_path='data/rules_config.yaml',
        output_dir='output'
    )
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    print(f"\nCheck the output/ directory for reports:")
    print(f"  - JSON report: output/*_drc_report.json")
    print(f"  - Text report: output/*_drc_report.txt")
    print()

if __name__ == '__main__':
    main()
